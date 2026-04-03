# backend/app/learning_path_ai.py
"""
AI-Powered Learning Path Generator - FAST VERSION.

Key optimization: Fire Groq AI call IMMEDIATELY without waiting for web searches.
Web searches run in background, results update the path if available.

Speed target: ~5 seconds per skill (vs 40+ seconds before)
"""

import json
import logging
import re
import hashlib
import threading
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

_AI_CACHE = {}
_WEB_RESULTS = {}  # Background web search results

MAX_WORKERS = 3

DEFAULT_ROADMAPS = {
    "Python": [
        {
            "title": "Python Official Tutorial",
            "url": "https://docs.python.org/3/tutorial/",
        },
        {"title": "Real Python", "url": "https://realpython.com/"},
        {
            "title": "Automate the Boring Stuff",
            "url": "https://automatetheboringstuff.com/",
        },
    ],
    "JavaScript": [
        {
            "title": "MDN JavaScript Guide",
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        },
        {"title": "JavaScript.info", "url": "https://javascript.info/"},
        {"title": "Eloquent JavaScript", "url": "https://eloquentjavascript.net/"},
    ],
    "React": [
        {"title": "React Official Docs", "url": "https://react.dev/"},
        {"title": "React Tutorial", "url": "https://react.dev/learn"},
        {"title": "React Patterns", "url": "https://reactpatterns.com/"},
    ],
    "Machine Learning": [
        {
            "title": "Andrew Ng ML Course",
            "url": "https://www.coursera.org/learn/machine-learning",
        },
        {"title": "scikit-learn Docs", "url": "https://scikit-learn.org/stable/"},
        {"title": "Fast.ai", "url": "https://fast.ai/"},
    ],
    "Data Science": [
        {"title": "Kaggle Learn", "url": "https://www.kaggle.com/learn"},
        {"title": "Pandas Docs", "url": "https://pandas.pydata.org/docs/"},
        {"title": "DataCamp", "url": "https://www.datacamp.com/"},
    ],
}


def _generate_cache_key(
    skill: str, role: str, days: int, hours: float, pace: str
) -> str:
    key_str = f"{skill}|{role}|{days}|{hours}|{pace}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _build_roadmap_prompt(
    skill: str,
    role: str,
    days: int,
    hours: float,
    pace: str,
    roadmap_results: List[Dict],
    web_results: List[Dict],
    youtube_results: List[Dict],
) -> str:
    """Build RAG prompt with fallback to default resources."""

    all_resources = []

    if roadmap_results:
        for r in roadmap_results[:4]:
            all_resources.append(
                {
                    "type": "article",
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                }
            )

    if web_results:
        for r in web_results[:3]:
            all_resources.append(
                {
                    "type": "article",
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                }
            )

    if not all_resources and skill in DEFAULT_ROADMAPS:
        all_resources = DEFAULT_ROADMAPS[skill][:3]

    resources_text = (
        json.dumps(all_resources, indent=2)
        if all_resources
        else "Use official documentation and tutorials."
    )

    yt_text = (
        json.dumps(youtube_results[:2], indent=2)
        if youtube_results
        else "YouTube tutorials available on the topic."
    )

    return f"""You are an expert curriculum designer.

Create a {days}-day learning path for "{skill}" targeting {role} role.

CONTEXT:
- Time available: {days} days, {hours} hours/day
- Learning pace: {pace}
- Target role: {role}

RESOURCES (use these if available):
{resources_text}

VIDEO TUTORIALS:
{yt_text}

Return ONLY valid JSON:
{{
  "summary": "Brief overview",
  "steps": [
    {{
      "day_from": 1,
      "day_to": {min(7, days)},
      "title": "Module name",
      "tasks": ["Task 1", "Task 2", "Task 3"],
      "resources": [{{"type": "article", "title": "Resource", "url": "https://..."}}],
      "project": "Hands-on project"
    }}
  ]
}}

Return ONLY the JSON object, no markdown or explanation."""


def _background_web_search(skill: str, role: str):
    """Background thread to do web searches (non-blocking)."""
    try:
        from .web_search import (
            search_roadmaps,
            search_learning_resources,
            search_youtube_embeds,
        )

        results = {"roadmaps": [], "resources": [], "youtube": []}

        try:
            results["roadmaps"] = search_roadmaps(skill, max_results=5) or []
        except:
            pass

        try:
            results["resources"] = (
                search_learning_resources(skill, role, max_results=3) or []
            )
        except:
            pass

        try:
            results["youtube"] = search_youtube_embeds(skill, role, max_results=2) or []
        except:
            pass

        _WEB_RESULTS[skill] = results
        logger.info(f"Background search completed for {skill}")

    except Exception as e:
        logger.warning(f"Background search failed for {skill}: {e}")
        _WEB_RESULTS[skill] = {"roadmaps": [], "resources": [], "youtube": []}


