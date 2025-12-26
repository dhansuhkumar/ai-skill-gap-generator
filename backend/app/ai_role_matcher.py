# backend/app/ai_role_matcher.py

import os
import json
from dotenv import load_dotenv

load_dotenv()
# This module no longer calls Gemini directly. Role matching is deterministic
# and lightweight; higher-quality role suggestions come from the unified AI
# response in `ai_generator.get_unified_analysis`.


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
    Deterministic role matcher that avoids calling Gemini.

    If `required_skills_for_selected` (from the unified AI analysis) is provided,
    compute a match percent for the selected role and return it as the primary
    result. Otherwise return an empty list — richer role suggestions should be
    taken from `ai_generator.get_unified_analysis`.
    """

    results = []
    if selected_role and required_skills_for_selected:
        percent, known, total, missing = _compute_match(user_skills, required_skills_for_selected)
        results.append({
            "role": selected_role,
            "match_percent": int(percent),
            "known_count": int(known),
            "total_required": int(total),
            "missing_skills_for_role": missing,
            "is_selected_role": True,
        })

    return results[:max_roles]
