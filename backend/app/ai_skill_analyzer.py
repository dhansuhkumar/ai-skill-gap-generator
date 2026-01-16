# backend/app/ai_skill_analyzer.py
"""
AI Skill Analyzer - CSV-based skill analysis (AI code removed).
All functionality now uses CSV data only.
"""

import re


def _normalize_skill_name(name: str) -> str:
    """
    Simple normalization so that 'js' and 'JavaScript', or 'html' and 'HTML'
    don't mismatch just because of case or punctuation.
    """
    if not isinstance(name, str):
        return ""
    s = name.strip().lower()

    # Tiny alias mapping
    aliases = {
        "js": "javascript",
        "html5": "html",
        "css3": "css",
        "ts": "typescript",
        "py": "python",
    }
    if s in aliases:
        s = aliases[s]

    # remove spaces and punctuation
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


def find_required_and_missing(user_skills, target_role):
    """
    Required + missing skill analyzer using CSV data only.
    
    Uses CSV-based analysis (Kaggle data) for skill gap detection.
    No AI fallback - purely deterministic CSV matching.
    """
    from .ai_generator import get_unified_analysis
    
    # Use the unified analysis which includes CSV data + YouTube resources
    analysis = get_unified_analysis(user_skills, target_role)
    
    # Extract required and missing skills
    required_skills = analysis.get("required_skills", [])
    missing_skills = analysis.get("missing_skills", [])
    
    return {
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "matched_jobs": analysis.get("matched_jobs", []),
        "resources": analysis.get("resources", {}),
        "source": analysis.get("source", "csv")
    }


# Alias for backward compatibility
find_required_and_missing_ai = find_required_and_missing
