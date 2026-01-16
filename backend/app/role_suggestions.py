# backend/app/role_suggestions.py
"""
Alternative Role Suggestions - Find roles user has high chance to become.
"""

from typing import List, Dict
from collections import Counter
from .db_data_loader import db_loader, find_matching_jobs
from .skill_cleaner import clean_and_deduplicate_skills


def get_alternative_roles(user_skills: List[str], limit: int = 5) -> List[Dict]:
    """
    Find alternative roles user has high chance to become based on their current skills.
    
    Args:
        user_skills: List of skills the user already has
        limit: Number of alternative roles to return
    
    Returns:
        List of dicts with:
            - role: Role name
            - match_score: Percentage match (0-100)
            - user_skills_count: How many required skills user has
            - required_skills_count: Total required skills for role
            - missing_skills_count: How many skills user needs to learn
    """
    print(f"🔍 Finding alternative roles for {len(user_skills)} user skills")
    
    # Get all unique job titles from database
    all_job_titles = db_loader.get_all_job_titles()
    
    if not all_job_titles:
        print("❌ No job titles found")
        return []
    
    # Sample popular roles (limit to 50 for performance)
    # Prioritize roles that appear frequently
    role_counts = Counter()
    for title in all_job_titles[:1000]:  # Check first 1000 titles
        # Normalize title (remove seniority levels)
        normalized = title.lower()
        for prefix in ['senior', 'junior', 'lead', 'principal', 'staff', 'entry']:
            normalized = normalized.replace(prefix, '').strip()
        role_counts[normalized] += 1
    
    # Get top 50 most common roles
    popular_roles = [role for role, count in role_counts.most_common(50)]
    
    print(f"✅ Analyzing {len(popular_roles)} popular roles")
    
    # Calculate match score for each role
    role_matches = []
    
    for role in popular_roles:
        # Find jobs for this role
        matched_jobs = find_matching_jobs(role, limit=100)
        
        if not matched_jobs:
            continue
        
        # Get required skills for this role
        job_links = [job.get('job_link') for job in matched_jobs if job.get('job_link')]
        skills_map = db_loader.get_skills_for_job_links(job_links[:50])  # Limit for speed
        
        if not skills_map:
            continue
        
        # Collect all required skills
        all_required = []
        for job_skills in skills_map.values():
            all_required.extend(job_skills)
        
        # Clean and deduplicate
        required_skills = clean_and_deduplicate_skills(all_required)
        
        if not required_skills:
            continue
        
        # Calculate how many user skills match
        user_skills_lower = {s.lower().strip() for s in user_skills}
        required_skills_lower = {s.lower().strip() for s in required_skills}
        
        matched_skills = user_skills_lower.intersection(required_skills_lower)
        
        # Calculate match score
        if len(required_skills) > 0:
            match_score = int((len(matched_skills) / len(required_skills)) * 100)
        else:
            match_score = 0
        
        # Only include roles with at least 20% match
        if match_score >= 20:
            role_matches.append({
                'role': role.title(),  # Capitalize for display
                'match_score': match_score,
                'user_skills_count': len(matched_skills),
                'required_skills_count': len(required_skills),
                'missing_skills_count': len(required_skills) - len(matched_skills)
            })
    
    # Sort by match score descending
    role_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    print(f"✅ Found {len(role_matches)} alternative roles")
    
    # Return top N
    return role_matches[:limit]
