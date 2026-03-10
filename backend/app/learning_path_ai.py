# backend/app/learning_path_ai.py
"""
AI-Powered Learning Path Generator
Optimized for free-tier API usage with caching and efficient prompts.
"""

import json
import logging
from typing import List, Dict, Optional
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

# In-memory cache for AI responses to minimize API calls
_AI_CACHE = {}

def _generate_cache_key(skill: str, role: str, days: int, hours: float, pace: str) -> str:
    """Generate a cache key for AI responses."""
    key_str = f"{skill}|{role}|{days}|{hours}|{pace}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _build_learning_path_prompt(
    skill: str,
    role: str,
    days: int,
    hours: float,
    pace: str,
    context: str = ""
) -> str:
    """
    Build an optimized AI prompt for learning path generation.
    Designed to be concise to save tokens on free-tier APIs.
    """
    prompt = f"""Generate a {days}-day learning plan for {skill} targeting {role} position.

Daily time: {hours}h, Pace: {pace}
{f'Context: {context}' if context else ''}

Provide JSON with this exact structure:
{{
  "summary": "Brief overview of the learning journey",
  "steps": [
    {{
      "day_from": 1,
      "day_to": 5,
      "title": "Phase name",
      "tasks": ["Task 1", "Task 2", "Task 3"],
      "project": "Hands-on project description"
    }}
  ]
}}

Requirements:
- 2-4 phases based on duration
- 3-4 specific tasks per phase
- 1 practical project per phase
- Focus on {role}-relevant skills
- Be concise and actionable

Return ONLY valid JSON, no markdown or explanation."""

    return prompt


def _build_projects_prompt(
    skills: List[str],
    role: str,
    project_type: str,
    context: str = ""
) -> str:
    """
    Build an optimized AI prompt for project recommendations.
    Designed to be concise to save tokens.
    """
    skills_str = ", ".join(skills)
    
    prompt = f"""Generate 3-4 {project_type} project ideas for {role} using: {skills_str}

{f'Context: {context}' if context else ''}

Provide JSON with this exact structure:
{{
  "projects": [
    {{
      "title": "Project name",
      "description": "Brief description (1-2 sentences)",
      "skills": ["skill1", "skill2"]
    }}
  ]
}}

Requirements:
- Real-world applicable projects
- Suitable for {project_type} portfolio
- Demonstrate {role} competency
- Each project uses 2+ skills from the list

Return ONLY valid JSON, no markdown or explanation."""

    return prompt


def _parse_ai_response(response_text: str) -> Optional[Dict]:
    """
    Parse AI response and extract JSON.
    Handles markdown code blocks and other formatting.
    """
    try:
        # Try direct JSON parse first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        
        # Look for JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for raw JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to parse AI response as JSON: {response_text[:200]}")
        return None


def generate_ai_learning_path(
    skill: str,
    role: str,
    days: int,
    hours: float,
    pace: str,
    context: str = "",
    requested_provider: Optional[str] = None,
    include_youtube: bool = True
) -> Dict:
    """
    Generate a learning path for a single skill.
    Uses HuggingFace retrieval for instant, deterministic results.
    Falls back to heuristic generation if no curated data exists.
    
    Args:
        skill: The skill to learn
        role: Target job role
        days: Number of days available
        hours: Daily hours available
        pace: Learning pace (Fast/Balanced/Thorough)
        context: Additional context from user
        requested_provider: Ignored (kept for API compatibility)
        include_youtube: Whether to include YouTube video recommendations
    
    Returns:
        Dict with 'summary', 'steps', and optionally 'youtube_videos' keys
    """
    # Check cache first
    cache_key = _generate_cache_key(skill, role, days, hours, pace)
    if cache_key in _AI_CACHE:
        logger.info(f"✅ Using cached learning path for {skill}")
        return _AI_CACHE[cache_key]
    
    # Use HuggingFace retrieval (instant, no API cost)
    result = None
    try:
        from .hf_data_loader import get_learning_path_for_skill
        
        logger.info(f"📚 Retrieving learning path for {skill} from HuggingFace")
        
        result = get_learning_path_for_skill(skill, days)
        
        if result and 'steps' in result:
            logger.info(f"✅ Learning path retrieved for {skill}")
        else:
            result = None
        
    except Exception as e:
        logger.error(f"Retrieval failed for {skill}: {e}")
    
    # Use fallback if HuggingFace failed
    if not result:
        result = _generate_fallback_learning_path(skill, role, days)
    
    # Add YouTube videos if requested
    if include_youtube:
        try:
            from .youtube_search import search_youtube_videos
            
            query = f"{skill} tutorial for beginners {role}"
            videos = search_youtube_videos(query, max_results=3, allow_search=True)
            
            if videos:
                result['youtube_videos'] = videos
                logger.info(f"🎬 Added {len(videos)} YouTube videos for {skill}")
        except Exception as e:
            logger.error(f"YouTube search failed for {skill}: {e}")
            result['youtube_videos'] = []
    
    # Cache the result
    _AI_CACHE[cache_key] = result
    return result


