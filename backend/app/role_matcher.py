# backend/app/role_matcher.py
"""
Role Matcher - Fuzzy matching for job roles using web search.
Provides intelligent job title matching without HuggingFace.
"""

import re
from typing import List, Dict

from .web_skill_extractor import search_role_skills


ROLE_ALIASES = {
    "frontend": ["front end", "front-end", "frontend", "ui developer", "web developer"],
    "backend": ["back end", "back-end", "backend", "server side", "api developer"],
    "fullstack": ["full stack", "full-stack", "fullstack", "full stack developer"],
    "data scientist": ["data science", "data scientist", "data analyst"],
    "data engineer": ["data engineering", "data engineer", "etl developer"],
    "machine learning": ["machine learning", "ml engineer", "ml", "ai engineer"],
    "devops": ["devops", "sre", "site reliability", "platform engineer"],
    "software engineer": [
        "software engineer",
        "software developer",
        "sde",
        "developer",
    ],
    "web developer": ["web developer", "web dev", "website developer"],
    "mobile developer": [
        "mobile developer",
        "android developer",
        "ios developer",
        "flutter developer",
    ],
    "cloud engineer": ["cloud engineer", "aws", "azure", "gcp", "cloud architect"],
    "qa engineer": ["qa", "quality assurance", "test engineer", "sdET"],
    "security engineer": ["security", "cybersecurity", "infosec", "security analyst"],
    "product manager": ["product manager", "product owner", "pm"],
    "project manager": ["project manager", "project management", "pm"],
}


def _normalize_role_name(role: str) -> str:
    """Normalize role name for better matching."""
    if not role:
        return ""

    role = role.lower().strip()
    role = re.sub(
        r"\b(senior|junior|lead|principal|staff|entry level|mid|mid-level|level \d+)\b",
        "",
        role,
    )
    role = re.sub(r"[^a-z0-9\s]", " ", role)
    role = re.sub(r"\s+", " ", role).strip()

    return role


def _get_role_category(role: str) -> str:
    """Determine the category of a role for better matching."""
    role_lower = role.lower()

    for category, aliases in ROLE_ALIASES.items():
        for alias in aliases:
            if alias in role_lower:
                return category

    return role_lower


def find_similar_roles(query: str, limit: int = 10) -> List[str]:
    """
    Find roles similar to the query using web search.
    """
    try:
        from ddgs import DDGS

        suggestions = []
        seen = set()

        queries = [
            f'"{query}" job roles titles',
            f"{query} developer positions",
            f"{query} career paths",
        ]

        with DDGS() as ddgs:
            for q in queries:
                if len(suggestions) >= limit:
                    break
                for r in ddgs.text(q, max_results=limit):
                    title = r.get("title", "").split(" - ")[0].split(" | ")[0].strip()
                    if title and title.lower() not in seen and len(title) > 3:
                        seen.add(title.lower())
                        suggestions.append(title)

        return suggestions[:limit]
    except Exception:
        return []


def match_role_to_csv(role_query: str, limit_jobs: int = 20) -> Dict:
    """
    Match a user-input role to web search job data.
    Returns matched jobs and their required skills.
    """
    skills, sources = search_role_skills(role_query, top_n=limit_jobs)

    return {
        "matched_jobs": [],
        "required_skills": skills,
        "role_query": role_query,
        "matched_count": sources,
    }


def compute_missing_skills(
    user_skills: List[str], required_skills: List[str]
) -> List[str]:
    """
    Compute missing skills by comparing user skills to required skills.
    """
    user_skills_normalized = {s.strip().lower() for s in user_skills if s}

    missing = []
    for skill in required_skills:
        skill_normalized = skill.strip().lower()
        if skill_normalized and skill_normalized not in user_skills_normalized:
            missing.append(skill)

    return missing


def autocomplete_role(query: str, limit: int = 10) -> List[str]:
    """Get role suggestions for autocomplete."""
    return find_similar_roles(query, limit)
