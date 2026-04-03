# backend/app/role_suggestions.py
"""
Alternative Role Suggestions - Find roles user has high chance to become.
Uses web search instead of HuggingFace datasets.
"""

from typing import List, Dict
from .web_skill_extractor import search_role_skills, get_tech_skills_vocab
from .skill_cleaner import clean_and_deduplicate_skills


COMMON_ROLES = [
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Software Engineer",
    "Data Scientist",
    "Data Engineer",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Mobile Developer",
    "QA Engineer",
    "Security Engineer",
    "Product Manager",
    "Web Developer",
    "UI/UX Designer",
]


def get_alternative_roles(user_skills: List[str], limit: int = 5) -> List[Dict]:
    """
    Find alternative roles user has high chance to become based on their current skills.

    Args:
        user_skills: List of skills the user already has
        limit: Number of alternative roles to return

    Returns:
        List of dicts with role, match_score, etc.
    """
    print(f"🔍 Finding alternative roles for {len(user_skills)} user skills")

    if not user_skills:
        return []

    user_skills_lower = {s.lower().strip() for s in user_skills}
    role_matches = []

    for role in COMMON_ROLES:
        required_skills, sources = search_role_skills(role, top_n=20)

        if not required_skills:
            continue

        required_lower = {s.lower().strip() for s in required_skills}
        matched = user_skills_lower.intersection(required_lower)

        if required_lower:
            match_score = int((len(matched) / len(required_lower)) * 100)
        else:
            match_score = 0

        if match_score >= 15:
            role_matches.append(
                {
                    "role": role,
                    "match_score": match_score,
                    "user_skills_count": len(matched),
                    "required_skills_count": len(required_lower),
                    "missing_skills_count": len(required_lower) - len(matched),
                }
            )

    role_matches.sort(key=lambda x: x["match_score"], reverse=True)
    print(f"✅ Found {len(role_matches)} alternative roles")

    return role_matches[:limit]
