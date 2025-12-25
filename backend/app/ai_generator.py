# backend/app/ai_generator.py
import os
import json
import hashlib
import logging
import threading
from typing import List
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except Exception as _e:
    genai = None
    print("⚠️ google.generativeai import failed (AI generator disabled):", _e)

load_dotenv()

logger = logging.getLogger(__name__)
if not logger.handlers:
    # Basic logging configuration for module-level messages
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Circuit breaker flag and simple in-memory cache (thread-safe)
_LOCK = threading.Lock()
AI_AVAILABLE = True
AI_CACHE = {}
# Last source used for observability (set per call)
LAST_AI_SOURCE = None

# Track whether we've configured genai with API key
_GENAI_CONFIGURED = False


def _ensure_genai_configured():
    """Ensure genai is configured with GEMINI_API_KEY if available.

    This is safe to call multiple times.
    """
    global _GENAI_CONFIGURED
    if _GENAI_CONFIGURED:
        return
    if not genai:
        return
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        logger.info("GEMINI_API_KEY not set; AI disabled")
        return
    try:
        genai.configure(api_key=key, transport='rest')
        _GENAI_CONFIGURED = True
        logger.info("genai configured with GEMINI_API_KEY")
    except Exception as e:
        logger.warning("genai.configure failed: %s", e)


def _cache_key(role: str, skills: List[str]) -> str:
    key = (role or "") + "|" + ",".join(sorted([str(s).strip() for s in (skills or []) if s]))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _strip_markdown(text: str) -> str:
    if not isinstance(text, str):
        return text
    t = text.strip()
    # Remove triple-backtick fences if any
    if t.startswith("```") and t.endswith("```"):
        parts = t.split("\n")
        if parts and parts[0].startswith("```"):
            parts = parts[1:]
        if parts and parts[-1].strip().endswith("```"):
            parts = parts[:-1]
        t = "\n".join(parts).strip()
    # Remove surrounding single backticks
    t = t.strip('`')
    return t


def _extract_json_like(text: str):
    """Try to extract a JSON object or array substring from text.

    Returns the JSON string or raises ValueError.
    """
    if not isinstance(text, str):
        raise ValueError("No text to parse")
    s = text.strip()
    # find first { or [ and matching closing
    first_obj = min([idx for idx in [s.find('{'), s.find('[')] if idx != -1], default=-1)
    if first_obj == -1:
        raise ValueError("No JSON start found")
    # Choose whether object or array
    open_ch = s[first_obj]
    close_ch = '}' if open_ch == '{' else ']'
    depth = 0
    for i in range(first_obj, len(s)):
        if s[i] == open_ch:
            depth += 1
        elif s[i] == close_ch:
            depth -= 1
            if depth == 0:
                return s[first_obj:i+1]
    raise ValueError("No matching JSON end found")


def generate_ai_project_ideas(role, skills):
    """
    Deterministic-first project ideas generator. Tries AI once, falls back to fixed list.
    Returns list[str] of 3 project titles.
    """
    fallback_list = [
        "Build a Portfolio Website with Dark Mode",
        "Create a Task Tracker using LocalStorage",
        "Design a Weather Dashboard using Public APIs",
    ]

    with _LOCK:
        if not AI_AVAILABLE or not genai:
            return fallback_list

    _ensure_genai_configured()
    if not _GENAI_CONFIGURED:
        return fallback_list

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    try:
        model = genai.GenerativeModel(model_name)
        prompt = (
            "Return EXACTLY 3 short project titles (strings) as a JSON array."
            " No markdown, no explanation. JSON ONLY."
            f" Target role: {role}. Current skills: {', '.join(skills) if skills else 'None'}."
        )
        response = model.generate_content(prompt)
        raw = getattr(response, "text", "") or ""
        raw = _strip_markdown(raw)
        json_str = _extract_json_like(raw)
        arr = json.loads(json_str)
        if not isinstance(arr, list):
            raise ValueError("AI did not return a JSON array")
        titles = [str(x).strip() for x in arr if isinstance(x, str) and str(x).strip()][:3]
        if len(titles) == 3:
            return titles
        return fallback_list
    except Exception as e:
        logger.warning("generate_ai_project_ideas failed: %s", e)
        return fallback_list


