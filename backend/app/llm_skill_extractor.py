# backend/app/llm_skill_extractor.py
"""
LLM-Based Skill Extractor - Fast, reliable skill extraction using Groq/Gemini.

Replaces unreliable web scraping with AI-powered skill extraction.
Speed: 3-5 seconds per role.
"""

import json
import logging
import hashlib
from typing import List, Tuple, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

_SKILL_CACHE = {}


def _get_skill_extraction_prompt(role: str, top_n: int = 15) -> str:
    """Build the prompt for skill extraction."""
    return f"""You are an expert technical recruiter and career advisor.

List the {top_n} most important and in-demand technical skills for a "{role}" role in 2026.

Consider:
- Programming languages
- Frameworks and libraries
- Tools and platforms
- Cloud services
- Soft skills that matter

Return ONLY a valid JSON array with skill names (exact format, no explanation):
["Skill1", "Skill2", "Skill3", ...]

Examples of good skill names: "Python", "React", "AWS", "Docker", "Git", "SQL", "REST API", "Machine Learning"

Return ONLY the JSON array:"""


def _parse_skill_response(response_text: str, role: str) -> List[str]:
    """Parse LLM response to extract skills list."""
    try:
        skills = json.loads(response_text.strip())
        if isinstance(skills, list) and len(skills) > 0:
            cleaned = []
            for s in skills:
                if isinstance(s, str) and len(s.strip()) > 0:
                    cleaned.append(s.strip())
            return cleaned
    except json.JSONDecodeError:
        pass

    import re

    json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if json_match:
        try:
            skills = json.loads(json_match.group(0))
            if isinstance(skills, list) and len(skills) > 0:
                cleaned = []
                for s in skills:
                    if isinstance(s, str) and len(s.strip()) > 0:
                        cleaned.append(s.strip())
                return cleaned
        except:
            pass

    logger.warning(f"Failed to parse skill response for {role}")
    return []


def _call_llm(prompt: str) -> Optional[str]:
    """Call LLM via router."""
    try:
        from .ai.router import get_ai_response

        response = get_ai_response(prompt, is_json=False)
        if response and len(response) > 10:
            return response
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
    return None


@lru_cache(maxsize=100)
def extract_skills_with_llm(role: str, top_n: int = 15) -> Tuple[List[str], str]:
    """
    Extract skills for a role using LLM.

    Args:
        role: Target job role (e.g., "Software Engineer")
        top_n: Number of top skills to return

    Returns:
        Tuple of (skills_list, source)
    """
    cache_key = f"{role.lower().strip()}:{top_n}"
    if cache_key in _SKILL_CACHE:
        logger.info(f"Using cached LLM skills for: {role}")
        return _SKILL_CACHE[cache_key]

    logger.info(f"Extracting skills for role: {role} via LLM")

    prompt = _get_skill_extraction_prompt(role, top_n)
    response = _call_llm(prompt)

    if response:
        skills = _parse_skill_response(response, role)
        if skills:
            _SKILL_CACHE[cache_key] = (skills[:top_n], "llm")
            logger.info(f"LLM extracted {len(skills)} skills for {role}")
            return (skills[:top_n], "llm")

    logger.warning(f"LLM extraction failed for {role}, using fallback")
    return ([], "failed")


def clear_cache():
    """Clear the skill cache."""
    _SKILL_CACHE.clear()
    extract_skills_with_llm.cache_clear()
