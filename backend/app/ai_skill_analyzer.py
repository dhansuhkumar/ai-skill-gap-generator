# backend/app/ai_skill_analyzer.py

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY is not set. AI skill analyzer will fall back to classic logic.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


def _normalize_skill_name(name: str) -> str:
    """
    Simple normalization so that 'js' and 'JavaScript', or 'html' and 'HTML'
    don't mismatch just because of case or punctuation.

    This is intentionally lightweight (no big static JSON).
    """
    if not isinstance(name, str):
        return ""
    s = name.strip().lower()

    # Tiny alias mapping (NOT a big hardcoded database, just obvious ones)
    aliases = {
        "js": "javascript",
        "html5": "html",
        "css3": "css",
        "ts": "typescript",
        "py": "python",
    }
    if s in aliases:
        s = aliases[s]

    # remove spaces and punctuation to make matching more forgiving
    import re
    s = re.sub(r"[^a-z0-9#+]", "", s)
    return s


def _compute_missing(user_skills, required_skills):
    """
    Deterministic difference:
    missing = required - user (after normalization).
    """
    user_norm = {_normalize_skill_name(s) for s in (user_skills or []) if s}
    missing = []
    for req in (required_skills or []):
        norm_req = _normalize_skill_name(req)
        if norm_req and norm_req not in user_norm:
            missing.append(req)
    # de-duplicate while keeping order
    seen = set()
    result = []
    for m in missing:
        key = _normalize_skill_name(m)
        if key not in seen and key:
            seen.add(key)
            result.append(m)
    return result


def find_required_and_missing_ai(user_skills, target_role):
    """
    🔹 AI-based required + missing skill analyzer.

    Input:
        user_skills : list[str]
        target_role : str

    Output (dict):
        {
          "required_skills": [...],  # AI-generated core skills for the role
          "missing_skills": [...]    # computed by comparing required vs user skills
        }

    If anything goes wrong, the caller should catch the exception
    and fall back to the classic find_missing_skills().
    """

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing; cannot use AI skill analyzer.")

    model_name = "gemini-2.5-flask"
    try:
        for m in genai.list_models():
            if 'generateContent' in getattr(m, "supported_generation_methods", []):
                name = getattr(m, "name", "")
                if "gemini-2.5-flash" in name:
                    model_name = name
                    break
                elif "gemini-2.0-flash" in name:
                    model_name = name
                elif "gemini-1.5-flash" in name and "2.5" not in model_name:
                    model_name = name
        print(f"🔍 Selected Model for Skill Analyzer: {model_name}")
    except Exception as e:
        print(f"⚠️ Error selecting model: {e}")
    model = genai.GenerativeModel(model_name)

    # Prompt: ask ONLY for required/core skills
    prompt = f"""
You are an expert technical recruiter.

User wants to become: "{target_role}"
User currently has skills: {", ".join(user_skills) if user_skills else "None"}

Step 1: Decide the essential technical skills required for this role in 2025.
Step 2: Return them as a JSON object with ONE key "required_skills".

Return JSON only, no explanation, no markdown.

Format:
{{
  "required_skills": ["skill1", "skill2", "skill3", ...]
}}

Rules:
- Use short, concrete skill names like "HTML", "CSS", "JavaScript", "React", "SQL", "Python", "Git".
- No soft skills.
- Maximum 15 skills.
"""

    response = model.generate_content(prompt)
    raw_text = getattr(response, "text", "").strip()
    print("🔍 Raw AI Required Skills output:", raw_text)

    # Extract JSON safely
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("AI output did not contain a JSON object.")

    json_str = raw_text[start:end + 1]
    data = json.loads(json_str)

    required_skills = data.get("required_skills", [])
    if not isinstance(required_skills, list) or len(required_skills) == 0:
        raise ValueError("AI did not return a valid required_skills list.")

    # Normalize required list (remove empties, duplicates)
    cleaned_required = []
    seen = set()
    for s in required_skills:
        if not isinstance(s, str):
            continue
        s_clean = s.strip()
        if not s_clean:
            continue
        key = _normalize_skill_name(s_clean)
        if key and key not in seen:
            seen.add(key)
            cleaned_required.append(s_clean)

    missing_skills = _compute_missing(user_skills, cleaned_required)

    return {
        "required_skills": cleaned_required,
        "missing_skills": missing_skills,
    }
