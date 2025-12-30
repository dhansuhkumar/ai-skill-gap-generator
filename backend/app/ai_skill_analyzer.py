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


def find_required_and_missing_ai(user_skills, target_role, requested_provider=None):
    """
    🔹 AI-based required + missing skill analyzer.
    Uses central `ai_generator.get_unified_analysis` with support for fallbacks.
    """
    try:
        analysis = ai_generator.get_unified_analysis(user_skills, target_role, requested_provider=requested_provider)
        return {
            "required_skills": analysis.get("required_skills", []),
            "missing_skills": analysis.get("missing_skills", [])
        }
    except Exception as e:
        # Fallback will be handled by the caller (routes.py)
        raise e
