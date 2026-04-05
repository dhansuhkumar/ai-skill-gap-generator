# backend/app/skill_analyzer.py
"""
Optimized Skill Gap Analyzer using LLM (Groq/Gemini).

Primary: LLM-based extraction (fast, reliable)
Fallback: Predefined skills database
"""

import functools
import logging
from typing import List, Dict, Tuple

from .llm_skill_extractor import extract_skills_with_llm
from .web_skill_extractor import _get_role_fallback_skills
from .skill_cleaner import clean_and_deduplicate_skills

logger = logging.getLogger(__name__)

_SKILL_CACHE = {}


def get_top_skills_for_role(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Get top N most frequently required skills for a role.

    Priority:
    1. LLM extraction (Groq/Gemini) - 3-5 seconds
    2. Predefined fallback skills - instant

    Args:
        role: Target job role
        top_n: Number of top skills to return

    Returns:
        Tuple of (top_skills_list, sources_analyzed)
    """
    cache_key = f"{role.lower().strip()}:{top_n}"

    if cache_key in _SKILL_CACHE:
        logger.info(f"Using cached skills for role: {role}")
        cached = _SKILL_CACHE[cache_key]
        return (cached["skills"], cached["sources"])

    logger.info(f"🔍 Extracting skills for role: {role}")

    skills, source = extract_skills_with_llm(role, top_n)

    if skills:
        _SKILL_CACHE[cache_key] = {"skills": skills, "sources": 1, "source": source}
        logger.info(f"✅ Found {len(skills)} skills for {role} via {source}")
        return (skills, 1)

    logger.warning(f"LLM extraction failed, using predefined skills for {role}")
    fallback_skills = _get_role_fallback_skills(role)
    _SKILL_CACHE[cache_key] = {
        "skills": fallback_skills,
        "sources": 0,
        "source": "fallback",
    }
    return (fallback_skills, 0)


@functools.lru_cache(maxsize=100)
def get_top_skills_for_role_cached(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Cached version of get_top_skills_for_role.
    Returns tuple for hashability.
    """
    skills, sources = get_top_skills_for_role(role, top_n)
    return (tuple(skills), sources)


def analyze_skill_gaps_optimized(
    user_skills: List[str], target_role: str, top_n: int = 10
) -> Dict:
    """
    Optimized skill gap analysis with LLM extraction.

    Args:
        user_skills: List of skills user already has
        target_role: Target job role
        top_n: Number of top missing skills to return

    Returns:
        Dict with:
            - required_skills: Top N required skills for role
            - missing_skills: Top N missing skills user needs
            - matched_jobs_count: Sources analyzed (1 for LLM)
            - source: 'llm' or 'fallback'
    """
    top_required_skills, sources = get_top_skills_for_role_cached(
        target_role, top_n=top_n
    )
    top_required_skills = list(top_required_skills)

    cache_key = f"{target_role.lower().strip()}:{top_n}"
    source = _SKILL_CACHE.get(cache_key, {}).get("source", "llm")

    user_skills_lower = [s.lower().strip() for s in user_skills]
    missing = []

    for skill in top_required_skills:
        skill_lower = skill.lower()
        if not any(skill_lower in us or us in skill_lower for us in user_skills_lower):
            missing.append(skill)

    missing_cleaned = clean_and_deduplicate_skills(missing, max_skills=top_n)

    return {
        "required_skills": top_required_skills,
        "missing_skills": missing_cleaned,
        "matched_jobs_count": sources,
        "source": source,
    }


def clear_skill_cache():
    """Clear the skill cache."""
    global _SKILL_CACHE
    _SKILL_CACHE.clear()
    get_top_skills_for_role_cached.cache_clear()
    extract_skills_with_llm.cache_clear()
