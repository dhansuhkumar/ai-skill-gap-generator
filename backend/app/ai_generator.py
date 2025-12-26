# backend/app/ai_generator.py
import os
import json
import hashlib
import logging
import threading
from typing import List
from dotenv import load_dotenv

load_dotenv()

from backend.app.ai import router as ai_router

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

# Router handles provider clients and configuration (genai/openai)


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

    # Use centralized router to get AI response (single provider per request)
    with _LOCK:
        if not AI_AVAILABLE:
            return fallback_list

    prompt = (
        "Return EXACTLY 3 short project titles (strings) as a JSON array."
        " No markdown, no explanation. JSON ONLY."
        f" Target role: {role}. Current skills: {', '.join(skills) if skills else 'None'}."
    )
    try:
        raw = ai_router.get_ai_response(prompt)
        raw = _strip_markdown(raw)
        try:
            json_str = _extract_json_like(raw)
            arr = json.loads(json_str)
        except Exception:
            arr = []
        if isinstance(arr, list):
            titles = [str(x).strip() for x in arr if isinstance(x, str) and str(x).strip()][:3]
            if len(titles) == 3:
                return titles
        return fallback_list
    except Exception as e:
        logger.warning("generate_ai_project_ideas failed: %s", e)
        return fallback_list


def generate_learning_path_for_skill(skill: str):
    # Single-skill helper that uses the batched `get_learning_paths_for_skills`
    # to avoid calling Gemini per-skill. If AI is unavailable, return fallback.
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

    try:
        # Use centralized batched call for a single skill to respect single-entrypoint
        res = get_learning_paths_for_skills([skill])
        if isinstance(res, dict) and skill in res:
            return res.get(skill) or fallback
        return fallback
    except Exception:
        return fallback


def get_learning_paths_for_skills(skills: list):
    """
    Batch-generate learning paths for a list of skills using exactly one
    Gemini call. Returns a dict mapping skill -> {summary, steps}.
    """
    global AI_AVAILABLE, AI_CACHE, LAST_AI_SOURCE

    skills = [str(s).strip() for s in (skills or []) if s]
    if not skills:
        return {}

    cache_key = _cache_key("learning_paths", skills + ["v1"])  # simple cache key
    with _LOCK:
        if cache_key in AI_CACHE:
            LAST_AI_SOURCE = "cache"
            return AI_CACHE[cache_key]
        if not AI_AVAILABLE:
            LAST_AI_SOURCE = "fallback"
            raise RuntimeError("AI unavailable")

    # Build exact schema-aware prompt for batched learning paths
    skills_json = json.dumps(skills)
    prompt = (
        "Return ONLY a single JSON object mapping each skill (string) to a learning path object.\n"
        "If you cannot follow the exact schema, return {}.\n\n"
        "Schema:\n"
        "{\n"
        "  \"<skill>\": {\n"
        "      \"summary\": \"one-line summary\",\n"
        "      \"steps\": [\n"
        "         { \"day_from\": 1, \"day_to\": 3, \"title\": \"...\", \"tasks\": [\"...\"], \"project\": \"short\", \"resources\": [\"link1\"] },\n"
        "         ...\n"
        "      ]\n"
        "  },\n"
        "  ...\n"
        "}\n\n"
        f"Inputs:\n- Skills JSON array: {skills_json}\n\n"
        "Rules:\n"
        "1) Provide a learning path for each skill in the input list.\n"
        "2) Each learning path must include a short one-line 'summary' and an array 'steps'.\n"
        "3) Each step must be an object with keys: day_from (int), day_to (int), title (str), tasks (array of strings), project (short str), resources (array of strings).\n"
        "4) Keep steps concise; 3-6 steps per skill is fine.\n"
        "5) Output JSON only. No extra keys. If uncertain, return {}.\n"
    )

    try:
        raw = ai_router.get_ai_response(prompt)
        raw = _strip_markdown(raw)
        json_str = _extract_json_like(raw)
        parsed = json.loads(json_str)

        if not isinstance(parsed, dict):
            raise ValueError("learning paths response not an object")

        # Validate minimal structure
        out = {}
        for sk in skills:
            val = parsed.get(sk)
            if not isinstance(val, dict):
                continue
            summary = val.get("summary") or ""
            steps = val.get("steps") or []
            cleaned_steps = []
            if isinstance(steps, list):
                for st in steps:
                    if not isinstance(st, dict):
                        continue
                    day_from = int(st.get("day_from") or 0)
                    day_to = int(st.get("day_to") or day_from)
                    title = str(st.get("title") or "").strip()
                    tasks = [str(t).strip() for t in (st.get("tasks") or []) if str(t).strip()]
                    project = str(st.get("project") or "").strip()
                    resources = [str(r).strip() for r in (st.get("resources") or []) if str(r).strip()]
                    cleaned_steps.append({"day_from": day_from, "day_to": day_to, "title": title, "tasks": tasks, "project": project, "resources": resources})
            out[sk] = {"summary": str(summary).strip(), "steps": cleaned_steps}

        provider_used = ai_router.get_last_successful_provider() or "local"
        with _LOCK:
            AI_CACHE[cache_key] = out
            LAST_AI_SOURCE = provider_used
        return out

    except Exception as e:
        msg = str(e).lower()
        for token in ("429", "resourceexhausted", "defaultcredentialserror", "permission", "quota", "notfound"):
            if token in msg:
                with _LOCK:
                    AI_AVAILABLE = False
                logger.warning("Disabling AI_AVAILABLE due to error in learning paths: %s", e)
                break
        with _LOCK:
            LAST_AI_SOURCE = "fallback"
        logger.exception("get_learning_paths_for_skills failed")
        raise


