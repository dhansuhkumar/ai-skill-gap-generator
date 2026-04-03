# backend/app/learning_path_ai.py
"""
AI-Powered Learning Path Generator with RAG (Retrieval-Augmented Generation).
Uses DuckDuckGo web search + Groq (LLaMA 3) for structured learning paths.
Parallelizes web searches for speed.
"""

import json
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logger = logging.getLogger(__name__)

_AI_CACHE = {}

MAX_WORKERS = 3


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
    """Build a RAG prompt that prioritizes real-world roadmaps."""

    roadmap_text = (
        json.dumps(roadmap_results[:6], indent=2)
        if roadmap_results
        else "No roadmap results found."
    )
    web_text = (
        json.dumps(web_results[:4], indent=2)
        if web_results
        else "No additional web results."
    )
    yt_text = (
        json.dumps(youtube_results[:3], indent=2)
        if youtube_results
        else "No YouTube results."
    )

    return f"""You are an expert at parsing open-source curricula and community roadmaps.

TASK: Build a learning path for "{skill}" targeting {role} role using ONLY the provided real-world sources below.

═══════════════════════════════════════════════════════════════════
REAL-WORLD ROADMAPS & CURRICULA (PRIMARY SOURCE - USE THESE):
═══════════════════════════════════════════════════════════════════
{roadmap_text}

═══════════════════════════════════════════════════════════════════
ADDITIONAL RESOURCES (USE FOR EXAMPLES AND EXERCISES):
═══════════════════════════════════════════════════════════════════
{web_text}

═══════════════════════════════════════════════════════════════════
VIDEO TUTORIALS:
═══════════════════════════════════════════════════════════════════
{yt_text}

═══════════════════════════════════════════════════════════════════
INSTRUCTIONS:
═══════════════════════════════════════════════════════════════════
1. Extract modules and milestones from the roadmaps above - do NOT invent your own steps
2. Structure by "Milestones" or "Modules" found in the real roadmaps
3. Each step MUST include a source_url linking to the original roadmap/resource it was derived from
4. Map the roadmap modules to the {days}-day timeframe ({hours}h/day, {pace} pace)
5. Include hands-on projects that mirror real-world curriculum exercises

Return JSON with this exact structure:
{{
  "summary": "Brief overview referencing the community roadmap source",
  "source_roadmap": "URL of primary roadmap used (or 'compiled from multiple sources')",
  "steps": [
    {{
      "day_from": 1,
      "day_to": 7,
      "title": "Module name from roadmap (e.g., 'JavaScript Fundamentals')",
      "tasks": ["Specific task 1", "Specific task 2", "Specific task 3"],
      "resources": [
        {{"type": "article", "title": "Resource title", "url": "https://..."}},
        {{"type": "video", "title": "Video title", "url": "https://youtube.com/...", "video_id": "abc123", "embed_url": "https://..."}}
      ],
      "project": "Hands-on project from real curriculum",
      "source_url": "URL of roadmap this step came from"
    }}
  ]
}}

IMPORTANT: 
- Return ONLY valid JSON, no markdown or explanation
- Every step MUST have a source_url
- Match real curriculum sequence, not arbitrary day divisions"""


def _parallel_search_roadmaps(skill: str) -> List[Dict]:
    """Search for roadmaps."""
    try:
        from .web_search import search_roadmaps

        return search_roadmaps(skill, max_results=8)
    except Exception as e:
        logger.error(f"Roadmap search failed: {e}")
        return []


def _parallel_search_resources(skill: str, role: str) -> List[Dict]:
    """Search for learning resources."""
    try:
        from .web_search import search_learning_resources

        return search_learning_resources(skill, role, max_results=5)
    except Exception as e:
        logger.error(f"Resource search failed: {e}")
        return []


