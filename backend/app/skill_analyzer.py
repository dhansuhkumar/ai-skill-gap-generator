# backend/app/skill_analyzer.py
"""
Optimized Skill Gap Analyzer using web search (DuckDuckGo).

Replaces HuggingFace dataset downloads with targeted web searches for speed.
"""

import functools
from typing import List, Dict, Tuple
from collections import Counter

from .web_skill_extractor import search_role_skills, get_tech_skills_vocab
from .skill_cleaner import clean_and_deduplicate_skills


@functools.lru_cache(maxsize=100)
def get_top_skills_for_role_cached(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Cached version of get_top_skills_for_role.
    Returns tuple for hashability.
    """
    skills, count = get_top_skills_for_role(role, top_n)
    return (tuple(skills), count)


def get_top_skills_for_role(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Get top N most frequently required skills for a role using web search.

    Args:
        role: Target job role
        top_n: Number of top skills to return

    Returns:
        Tuple of (top_skills_list, sources_analyzed)
    """
    print(f"🔍 Searching skills for role: {role}")

    top_skills, sources = search_role_skills(role, top_n=top_n)

    if not top_skills:
        print(f"⚠️ No skills found for role: {role}")
        return ([], 0)

    print(f"✅ Found {len(top_skills)} skills from {sources} sources")

    return (top_skills, sources)


def analyze_skill_gaps_optimized(
    user_skills: List[str], target_role: str, top_n: int = 10
) -> Dict:
    """
    Optimized skill gap analysis with web search and frequency ranking.

    Args:
        user_skills: List of skills user already has
        target_role: Target job role
        top_n: Number of top missing skills to return

    Returns:
        Dict with:
            - required_skills: Top N required skills for role
            - missing_skills: Top N missing skills user needs
            - matched_jobs_count: Number of sources analyzed
            - source: 'web_search'
    """
    top_required_skills, sources = get_top_skills_for_role_cached(
        target_role, top_n=top_n
    )
    top_required_skills = list(top_required_skills)

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
        "source": "web_search",
    }


def clear_skill_cache():
    """Clear the LRU cache for skill analysis."""
    get_top_skills_for_role_cached.cache_clear()
    search_role_skills.cache_clear() if hasattr(
        search_role_skills, "cache_clear"
    ) else None