def get_unified_analysis(user_skills, target_role, requested_provider: str = None):
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

    user_skills_list = json.dumps([str(s).strip() for s in (user_skills or [])])

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
    prompt = prompt.replace("<<TARGET_ROLE>>", str(target_role or "")).replace("<<USER_SKILLS_JSON>>", user_skills_list)

    # detect cache hit for the candidate provider before making call
    provider_candidate = ai_router.select_provider(requested_provider)
    cache_key = _cache_key(f"{target_role}|{provider_candidate}", user_skills)
    with _LOCK:
        if cache_key in AI_CACHE:
            LAST_AI_SOURCE = "cache"
            return AI_CACHE[cache_key]
        if not AI_AVAILABLE:
            LAST_AI_SOURCE = "fallback"
            raise RuntimeError("AI unavailable")

    try:
        raw = ai_router.get_ai_response(prompt, requested_provider)
        raw = _strip_markdown(raw)
        json_str = _extract_json_like(raw)
        parsed = json.loads(json_str)

        # Basic validation and normalization
        if not isinstance(parsed, dict):
            raise ValueError("AI output is not a JSON object")

        result = {
            "schema_version": parsed.get("schema_version"),
            "candidate_required_skills": [str(s).strip() for s in parsed.get("candidate_required_skills")][:20] if parsed.get("candidate_required_skills") else [],
            "candidate_missing_skills": [str(s).strip() for s in parsed.get("candidate_missing_skills")],
            "suggested_focus_skills": [str(s).strip() for s in parsed.get("suggested_focus_skills")][:5],
            "job_matches": parsed.get("job_matches") or [],
            "ai_projects_sample": parsed.get("ai_projects_sample") or [],
        }

        provider_used = ai_router.get_last_successful_provider() or provider_candidate or "local"
        cache_key_used = _cache_key(f"{target_role}|{provider_used}", user_skills)
        with _LOCK:
            AI_CACHE[cache_key_used] = result
            LAST_AI_SOURCE = provider_used
        # ensure router state updated (router sets last successful provider on success)
        return result

    except Exception as e:
        msg = str(e).lower()
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
