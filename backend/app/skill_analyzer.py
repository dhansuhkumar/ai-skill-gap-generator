# backend/app/skill_analyzer.py
"""
Optimized Skill Gap Analyzer with caching and frequency-based ranking.
"""

import functools
from typing import List, Dict, Tuple
from collections import Counter

from .db_data_loader import db_loader, find_matching_jobs
from .role_matcher import match_role_to_csv, compute_missing_skills
from .skill_cleaner import clean_and_deduplicate_skills, rank_skills_by_frequency


# LRU Cache for role analysis (cache up to 100 different role queries)
@functools.lru_cache(maxsize=100)
def get_top_skills_for_role_cached(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Cached version of get_top_skills_for_role.
    Returns tuple for hashability.
    """
    skills, job_count = get_top_skills_for_role(role, top_n)
    return (tuple(skills), job_count)


def get_top_skills_for_role(role: str, top_n: int = 10) -> Tuple[List[str], int]:
    """
    Get top N most frequently required skills for a role.
    
    Args:
        role: Target job role
        top_n: Number of top skills to return
    
    Returns:
        Tuple of (top_skills_list, total_jobs_analyzed)
    """
    print(f"🔍 Analyzing role: {role}")
    
    # Find matching jobs (limit to 500 for speed)
    matched_jobs = find_matching_jobs(role, limit=500)
    
    if not matched_jobs:
        print(f"❌ No jobs found for role: {role}")
        return ([], 0)
    
    print(f"✅ Found {len(matched_jobs)} matching jobs")
    
    # Get job_links from matched jobs
    job_links = [job.get('job_link') for job in matched_jobs if job.get('job_link')]
    
    if not job_links:
        print(f"❌ No job_links found in matched jobs")
        return ([], 0)
    
    print(f"✅ Extracted {len(job_links)} job links")
    
    # Get skills for all job links
    skills_map = db_loader.get_skills_for_job_links(job_links)
    
    if not skills_map:
        print(f"❌ No skills found for job links")
        return ([], 0)
    
    print(f"✅ Found skills for {len(skills_map)} jobs")
    
    # Count skill frequency across all jobs
    skill_counter = Counter()
    total_raw_skills = 0
    
    for job_link, job_skills in skills_map.items():
        total_raw_skills += len(job_skills)
        
        # Clean skills before counting (minimal validation now)
        cleaned_job_skills = clean_and_deduplicate_skills(job_skills)
        
        # Update counter
        for skill in cleaned_job_skills:
            skill_counter[skill] += 1
    
    print(f"✅ Processed {total_raw_skills} raw skills")
    print(f"✅ Counted {len(skill_counter)} unique skills after cleaning")
    
    # Get top N skills by frequency
    top_skills = rank_skills_by_frequency(dict(skill_counter), top_n=top_n)
    
    print(f"✅ Returning top {len(top_skills)} skills: {top_skills}")
    
    return (top_skills, len(matched_jobs))


def analyze_skill_gaps_optimized(
    user_skills: List[str],
    target_role: str,
    top_n: int = 10
) -> Dict:
    """
    Optimized skill gap analysis with caching and frequency ranking.
    
    Args:
        user_skills: List of skills user already has
        target_role: Target job role
        top_n: Number of top missing skills to return
    
    Returns:
        Dict with:
            - required_skills: Top N required skills for role
            - missing_skills: Top N missing skills user needs
            - matched_jobs_count: Number of jobs analyzed
            - source: 'csv_optimized'
    """
    # Get top skills for role (uses cache)
    top_required_skills, job_count = get_top_skills_for_role_cached(target_role, top_n=top_n)
    top_required_skills = list(top_required_skills)  # Convert from tuple
    
    # Compute missing skills
    missing = compute_missing_skills(user_skills, top_required_skills)
    
    # Clean and limit missing skills
    missing_cleaned = clean_and_deduplicate_skills(missing, max_skills=top_n)
    
    return {
        'required_skills': top_required_skills,
        'missing_skills': missing_cleaned,
        'matched_jobs_count': job_count,
        'source': 'csv_optimized'
    }


def clear_skill_cache():
    """Clear the LRU cache for skill analysis."""
    get_top_skills_for_role_cached.cache_clear()
