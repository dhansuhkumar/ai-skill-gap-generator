# backend/app/ai_generator.py
"""
AI Generator - Web-search based skill gap analysis with parallel processing.
All functionality uses web search instead of HuggingFace datasets.
"""

import logging
import time
import hashlib
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .skill_analyzer import analyze_skill_gaps_optimized
from .learning_path_ai import generate_ai_learning_path, generate_ai_projects

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

MAX_PARALLEL_SKILLS = 5

_PLAN_CACHE: dict = {}


def analyze_skill_gaps(
    user_skills: List[str], target_role: str, top_n: int = 10
) -> Dict:
    """
    Web-search-based skill gap analysis.
    Returns TOP N most important missing skills (frequency-based).
    """
    result = analyze_skill_gaps_optimized(user_skills, target_role, top_n=top_n)

    return {
        "required_skills": result["required_skills"],
        "missing_skills": result["missing_skills"],
        "matched_count": result["matched_jobs_count"],
        "source": result["source"],
    }


def _generate_single_skill_path(
    skill: str,
    role: str,
    start_day: int,
    end_day: int,
    hours: float,
    pace: str,
    context: str,
    requested_provider: Optional[str],
) -> tuple:
    """Generate learning path for a single skill. Used for parallel execution."""
    try:
        ai_path = generate_ai_learning_path(
            skill=skill,
            role=role,
            days=end_day - start_day + 1,
            hours=hours,
            pace=pace,
            context=context,
            requested_provider=requested_provider,
        )

        if ai_path and "steps" in ai_path:
            for step in ai_path["steps"]:
                step["day_from"] = step.get("day_from", 1) + start_day - 1
                step["day_to"] = (
                    step.get("day_to", end_day - start_day + 1) + start_day - 1
                )

        logger.info(f"   ✅ Path generated for {skill}")
        return (skill, ai_path)
    except Exception as e:
        logger.error(f"   ❌ Error generating path for {skill}: {e}")
        return (
            skill,
            {
                "summary": f"Learn {skill} for {role}",
                "steps": [
                    {
                        "day_from": start_day,
                        "day_to": end_day,
                        "title": f"Learn {skill}",
                        "tasks": [
                            f"Study {skill} fundamentals",
                            f"Complete {skill} tutorials",
                            f"Build practice projects",
                        ],
                        "project": f"{skill} practice project",
                    }
                ],
            },
        )


def generate_learning_plan(
    selected_skills: List[str],
    role: str,
    days: int = 30,
    hours: float = 1.0,
    project_type: str = "portfolio",
    learning_pace: str = "Balanced",
    time_commitment: str = "1 hour",
    context: str = "",
    requested_provider: Optional[str] = None,
) -> Dict:
    """
    Generate an AI-powered learning plan for selected skills.
    Uses parallel processing for skill path generation.
    """
    logger.info(
        f"🚀 Generating learning plan for {len(selected_skills)} skills over {days} days"
    )
    logger.info(f"   Provider: {requested_provider or 'auto'}, Pace: {learning_pace}")

    sorted_skills = ",".join(sorted(selected_skills))
    cache_key = hashlib.md5(
        f"{sorted_skills}|{role}|{days}|{hours}|{learning_pace}|{project_type}".encode()
    ).hexdigest()

    if cache_key in _PLAN_CACHE:
        logger.info("⚡ Returning cached complete learning plan")
        return _PLAN_CACHE[cache_key]

    days_per_skill = max(3, days // len(selected_skills)) if selected_skills else days

    learning_paths = {}

    logger.info("Phase 1: Parallel skill path generation...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SKILLS) as executor:
        futures = {}
        for i, skill in enumerate(selected_skills):
            start_day = (i * days_per_skill) + 1
            end_day = min((i + 1) * days_per_skill, days)

            future = executor.submit(
                _generate_single_skill_path,
                skill,
                role,
                start_day,
                end_day,
                hours,
                learning_pace,
                context,
                requested_provider,
            )
            futures[future] = skill
            logger.info(f"   Submitted: {skill} (days {start_day}-{end_day})")

        for future in as_completed(futures):
            skill, path = future.result()
            learning_paths[skill] = path

    elapsed = time.time() - start_time
    logger.info(f"   Parallel generation completed in {elapsed:.1f}s")

    logger.info("Phase 2: Generating projects...")
    try:
        projects = generate_ai_projects(
            skills=selected_skills,
            role=role,
            project_type=project_type,
            context=context,
            requested_provider=requested_provider,
        )
        logger.info(f"   ✅ {len(projects)} projects generated")
    except Exception as e:
        logger.error(f"   ❌ Error generating projects: {e}")
        projects = [
            {
                "title": f"{role} Portfolio Project",
                "description": f"Build a comprehensive project using {', '.join(selected_skills)}",
                "skills": selected_skills,
            }
        ]

    matching_score = max(30, min(95, 50 + (len(selected_skills) * 8)))

    logger.info(f"✅ Learning plan complete in {time.time() - start_time:.1f}s")

    result = {
        "learning_paths": learning_paths,
        "projects": projects,
        "matching_score": matching_score,
        "source": requested_provider or "ai_auto",
    }

    _PLAN_CACHE[cache_key] = result
    return result


def generate_chat_response(
    prompt: str, requested_provider: Optional[str] = None
) -> str:
    """Generate chat response using Groq (LLaMA 3)."""
    from .ai.router import get_ai_response

    return get_ai_response(prompt, requested_provider, is_json=False)