def generate_learning_path_for_skill(skill: str):
    fallback = {
        "summary": f"Learn core concepts of {skill} and build a small project.",
        "steps": [
            f"Follow an introductory tutorial for {skill}",
            f"Build a tiny project using {skill}",
            "Refine by adding tests and reading official docs",
        ],
    }
    
    if not skill:
        return {"summary": "", "steps": []}

    with _LOCK:
        if not AI_AVAILABLE or not genai:
            return fallback

    _ensure_genai_configured()
    if not _GENAI_CONFIGURED:
        return fallback

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    try:
        model = genai.GenerativeModel(model_name)
        prompt = (
            f"Create a concise learning path for the skill: '{skill}'.\n"
            "Return a JSON object with:\n"
            "  \"summary\": \"Brief summary of the approach\",\n"
            "  \"steps\": [\"Step 1\", \"Step 2\", \"Step 3\"]\n"
            "Return JSON ONLY. No markdown."
        )
        response = model.generate_content(prompt)
        raw = getattr(response, "text", "").strip()
        # Extract JSON object
        json_str = _extract_json_like(raw)
        obj = json.loads(json_str)
        
        if not isinstance(obj, dict):
            raise ValueError("Learning-path JSON is not an object")

        summary = (obj.get("summary") or "").strip()
        steps = obj.get("steps") or []
        if not isinstance(steps, list):
            steps = []
        steps = [str(s).strip() for s in steps if str(s).strip()]

        return {
            "summary": summary,
            "steps": steps,
        }
    except Exception as e:
        logger.warning(f"Learning-path generation failed for '{skill}': {e}")
        return fallback