def generate_ai_learning_path(
    skill: str,
    role: str,
    days: int,
    hours: float,
    pace: str,
    context: str = "",
    requested_provider: Optional[str] = None,
    include_youtube: bool = True,
) -> Dict:
    """
    FAST VERSION: Generate learning path using Groq AI.

    Key optimization: Fire Groq call IMMEDIATELY without waiting for web searches.
    Web searches run in background thread, results cached for next time.

    Speed: ~5-8 seconds (was 40+ seconds)
    """
    cache_key = _generate_cache_key(skill, role, days, hours, pace)
    if cache_key in _AI_CACHE:
        logger.info(f"Using cached learning path for {skill}")
        return _AI_CACHE[cache_key]

    logger.info(f"Generating fast learning path for {skill}...")

    web_results = _WEB_RESULTS.get(
        skill, {"roadmaps": [], "resources": [], "youtube": []}
    )

    prompt = _build_roadmap_prompt(
        skill,
        role,
        days,
        hours,
        pace,
        roadmap_results=web_results.get("roadmaps", []),
        web_results=web_results.get("resources", []),
        youtube_results=web_results.get("youtube", []) if include_youtube else [],
    )

    try:
        from .ai.router import get_ai_response

        logger.info(f"Calling Groq AI for {skill}...")
        raw = get_ai_response(prompt, requested_provider)
        result = _parse_ai_response(raw)

        if result and "steps" in result:
            result["youtube_videos"] = web_results.get("youtube", [])
            result["is_fast_mode"] = True
            _AI_CACHE[cache_key] = result
            logger.info(f"Fast learning path generated for {skill}")
            return result

    except Exception as e:
        logger.error(f"Groq generation failed for {skill}: {e}")

    result = _generate_fallback_learning_path(skill, role, days)
    result["is_fast_mode"] = True
    _AI_CACHE[cache_key] = result
    return result


def _parse_ai_response(response_text: str) -> Optional[Dict]:
    """Parse AI response to JSON."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        logger.error(f"Failed to parse AI response")
        return None


def _generate_fallback_learning_path(skill: str, role: str, days: int) -> Dict:
    """Generate simple fallback path when AI fails."""
    default_resources = DEFAULT_ROADMAPS.get(skill, [])

    if days >= 21:
        phase1 = days // 3
        phase2 = days // 3
        phase3 = days - phase1 - phase2

        return {
            "summary": f"Learn {skill} for {role} - curated curriculum",
            "source_roadmap": "Community resources",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": phase1,
                    "title": f"{skill} Foundations",
                    "tasks": [
                        f"Learn core {skill} concepts",
                        "Complete beginner exercises",
                        "Set up environment",
                    ],
                    "resources": default_resources[:2] if default_resources else [],
                    "project": f"{skill} starter project",
                },
                {
                    "day_from": phase1 + 1,
                    "day_to": phase1 + phase2,
                    "title": f"Intermediate {skill}",
                    "tasks": [
                        f"Practice {skill}",
                        "Build intermediate projects",
                        "Learn best practices",
                    ],
                    "resources": default_resources[2:4]
                    if len(default_resources) > 2
                    else [],
                    "project": f"{skill} practice project",
                },
                {
                    "day_from": phase1 + phase2 + 1,
                    "day_to": days,
                    "title": f"Advanced {skill} & Portfolio",
                    "tasks": [
                        f"Master advanced {skill}",
                        "Build portfolio project",
                        "Prepare for interviews",
                    ],
                    "resources": default_resources[:2] if default_resources else [],
                    "project": f"{skill} portfolio project",
                },
            ],
        }
    else:
        return {
            "summary": f"Learn {skill} for {role}",
            "source_roadmap": "Community curriculum",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": days,
                    "title": f"Learn {skill}",
                    "tasks": [
                        f"Study {skill} fundamentals",
                        f"Complete {skill} tutorials",
                        f"Build practice projects",
                    ],
                    "resources": default_resources[:2] if default_resources else [],
                    "project": f"{skill} practice project",
                }
            ],
        }


def generate_ai_projects(
    skills: List[str],
    role: str,
    project_type: str,
    context: str = "",
    requested_provider: Optional[str] = None,
) -> List[Dict]:
    """Generate project recommendations using AI."""
    cache_key = hashlib.md5(
        f"{','.join(sorted(skills))}|{role}|{project_type}".encode()
    ).hexdigest()

    if cache_key in _AI_CACHE:
        return _AI_CACHE[cache_key]

    prompt = f"""Generate portfolio project ideas for someone targeting {role} with skills: {", ".join(skills)}.

Return ONLY valid JSON array:
[
  {{
    "title": "Project Title",
    "description": "Brief description",
    "skills": ["Skill1", "Skill2"]
  }}
]

Return only the JSON array:"""

    try:
        from .ai.router import get_ai_response

        raw = get_ai_response(prompt, requested_provider)

        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if json_match:
            projects = json.loads(json_match.group(0))
            _AI_CACHE[cache_key] = projects
            return projects
    except Exception as e:
        logger.error(f"Project generation failed: {e}")

    return [
        {
            "title": f"{skill} {project_type.capitalize()} Project",
            "description": f"Build a {project_type} project demonstrating {skill} skills",
            "skills": [skill],
        }
        for skill in skills[:3]
    ]


def prefetch_web_searches(skills: List[str], role: str):
    """
    Prefetch web searches in background for faster next-time responses.
    Call this after generating paths to warm up the cache.
    """
    for skill in skills:
        thread = threading.Thread(
            target=_background_web_search, args=(skill, role), daemon=True
        )
        thread.start()
