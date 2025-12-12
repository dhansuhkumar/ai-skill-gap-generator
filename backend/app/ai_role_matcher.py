# backend/app/ai_role_matcher.py

import os
import json
from dotenv import load_dotenv
try:
    import google.generativeai as genai
except Exception as _e:
    genai = None
    print("⚠️ google.generativeai import failed (AI role matcher disabled):", _e)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as _e:
        print("⚠️ genai.configure failed in ai_role_matcher:", _e)
else:
    print("⚠️ GEMINI_API_KEY not set or genai unavailable – AI role matcher will be disabled.")


def _norm_skill(name: str) -> str:
    """Normalize skill names for matching."""
    if not isinstance(name, str):
        return ""
    s = name.strip().lower()
    aliases = {
        "js": "javascript",
        "html5": "html",
        "css3": "css",
        "ts": "typescript",
        "py": "python",
    }
    if s in aliases:
        s = aliases[s]

    import re
    s = re.sub(r"[^a-z0-9#+]", "", s)
    return s


def _compute_match(user_skills, required_skills):
    """
    Compute match percentage and missing skills given:
      user_skills: list[str]
      required_skills: list[str]
    """
    user_norm = {_norm_skill(s) for s in (user_skills or []) if s}
    required_norm = [_norm_skill(s) for s in (required_skills or []) if s]

    total = len(required_norm)
    if total == 0:
        return 0, 0, 0, []

    known = sum(1 for x in required_norm if x in user_norm)
    percent = round((known / total) * 100)

    missing = [
        required_skills[i]
        for i, norm in enumerate(required_norm)
        if norm not in user_norm
    ]

    return int(percent), int(known), int(total), missing


def find_role_matches_ai(user_skills, selected_role, required_skills_for_selected=None, max_roles=5):
    """
    AI-based role matcher (NO skill_db.json).

    INPUT:
      user_skills: list[str]
      selected_role: str  -> role user chose in UI
      required_skills_for_selected: list[str] or None
         -> from your existing find_required_and_missing_ai (for better accuracy)

    PROCESS:
      1) Ask AI: "Given these skills and target role, suggest up to N realistic roles
         and list core skills required for each."
      2) Compute match % and missing skills for each role in code.
      3) Ensure the selected_role is present and prioritized.

    OUTPUT:
      List[dict] like:
      [
        {
          "role": "...",
          "match_percent": 72,
          "known_count": 5,
          "total_required": 7,
          "missing_skills_for_role": [...],
          "is_selected_role": True/False
        },
        ...
      ]
    """

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing; cannot use AI role matcher.")

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

    # Build prompt for roles + required skills
    prompt = f"""
You are a helpful career coach for tech roles.

User selected target role: "{selected_role}"
User current skills: {", ".join(user_skills) if user_skills else "None"}

Your job:

1. Suggest up to {max_roles} realistic job roles in software/tech that fit this user.
2. ALWAYS include the user-selected role, even if it is not the top match.
3. DO NOT make every role end with the word "Developer".
   - You can use varied titles like: "Web Developer", "Data Scientist",
     "Machine Learning Engineer", "DevOps Engineer", "QA Engineer",
     "Data Analyst", "Mobile App Engineer", etc.
   - At most TWO roles are allowed to end with "Developer".
4. For each role, list the core technical skills needed (5–12 skills).
5. Return JSON ONLY (no markdown, no explanation) in this exact format:

[
  {{
    "role": "Web Developer",
    "priority": "high" | "medium" | "low",
    "required_skills": ["HTML", "CSS", "JavaScript", "React", "Git"]
  }},
  {{
    "role": "Data Scientist",
    "priority": "medium",
    "required_skills": ["Python", "Pandas", "NumPy", "SQL", "Machine Learning"]
  }}
]

Rules:
- Role names must be short and standard, like:
  "Web Developer", "Frontend Engineer", "Backend Engineer",
  "Data Scientist", "Data Analyst", "DevOps Engineer",
  "Machine Learning Engineer", "QA Engineer", etc.
- Choose roles that are genuinely plausible given the user's skills.
- Only include technical skills in required_skills (no soft skills).
- JSON array only, nothing else.
"""


    response = model.generate_content(prompt)
    raw_text = getattr(response, "text", "").strip()
    print("🔍 Raw AI Role Matcher output:", raw_text)

    # Extract JSON array
    start = raw_text.find("[")
    end = raw_text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("AI role matcher did not return a JSON array.")

    roles_data = json.loads(raw_text[start:end + 1])
    if not isinstance(roles_data, list):
        raise ValueError("AI role matcher returned non-list JSON.")

    # Normalize AI roles into our structure
    matches = []
    seen_roles = set()

    # Helper: add one role entry
    def _add_role_entry(role_name, required_skills, is_selected=False):
        key = role_name.strip().lower()
        if key in seen_roles:
            return
        seen_roles.add(key)

        percent, known, total, missing = _compute_match(user_skills, required_skills)
        matches.append({
            "role": role_name,
            "match_percent": percent,
            "known_count": known,
            "total_required": total,
            "missing_skills_for_role": missing,
            "is_selected_role": bool(is_selected),
        })

    # 1) Add roles from AI response
    for item in roles_data:
        if not isinstance(item, dict):
            continue
        role_name = (item.get("role") or "").strip()
        required = item.get("required_skills") or []
        if not role_name or not isinstance(required, list) or not required:
            continue

        is_selected = selected_role and role_name.lower() == selected_role.strip().lower()
        _add_role_entry(role_name, required, is_selected=is_selected)

    # 2) Ensure the selected role is present (using required_skills_for_selected, if provided)
    if selected_role:
        sel_key = selected_role.strip().lower()
        if sel_key not in seen_roles and required_skills_for_selected:
            _add_role_entry(selected_role, required_skills_for_selected, is_selected=True)

    # 3) Sort by match_percent desc, with selected role on top if tie
    matches.sort(key=lambda x: (x["match_percent"], x["is_selected_role"]), reverse=True)

    # 4) Trim
    return matches[:max_roles]