def _generate_fallback_learning_path(skill: str, role: str, days: int) -> Dict:
    """
    Fallback heuristic learning path when AI is unavailable.
    Simple but functional.
    """
    if days >= 21:
        # Multi-phase learning
        phase1_days = days // 3
        phase2_days = days // 3
        phase3_days = days - phase1_days - phase2_days
        
        return {
            "summary": f"Master {skill} for {role} in {days} days",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": phase1_days,
                    "title": f"{skill} Fundamentals",
                    "tasks": [
                        f"Learn core {skill} concepts",
                        f"Complete beginner tutorials",
                        f"Practice basic {skill} exercises"
                    ],
                    "project": f"Simple {skill} starter project"
                },
                {
                    "day_from": phase1_days + 1,
                    "day_to": phase1_days + phase2_days,
                    "title": f"Intermediate {skill}",
                    "tasks": [
                        f"Build practical {skill} projects",
                        f"Learn advanced {skill} features",
                        f"Study best practices"
                    ],
                    "project": f"{skill} intermediate project for {role}"
                },
                {
                    "day_from": phase1_days + phase2_days + 1,
                    "day_to": days,
                    "title": f"Advanced {skill} & Integration",
                    "tasks": [
                        f"Master advanced {skill} concepts",
                        f"Integrate {skill} with other technologies",
                        f"Build portfolio project"
                    ],
                    "project": f"Complete {skill} portfolio project"
                }
            ]
        }
    else:
        # Single-phase for short timelines
        return {
            "summary": f"Learn {skill} for {role} in {days} days",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": days,
                    "title": f"Learn {skill}",
                    "tasks": [
                        f"Study {skill} fundamentals",
                        f"Complete {skill} tutorials",
                        f"Build a small {skill} project"
                    ],
                    "project": f"{skill} practice project"
                }
            ]
        }


def generate_ai_projects(
    skills: List[str],
    role: str,
    project_type: str,
    context: str = "",
    requested_provider: Optional[str] = None
) -> List[Dict]:
    """
    Get curated project recommendations from HuggingFace.
    Instant retrieval, no API costs.
    
    Args:
        skills: List of skills to incorporate
        role: Target job role
        project_type: Type of project (portfolio/practice/production)
        context: Additional context from user
        requested_provider: Ignored (kept for API compatibility)
    
    Returns:
        List of project dictionaries with title, description, and skills
    """
    # Check cache
    cache_key = hashlib.md5(f"{','.join(sorted(skills))}|{role}|{project_type}".encode()).hexdigest()
    if cache_key in _AI_CACHE:
        logger.info(f"✅ Using cached projects for {role}")
        return _AI_CACHE[cache_key]
    
    # Use HuggingFace retrieval (instant, no API cost)
    try:
        from .hf_data_loader import get_projects_for_skills
        
        logger.info(f"📚 Retrieving projects for {role} from HuggingFace")
        
        projects = get_projects_for_skills(skills, limit=5)
        
        if projects:
            # Cache the result
            _AI_CACHE[cache_key] = projects
            logger.info(f"✅ Retrieved {len(projects)} projects")
            return projects
        
    except Exception as e:
        logger.error(f"Project retrieval failed: {e}")
    
    # Fallback to simple projects
    return _generate_fallback_projects(skills, role, project_type)


def _generate_fallback_projects(skills: List[str], role: str, project_type: str) -> List[Dict]:
    """Fallback project generation when AI is unavailable."""
    projects = []
    
    # Individual skill projects
    for skill in skills[:3]:  # Limit to 3
        projects.append({
            "title": f"{skill} {project_type.capitalize()} Project",
            "description": f"Build a {project_type} project demonstrating {skill} skills for {role} position",
            "skills": [skill]
        })
    
    # Capstone project combining all skills
    if len(skills) > 1:
        projects.append({
            "title": f"{role} Capstone Project",
            "description": f"Comprehensive {project_type} project combining {', '.join(skills)} for {role}",
            "skills": skills
        })
    
    return projects
