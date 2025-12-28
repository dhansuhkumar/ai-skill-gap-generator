# backend/app/ai_skill_analyzer.py

import os
import json
from dotenv import load_dotenv
from dotenv import load_dotenv

load_dotenv()

# This module no longer imports or configures Gemini directly; use
# `ai_generator.get_unified_analysis` for AI-driven analysis.

from . import ai_generator


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

    # This function no longer makes direct Gemini calls. Use the central
    # `ai_generator.get_unified_analysis(user_skills, target_role)` which runs a
    # single, controlled Gemini request and returns the required/missing skills.
    raise RuntimeError("Use ai_generator.get_unified_analysis(user_skills, target_role) instead of direct AI calls.")