def get_unified_analysis(user_skills, target_role):
    """
    Single Gemini request returning a validated JSON object matching the task schema:
      - candidate_required_skills (max 20)
      - candidate_missing_skills
      - suggested_focus_skills (up to 5)
      - job_matches (3-5 entries with integer match_percent)
      - ai_projects_sample (exactly 3 objects with title and short)

    Uses `GEMINI_MODEL` env var (default `models/gemini-2.5-flash`).
    Caches results and respects the circuit breaker `AI_AVAILABLE`.
    Raises on validation or API errors to trigger fallback in caller.
    """
    global AI_AVAILABLE, AI_CACHE, LAST_AI_SOURCE

    user_skills = user_skills or []
    target_role = target_role or ""

    cache_key = _cache_key(target_role, user_skills)
    with _LOCK:
        if cache_key in AI_CACHE:
            LAST_AI_SOURCE = "cache"
            return AI_CACHE[cache_key]
        if not AI_AVAILABLE:
            LAST_AI_SOURCE = "fallback"
            raise RuntimeError("AI unavailable")

    # Ensure genai configured
    _ensure_genai_configured()
    if not _GENAI_CONFIGURED or not genai:
        with _LOCK:
            LAST_AI_SOURCE = "fallback"
        raise RuntimeError("AI unavailable or not configured")

    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

    user_skills_list = json.dumps([str(s).strip() for s in (user_skills or [])])
    # Exact prompt required by system/task — placeholders replaced with actual inputs
    prompt = """
You are an expert technical career coach and data engineer. Return ONLY a single valid JSON object (no markdown, no commentary) that exactly matches the schema described below. If you cannot strictly follow these constraints, return an empty JSON object {} and nothing else.

Schema:
{
  "schema_version": "v1",
  "candidate_required_skills": ["skill1", "skill2", ...],           // canonical names; max 20
  "candidate_missing_skills": ["skillA", "skillB", ...],           // subset of above
  "suggested_focus_skills": ["skillA", "skillC"],                  // up to 5 skills we suggest the user focus on first
  "job_matches": [
     { "role":"Role Name", "match_percent": 85 },
     ...
  ],                                                                // 3-5 entries
  "ai_projects_sample": [
     { "title":"Short title", "short":"1-line description" },
     ...
  ]                                                                  // exactly 3
}

Inputs:
- Target role: <<TARGET_ROLE>>
- User skills list: <<USER_SKILLS_JSON>>   (JSON array)

Rules:
1. Use canonical, consistent skill names (e.g., "JavaScript", "React", "Node.js", "Python", "PostgreSQL", "Docker", "AWS").
2. Decide up to 20 required skills for the role in 2025; include modern stack items and infra if relevant.
3. Compute missing_skills = required_skills minus user_skills (do exact match on canonical names).
4. Provide suggested_focus_skills: top 3-5 missing skills prioritized by impact (which skills will most improve match%).
5. Provide 3 brief project ideas (title + one-line short).
6. Provide 3-5 job_matches with integer match_percent computed assuming user has the provided user_skills.
7. All match_percent values must be integers 0-100.
8. Output JSON only. No extra keys. No commentary. If uncertain, return {}.

End of prompt.
"""
    # Substitute placeholders exactly as required
    prompt = prompt.replace("<<TARGET_ROLE>>", str(target_role or "")).replace("<<USER_SKILLS_JSON>>", user_skills_list)

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        raw = getattr(response, "text", "") or ""
        raw = _strip_markdown(raw)
        try:
            json_str = _extract_json_like(raw)
            parsed = json.loads(json_str)
        except Exception as pe:
            # parsing failure: do not trip circuit-breaker; propagate to caller
            logger.debug("JSON extraction failed: %s", pe)
            raise

        # Validate keys and types per exact schema required by the task
        required_keys = ["schema_version", "candidate_required_skills", "candidate_missing_skills", "suggested_focus_skills", "job_matches", "ai_projects_sample"]
        if not isinstance(parsed, dict):
            raise ValueError("AI output is not a JSON object")
        for k in required_keys:
            if k not in parsed:
                raise KeyError(f"Missing required key: {k}")

        if not isinstance(parsed.get("candidate_required_skills"), list):
            raise TypeError("candidate_required_skills must be a list")
        if not isinstance(parsed.get("candidate_missing_skills"), list):
            raise TypeError("candidate_missing_skills must be a list")
        if not isinstance(parsed.get("suggested_focus_skills"), list):
            raise TypeError("suggested_focus_skills must be a list")
        if not isinstance(parsed.get("job_matches"), list):
            raise TypeError("job_matches must be a list")
        if not isinstance(parsed.get("ai_projects_sample"), list):
            raise TypeError("ai_projects_sample must be a list")

        # Validate ai_projects_sample (exactly 3 objects with title and short)
        aps = parsed.get("ai_projects_sample")
        if len(aps) != 3:
            raise ValueError("ai_projects_sample must contain exactly 3 items")
        aps_clean = []
        for it in aps:
            if not isinstance(it, dict):
                raise TypeError("ai_projects_sample items must be objects")
            title = it.get("title")
            short = it.get("short")
            if not title or not short:
                raise ValueError("ai_projects_sample items must have title and short")
            aps_clean.append({"title": str(title).strip(), "short": str(short).strip()})

        # Validate job_matches
        jm_valid = []
        for jm in parsed.get("job_matches"):
            if not isinstance(jm, dict):
                continue
            role = jm.get("role")
            pct = jm.get("match_percent")
            if role is None or pct is None:
                continue
            try:
                pct = int(pct)
            except Exception:
                raise TypeError("job_matches.match_percent must be an integer")
            if pct < 0 or pct > 100:
                raise ValueError("job_matches.match_percent must be 0-100")
            jm_valid.append({"role": str(role), "match_percent": int(pct)})
        if not (3 <= len(jm_valid) <= 5):
            raise ValueError("job_matches must contain 3 to 5 valid entries")

        result = {
            "schema_version": parsed.get("schema_version"),
            "candidate_required_skills": [str(s).strip() for s in parsed.get("candidate_required_skills")][:20],
            "candidate_missing_skills": [str(s).strip() for s in parsed.get("candidate_missing_skills")],
            "suggested_focus_skills": [str(s).strip() for s in parsed.get("suggested_focus_skills")][:5],
            "job_matches": jm_valid,
            "ai_projects_sample": aps_clean,
        }

        with _LOCK:
            AI_CACHE[cache_key] = result
            LAST_AI_SOURCE = "gemini"
        return result

    except Exception as e:
        msg = str(e).lower()
        # Only trigger circuit-breaker for quota/auth/resource errors
        for token in ("429", "resourceexhausted", "defaultcredentialserror", "permission", "quota", "notfound"):
            if token in msg:
                with _LOCK:
                    AI_AVAILABLE = False
                logger.warning("Disabling AI_AVAILABLE due to error: %s", e)
                break
        with _LOCK:
            LAST_AI_SOURCE = "fallback"
        logger.exception("get_unified_analysis failed")
        raise
