# backend/app/ai_generator.py
"""
AI Generator - CSV-based skill gap analysis (AI code removed).
All functionality now uses CSV data only.
"""

import os
import json
import logging
import time
from typing import List, Optional, Dict

from .db_data_loader import (
    db_loader,
    get_required_skills,
    find_matching_jobs
)
from .role_matcher import (
    match_role_to_csv,
    compute_missing_skills
)
from .youtube_search import search_youtube_videos

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Always use database mode - no AI
USE_DB_MODE = True


# ==================== CSV-BASED SKILL GAP ANALYSIS ====================

def analyze_skill_gaps(user_skills: List[str], target_role: str, top_n: int = 10) -> Dict:
    """
    CSV-based skill gap analysis with optimization.
    Returns TOP N most important missing skills (frequency-based).
    
    Args:
        user_skills: List of skills the user already has
        target_role: The role the user is targeting
        top_n: Number of top skills to return (default: 10)
    
    Returns:
        Dict with:
            - required_skills: Top N required skills for the role
            - missing_skills: Top N skills user needs to learn
            - matched_jobs_count: Number of jobs analyzed
            - source: "csv_optimized"
    """
    from .skill_analyzer import analyze_skill_gaps_optimized
    
    # Use optimized analyzer with caching
    result = analyze_skill_gaps_optimized(user_skills, target_role, top_n=top_n)
    
    return {
        'required_skills': result['required_skills'],
        'missing_skills': result['missing_skills'],
        'matched_count': result['matched_jobs_count'],
        'source': result['source']
    }



def get_learning_resources_csv(missing_skills: List[str]) -> Dict[str, List[Dict]]:
    """
    Get YouTube video resources for each missing skill.
    
    Args:
        missing_skills: List of skills to find resources for
    
    Returns:
        Dict mapping each skill to a list of video resources
    """
    resources = {}
    
    for skill in missing_skills[:5]:  # Limit to 5 skills to avoid issues
        videos = search_youtube_videos(f"{skill} tutorial", max_results=3)
        if videos:
            resources[skill] = videos
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    return resources


def get_unified_analysis(user_skills: List[str], target_role: str) -> Dict:
    """
    Unified analysis function that uses CSV data.
    
    Args:
        user_skills: List of skills the user has
        target_role: Target job role
    
    Returns:
        Dict with required_skills, missing_skills, and resources
    """
    try:
        # Get skill gap analysis from CSV
        gap_analysis = analyze_skill_gaps(user_skills, target_role)
        
        # Get YouTube resources for missing skills
        missing_skills = gap_analysis.get('missing_skills', [])
        resources = get_learning_resources_csv(missing_skills)
        
        return {
            'required_skills': gap_analysis.get('required_skills', []),
            'missing_skills': missing_skills,
            'matched_jobs': gap_analysis.get('matched_jobs', []),
            'resources': resources,
            'source': 'csv'
        }
    except Exception as e:
        logger.error(f"CSV analysis failed: {e}")
        # Return empty result on error
        return {
            'required_skills': [],
            'missing_skills': [],
            'matched_jobs': [],
            'resources': {},
            'source': 'csv_error'
        }


def generate_learning_plan(
    selected_skills: List[str],
    role: str,
    days: int = 30,
    hours: float = 1.0,
    project_type: str = "portfolio",
    learning_pace: str = "Balanced",
    time_commitment: str = "1 hour",
    context: str = "",
    requested_provider: Optional[str] = None
) -> Dict:
    """
    Generate an AI-powered learning plan for selected skills.
    Optimized for free-tier API usage with caching and efficient prompts.
    
    Args:
        selected_skills: List of skills to learn
        role: Target job role
        days: Total days available
        hours: Daily hours available
        project_type: Type of project (portfolio, practice, production)
        learning_pace: Learning pace (Fast, Balanced, Thorough)
        time_commitment: Time commitment string
        context: Additional context from user
        requested_provider: AI provider (gemini/openai/groq or None for auto)
    
    Returns:
        Dict with learning_paths, projects, and matching_score
    """
    from .learning_path_ai import generate_ai_learning_path, generate_ai_projects
    
    logger.info(f"🚀 Generating AI learning plan for {len(selected_skills)} skills over {days} days")
    logger.info(f"   Provider: {requested_provider or 'auto'}, Pace: {learning_pace}")
    
    # Distribute days across skills
    days_per_skill = max(3, days // len(selected_skills)) if selected_skills else days
    
    learning_paths = {}
    
    # Generate AI-powered learning path for each skill
    for i, skill in enumerate(selected_skills):
        # Calculate day range for this skill
        start_day = (i * days_per_skill) + 1
        end_day = min((i + 1) * days_per_skill, days)
        skill_days = end_day - start_day + 1
        
        logger.info(f"   Generating path for {skill} (days {start_day}-{end_day})")
        
        try:
            # Use AI to generate learning path
            ai_path = generate_ai_learning_path(
                skill=skill,
                role=role,
                days=skill_days,
                hours=hours,
                pace=learning_pace,
                context=context,
                requested_provider=requested_provider
            )
            
            # Adjust day numbers to match overall timeline
            if ai_path and "steps" in ai_path:
                for step in ai_path["steps"]:
                    step["day_from"] = step.get("day_from", 1) + start_day - 1
                    step["day_to"] = step.get("day_to", skill_days) + start_day - 1
                
                learning_paths[skill] = ai_path
                logger.info(f"   ✅ AI path generated for {skill}")
            else:
                logger.warning(f"   ⚠️ AI path invalid for {skill}, using fallback")
                # Fallback is already handled in generate_ai_learning_path
                learning_paths[skill] = ai_path
                
        except Exception as e:
            logger.error(f"   ❌ Error generating path for {skill}: {e}")
            # Use simple fallback
            learning_paths[skill] = {
                "summary": f"Learn {skill} for {role}",
                "steps": [{
                    "day_from": start_day,
                    "day_to": end_day,
                    "title": f"Learn {skill}",
                    "tasks": [
                        f"Study {skill} fundamentals",
                        f"Complete {skill} tutorials",
                        f"Build practice projects"
                    ],
                    "project": f"{skill} practice project"
                }]
            }
    
    # Generate AI-powered project recommendations
    logger.info(f"   Generating projects for {role}")
    try:
        projects = generate_ai_projects(
            skills=selected_skills,
            role=role,
            project_type=project_type,
            context=context,
            requested_provider=requested_provider
        )
        logger.info(f"   ✅ {len(projects)} projects generated")
    except Exception as e:
        logger.error(f"   ❌ Error generating projects: {e}")
        # Simple fallback
        projects = [{
            "title": f"{role} Portfolio Project",
            "description": f"Build a comprehensive project using {', '.join(selected_skills)}",
            "skills": selected_skills
        }]
    
    # Calculate matching score based on number of skills
    matching_score = max(30, min(95, 50 + (len(selected_skills) * 8)))
    
    logger.info(f"✅ Learning plan generation complete!")
    
    return {
        "learning_paths": learning_paths,
        "projects": projects,
        "matching_score": matching_score,
        "source": requested_provider or "ai_auto"
    }



# ==================== REMOVED AI FUNCTIONS ====================

# All AI-based functions have been removed:
# - _call_gemini, _call_groq, _call_openai (API calls)
# - _generate_ai_response (orchestrator)
# - analyze_skill_gaps_ai (was fallback)
# - extract_skills_with_ai
# - generate_learning_plan (was AI-based)
# - Provider state management (PROVIDERS, circuit breaker)