def _parallel_search_youtube(skill: str, role: str) -> List[Dict]:
    """Search for YouTube videos."""
    try:
        from .web_search import search_youtube_embeds

        return search_youtube_embeds(skill, role, max_results=3)
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        return []


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
    Generate a learning path using RAG: parallel web search + Groq synthesis.
    """
    cache_key = _generate_cache_key(skill, role, days, hours, pace)
    if cache_key in _AI_CACHE:
        logger.info(f"Using cached learning path for {skill}")
        return _AI_CACHE[cache_key]

    roadmap_results = []
    web_results = []
    youtube_results = []

    try:
        logger.info(f"Phase 1: Parallel web searches for {skill}...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_roadmaps = executor.submit(_parallel_search_roadmaps, skill)
            future_resources = executor.submit(_parallel_search_resources, skill, role)
            future_youtube = executor.submit(_parallel_search_youtube, skill, role)

            roadmap_results = future_roadmaps.result()
            logger.info(f"Found {len(roadmap_results)} roadmap sources")

            web_results = future_resources.result()
            logger.info(f"Found {len(web_results)} web resources")

            if include_youtube:
                youtube_results = future_youtube.result()
                logger.info(f"Found {len(youtube_results)} YouTube videos")

    except Exception as e:
        logger.error(f"Parallel web search failed for {skill}: {e}")

    prompt = _build_roadmap_prompt(
        skill, role, days, hours, pace, roadmap_results, web_results, youtube_results
    )

    try:
        from .ai.router import get_ai_response

        logger.info(f"Phase 2: Extracting curriculum from real roadmaps...")
        raw = get_ai_response(prompt, requested_provider)
        result = _parse_ai_response(raw)

        if result and "steps" in result:
            result["youtube_videos"] = youtube_results
            result["source_roadmap"] = result.get("source_roadmap", "Community roadmap")
            result["is_rag_based"] = len(roadmap_results) > 0
            _AI_CACHE[cache_key] = result
            logger.info(f"RAG-based learning path generated for {skill}")
            return result
    except Exception as e:
        logger.error(f"Groq generation failed for {skill}: {e}")

    result = _generate_fallback_learning_path(skill, role, days, roadmap_results)
    result["youtube_videos"] = youtube_results
    result["is_rag_based"] = False
    _AI_CACHE[cache_key] = result
    return result


def _parse_ai_response(response_text: str) -> Optional[Dict]:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        import re

        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        logger.error(f"Failed to parse AI response: {response_text[:200]}")
        return None


def _generate_fallback_learning_path(
    skill: str, role: str, days: int, roadmap_results: List[Dict] = None
) -> Dict:
    """Generate fallback path, preferring to use real roadmap data if available."""

    if roadmap_results:
        primary_source = roadmap_results[0].get("url", "") if roadmap_results else ""
        return {
            "summary": f"Learn {skill} for {role} in {days} days - curated from community roadmaps",
            "source_roadmap": primary_source or "Compiled from community sources",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": min(days, 7),
                    "title": f"{skill} Foundations",
                    "tasks": [
                        f"Review {skill} core concepts",
                        f"Complete introductory exercises",
                        f"Set up development environment",
                    ],
                    "resources": [
                        {
                            "type": "article",
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                        }
                        for r in roadmap_results[:3]
                    ]
                    if roadmap_results
                    else [],
                    "project": f"Build a simple {skill} application",
                    "source_url": primary_source,
                },
                {
                    "day_from": min(days, 8),
                    "day_to": min(days, 14),
                    "title": f"{skill} Core Skills",
                    "tasks": [
                        f"Practice {skill} fundamentals",
                        f"Work through intermediate tutorials",
                        f"Build small projects",
                    ],
                    "resources": [],
                    "project": f"{skill} practice project",
                    "source_url": primary_source,
                },
                {
                    "day_from": min(days, 15),
                    "day_to": days,
                    "title": f"{skill} Advanced & Portfolio",
                    "tasks": [
                        f"Master advanced {skill} topics",
                        f"Build a portfolio project",
                        f"Review and refine code",
                    ],
                    "resources": [
                        {
                            "type": "article",
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                        }
                        for r in roadmap_results[3:6]
                    ]
                    if len(roadmap_results) > 3
                    else [],
                    "project": f"Complete {skill} portfolio project",
                    "source_url": primary_source,
                },
            ],
        }

    if days >= 21:
        phase1_days = days // 3
        phase2_days = days // 3
        phase3_days = days - phase1_days - phase2_days
        return {
            "summary": f"Master {skill} for {role} in {days} days",
            "source_roadmap": "Community-curated curriculum",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": phase1_days,
                    "title": f"{skill} Fundamentals",
                    "tasks": [
                        f"Learn core {skill} concepts",
                        f"Complete beginner tutorials",
                        f"Practice basic {skill} exercises",
                    ],
                    "resources": [],
                    "project": f"Simple {skill} starter project",
                    "source_url": "",
                },
                {
                    "day_from": phase1_days + 1,
                    "day_to": phase1_days + phase2_days,
                    "title": f"Intermediate {skill}",
                    "tasks": [
                        f"Build practical {skill} projects",
                        f"Learn advanced {skill} features",
                        f"Study best practices",
                    ],
                    "resources": [],
                    "project": f"{skill} intermediate project for {role}",
                    "source_url": "",
                },
                {
                    "day_from": phase1_days + phase2_days + 1,
                    "day_to": days,
                    "title": f"Advanced {skill} & Integration",
                    "tasks": [
                        f"Master advanced {skill} concepts",
                        f"Integrate {skill} with other technologies",
                        f"Build portfolio project",
                    ],
                    "resources": [],
                    "project": f"Complete {skill} portfolio project",
                    "source_url": "",
                },
            ],
        }
    else:
        return {
            "summary": f"Learn {skill} for {role} in {days} days",
            "source_roadmap": "Community-curated curriculum",
            "steps": [
                {
                    "day_from": 1,
                    "day_to": days,
                    "title": f"Learn {skill}",
                    "tasks": [
                        f"Study {skill} fundamentals",
                        f"Complete {skill} tutorials",
                        f"Build a small {skill} project",
                    ],
                    "resources": [],
                    "project": f"{skill} practice project",
                    "source_url": "",
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

    prompt = f"""Generate {project_type} project ideas for someone targeting {role} role with skills: {", ".join(skills)}.

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

    return _generate_fallback_projects(skills, role, project_type)


import re


def _generate_fallback_projects(
    skills: List[str], role: str, project_type: str
) -> List[Dict]:
    projects = []
    for skill in skills[:3]:
        projects.append(
            {
                "title": f"{skill} {project_type.capitalize()} Project",
                "description": f"Build a {project_type} project demonstrating {skill} skills for {role} position",
                "skills": [skill],
            }
        )
    if len(skills) > 1:
        projects.append(
            {
                "title": f"{role} Capstone Project",
                "description": f"Comprehensive {project_type} project combining {', '.join(skills)} for {role}",
                "skills": skills,
            }
        )
    return projects
