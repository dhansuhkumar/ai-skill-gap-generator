# backend/app/role_matcher.py
"""
Role Matcher - Fuzzy matching for job roles against CSV data.
Provides intelligent job title matching without AI.
"""

import re
from typing import List, Dict, Tuple
from difflib import get_close_matches

from .db_data_loader import (
    db_loader,
    get_all_job_titles,
    find_matching_jobs,
    get_similar_job_titles
)


# Common role name variations mappings
ROLE_ALIASES = {
    'frontend': ['front end', 'front-end', 'frontend', 'ui developer', 'web developer'],
    'backend': ['back end', 'back-end', 'backend', 'server side', 'api developer'],
    'fullstack': ['full stack', 'full-stack', 'fullstack', 'full stack developer'],
    'data scientist': ['data science', 'data scientist', 'data analyst'],
    'data engineer': ['data engineering', 'data engineer', 'etl developer'],
    'machine learning': ['machine learning', 'ml engineer', 'ml', 'ai engineer'],
    'devops': ['devops', 'sre', 'site reliability', 'platform engineer'],
    'software engineer': ['software engineer', 'software developer', 'sde', 'developer'],
    'web developer': ['web developer', 'web dev', 'website developer'],
    'mobile developer': ['mobile developer', 'android developer', 'ios developer', 'flutter developer'],
    'cloud engineer': ['cloud engineer', 'aws', 'azure', 'gcp', 'cloud architect'],
    'qa engineer': ['qa', 'quality assurance', 'test engineer', 'sdET'],
    'security engineer': ['security', 'cybersecurity', 'infosec', 'security analyst'],
    'product manager': ['product manager', 'product owner', 'pm'],
    'project manager': ['project manager', 'project management', 'pm'],
}


def _normalize_role_name(role: str) -> str:
    """Normalize role name for better matching."""
    if not role:
        return ""
    
    role = role.lower().strip()
    
    # Remove common suffixes/prefixes
    role = re.sub(r'\b(senior|junior|lead|principal|staff|entry level|mid|mid-level|level \d+)\b', '', role)
    
    # Remove special characters
    role = re.sub(r'[^a-z0-9\s]', ' ', role)
    
    # Normalize spaces
    role = re.sub(r'\s+', ' ', role).strip()
    
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
    Find roles similar to the query using fuzzy matching.
    """
    all_titles = get_all_job_titles()
    if not all_titles:
        return []
    
    query_lower = query.lower()
    normalized_query = _normalize_role_name(query)
    
    # First, try direct substring matching
    direct_matches = [t for t in all_titles if query_lower in t.lower()]
    
    if direct_matches:
        return direct_matches[:limit]
    
    # Try fuzzy matching for similar titles
    if all_titles:
        close = get_close_matches(query, all_titles, n=limit, cutoff=0.4)
        if close:
            return close
    
    # Try matching against known role aliases
    query_category = _get_role_category(query)
    alias_matches = []
    for title in all_titles:
        title_category = _get_role_category(title)
        if query_category == title_category or query_category in title.lower():
            alias_matches.append(title)
    
    if alias_matches:
        return alias_matches[:limit]
    
    # Fallback: return titles that contain any word from query
    query_words = query_lower.split()
    word_matches = []
    for title in all_titles:
        title_lower = title.lower()
        if any(word in title_lower for word in query_words):
            word_matches.append(title)
    
    return word_matches[:limit] if word_matches else list(all_titles)[:limit]


def match_role_to_csv(role_query: str, limit_jobs: int = 20) -> Dict:
    """
    Match a user-input role to CSV job data.
    Returns matched jobs and their required skills.
    
    Args:
        role_query: The role the user is interested in
        limit_jobs: Maximum number of jobs to consider
    
    Returns:
        Dict with:
            - matched_jobs: List of job dicts from CSV
            - required_skills: List of required skills for those jobs
            - role_query: Original query
            - matched_count: Number of jobs found
    """
    # Find matching jobs in CSV
    matched_jobs = find_matching_jobs(role_query, limit=limit_jobs)
    
    if not matched_jobs:
        # Try fuzzy matching
        similar_roles = find_similar_roles(role_query, limit=5)
        if similar_roles:
            # Try to find jobs for the most similar role
            for similar_role in similar_roles:
                jobs = find_matching_jobs(similar_role, limit=limit_jobs)
                if jobs:
                    matched_jobs = jobs
                    break
    
    # Get required skills for matched jobs
    if matched_jobs:
        job_titles = [j['job_title'] for j in matched_jobs]
        required_skills = db_loader.get_skills_for_job_titles(job_titles)
    else:
        required_skills = []
    
    # Deduplicate skills while preserving order
    seen = set()
    unique_skills = []
    for skill in required_skills:
        skill_lower = skill.strip().lower()
        if skill_lower and skill_lower not in seen:
            seen.add(skill_lower)
            unique_skills.append(skill)
    
    return {
        'matched_jobs': matched_jobs,
        'required_skills': unique_skills,
        'role_query': role_query,
        'matched_count': len(matched_jobs)
    }


def compute_missing_skills(user_skills: List[str], required_skills: List[str]) -> List[str]:
    """
    Compute missing skills by comparing user skills to required skills.
    
    Args:
        user_skills: List of skills the user has
        required_skills: List of skills required for the role
    
    Returns:
        List of missing skills
    """
    # Normalize user skills
    user_skills_normalized = {s.strip().lower() for s in user_skills if s}
    
    missing = []
    for skill in required_skills:
        skill_normalized = skill.strip().lower()
        if skill_normalized and skill_normalized not in user_skills_normalized:
            missing.append(skill)
    
    return missing


def autocomplete_role(query: str, limit: int = 10) -> List[str]:
    """
    Get role suggestions for autocomplete.
    """
    return get_similar_job_titles(query, limit)


# Test function
if __name__ == '__main__':
    # Test the role matcher
    test_queries = [
        'software developer',
        'frontend',
        'data scientist',
        'devops',
        'full stack',
    ]
    
    print("Testing Role Matcher:")
    print("=" * 50)
    
    for query in test_queries:
        result = match_role_to_csv(query)
        print(f"\nQuery: '{query}'")
        print(f"Matched {result['matched_count']} jobs")
        print(f"Found {len(result['required_skills'])} unique skills")
        print(f"Top 5 skills: {result['required_skills'][:5]}")
