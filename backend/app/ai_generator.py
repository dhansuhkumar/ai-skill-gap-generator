# backend/app/ai_generator.py
import os
import json
import hashlib
import logging
import threading
import time
from typing import List
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from backend.app.ai import router as ai_router

logger = logging.getLogger(__name__)
if not logger.handlers:
    # Basic logging configuration for module-level messages
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Circuit breaker flag and simple in-memory cache (thread-safe)
_LOCK = threading.Lock()
AI_AVAILABLE = True
AI_CACHE = {}  # key -> (timestamp, data)
# Last source used for observability (set per call)
LAST_AI_SOURCE = None
# Cache size management
_MAX_CACHE_SIZE = 1000  # Maximum number of cache entries
# Cache TTL in seconds (24 hours)
_CACHE_TTL = 86400

# Router handles provider clients and configuration (genai/openai)

# Load skill data for heuristic fallbacks
_SKILL_DATA = {}
try:
    skill_data_path = Path(__file__).parent / "skill_data.json"
    with open(skill_data_path, 'r', encoding='utf-8') as f:
        _SKILL_DATA = json.load(f)
except Exception as e:
    logger.warning("Failed to load skill_data.json: %s", e)


def _cache_key(role: str, skills: List[str], version: str = "v1") -> str:
    key = f"{version}|{(role or '')}|{','.join(sorted([str(s).strip() for s in (skills or []) if s]))}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _get_from_cache(cache_key):
    """Get data from cache if not expired, else None."""
    global AI_CACHE
    if cache_key in AI_CACHE:
        timestamp, data = AI_CACHE[cache_key]
        if time.time() - timestamp < _CACHE_TTL:
            return data
        else:
            del AI_CACHE[cache_key]  # Remove expired entry
    return None


def _set_cache(cache_key, data):
    """Set data in cache with current timestamp."""
    global AI_CACHE
    AI_CACHE[cache_key] = (time.time(), data)


def _manage_cache_size():
    """Manage cache size by removing oldest entries if cache exceeds max size."""
    global AI_CACHE
    if len(AI_CACHE) > _MAX_CACHE_SIZE:
        # Sort by timestamp (oldest first) and remove oldest entries
        sorted_entries = sorted(AI_CACHE.items(), key=lambda x: x[1][0])
        items_to_remove = len(AI_CACHE) - _MAX_CACHE_SIZE + int(_MAX_CACHE_SIZE * 0.1)
        keys_to_remove = [key for key, _ in sorted_entries[:items_to_remove]]
        for key in keys_to_remove:
            del AI_CACHE[key]
        logger.info("Cache size managed: removed %d entries, current size: %d", len(keys_to_remove), len(AI_CACHE))


def _strip_markdown(text: str) -> str:
    if not isinstance(text, str):
        return text
    t = text.strip()
    # Remove triple-backtick fences if any
    if t.startswith("```") and t.endswith("```"):
        parts = t.split("\n")
        if parts and parts[0].startswith("```"):
            parts = parts[1:]
        if parts and parts[-1].strip().endswith("```"):
            parts = parts[:-1]
        t = "\n".join(parts).strip()
    # Remove surrounding single backticks
    t = t.strip('`')
    return t


def _extract_json_like(text: str):
    """Try to extract a JSON object or array substring from text.

    Returns the JSON string or raises ValueError.
    """
    if not isinstance(text, str):
        raise ValueError("No text to parse")
    s = text.strip()
    # find first { or [ and matching closing
    first_obj = min([idx for idx in [s.find('{'), s.find('[')] if idx != -1], default=-1)
    if first_obj == -1:
        raise ValueError("No JSON start found")
    # Choose whether object or array
    open_ch = s[first_obj]
    close_ch = '}' if open_ch == '{' else ']'
    depth = 0
    for i in range(first_obj, len(s)):
        if s[i] == open_ch:
            depth += 1
        elif s[i] == close_ch:
            depth -= 1
            if depth == 0:
                return s[first_obj:i+1]
    raise ValueError("No matching JSON end found")


def _get_heuristic_project_ideas(role: str, skills: List[str]) -> List[str]:
    """Generate project ideas using skill relationships from skill_data.json."""
    if not _SKILL_DATA:
        return [
            "Build a Portfolio Website with Dark Mode",
            "Create a Task Tracker using LocalStorage",
            "Design a Weather Dashboard using Public APIs",
        ]

    # Normalize skills to lowercase for matching
    user_skills = set(str(s).lower().strip() for s in skills if s)
    related_skills = set()

    # Find related skills from user's skills
    for skill in user_skills:
        if skill in _SKILL_DATA:
            skill_info = _SKILL_DATA[skill]
            related_skills.update(str(r).lower() for r in skill_info.get("related", []))
            related_skills.update(str(d).lower() for d in skill_info.get("dependencies", []))

    # Remove skills user already has
    related_skills -= user_skills

    # Generate project ideas based on role and available skills
    projects = []
    role_lower = role.lower()

    if "frontend" in role_lower or "web" in role_lower:
        if "react" in user_skills or "javascript" in user_skills:
            projects.append("Build a React Component Library")
        if "css" in user_skills:
            projects.append("Create a Responsive CSS Framework")
        if "html" in user_skills:
            projects.append("Design an Interactive Web Portfolio")

    elif "backend" in role_lower or "python" in role_lower:
        if "python" in user_skills:
            projects.append("Build a REST API with Flask")
        if "django" in user_skills:
            projects.append("Create a Blog Application with Django")
        if "database" in related_skills or "sql" in related_skills:
            projects.append("Design a Database Schema for E-commerce")

    elif "data" in role_lower or "machine learning" in role_lower:
        if "python" in user_skills:
            projects.append("Build a Data Visualization Dashboard")
        if "pandas" in related_skills:
            projects.append("Create a Data Analysis Tool")
        if "machine learning" in user_skills:
            projects.append("Develop a Predictive Model")

    # Fallback projects if no specific matches
    if len(projects) < 3:
        fallback_projects = [
            "Build a Task Management Application",
            "Create a Personal Finance Tracker",
            "Design a Recipe Management System",
            "Develop a Social Media Dashboard",
            "Build a File Organization Tool"
        ]
        projects.extend(fallback_projects[:3 - len(projects)])

    return projects[:3]


def _get_heuristic_learning_paths(skills: List[str]) -> dict:
    """Generate learning paths using skill relationships."""
    if not _SKILL_DATA:
        # Basic fallback
        return {skill: {
            "summary": f"Learn core concepts of {skill} and build a small project.",
            "steps": [
                {"day_from": 1, "day_to": 3, "title": f"Introduction to {skill}", "tasks": [f"Follow introductory tutorial for {skill}"], "project": f"Build a simple {skill} project", "resources": ["Official documentation"]},
                {"day_from": 4, "day_to": 7, "title": f"Advanced {skill} Concepts", "tasks": [f"Practice advanced features of {skill}"], "project": f"Enhance the {skill} project", "resources": ["Online courses"]},
                {"day_from": 8, "day_to": 10, "title": f"{skill} Best Practices", "tasks": [f"Learn best practices and testing"], "project": f"Add tests to {skill} project", "resources": ["Community forums"]}
            ]
        } for skill in skills}

    result = {}
    for skill in skills:
        skill_lower = skill.lower().strip()
        skill_info = _SKILL_DATA.get(skill_lower, {})

        # Build learning path based on dependencies
        dependencies = skill_info.get("dependencies", [])
        related = skill_info.get("related", [])

        steps = []
        day_counter = 1

        # Step 1: Learn prerequisites
        if dependencies:
            steps.append({
                "day_from": day_counter,
                "day_to": day_counter + 2,
                "title": f"Learn Prerequisites: {', '.join(dependencies)}",
                "tasks": [f"Study {dep} fundamentals" for dep in dependencies],
                "project": f"Build a simple {dependencies[0] if dependencies else skill} application",
                "resources": ["Official documentation", "Online tutorials"]
            })
            day_counter += 3

        # Step 2: Core skill learning
        steps.append({
            "day_from": day_counter,
            "day_to": day_counter + 3,
            "title": f"Master {skill} Fundamentals",
            "tasks": [f"Complete {skill} tutorials", f"Practice basic {skill} concepts"],
            "project": f"Create a basic {skill} project",
            "resources": ["Official docs", "Interactive platforms"]
        })
        day_counter += 4

        # Step 3: Advanced topics and related skills
        if related:
            steps.append({
                "day_from": day_counter,
                "day_to": day_counter + 2,
                "title": f"Explore Related Skills: {', '.join(related[:2])}",
                "tasks": [f"Learn integration with {rel}" for rel in related[:2]],
                "project": f"Build a project combining {skill} with {related[0] if related else 'related tech'}",
                "resources": ["Integration guides", "Community examples"]
            })

        summary = f"Comprehensive learning path for {skill} including prerequisites and related technologies."

        result[skill] = {
            "summary": summary,
            "steps": steps
        }

    return result


def _get_heuristic_unified_analysis(user_skills: List[str], target_role: str) -> dict:
    """Generate unified analysis using skill relationships."""
    if not _SKILL_DATA:
        return {
            "schema_version": "v1",
            "candidate_required_skills": ["JavaScript", "Python", "SQL", "Git", "Problem Solving"],
            "candidate_missing_skills": ["JavaScript", "SQL"],
            "suggested_focus_skills": ["JavaScript", "SQL"],
            "job_matches": [
                {"role": "Software Developer", "match_percent": 65},
                {"role": "Web Developer", "match_percent": 70},
                {"role": "Data Analyst", "match_percent": 60}
            ],
            "ai_projects_sample": [
                {"title": "Build a Web Application", "short": "Create a full-stack web app"},
                {"title": "Data Analysis Tool", "short": "Build a tool for data processing"},
                {"title": "API Development", "short": "Develop RESTful APIs"}
            ]
        }

    # Normalize user skills
    user_skills_set = set(str(s).lower().strip() for s in user_skills if s)

    # Determine required skills based on role
    role_lower = target_role.lower()
    required_skills = []

    if "frontend" in role_lower or "web" in role_lower:
        required_skills = ["HTML", "CSS", "JavaScript", "React", "Responsive Design"]
    elif "backend" in role_lower:
        required_skills = ["Python", "Java", "Node.js", "SQL", "REST APIs"]
    elif "data" in role_lower or "analyst" in role_lower:
        required_skills = ["Python", "SQL", "Pandas", "Statistics", "Data Visualization"]
    elif "machine learning" in role_lower or "ml" in role_lower:
        required_skills = ["Python", "Machine Learning", "TensorFlow", "Statistics", "Pandas"]
    elif "fullstack" in role_lower or "full-stack" in role_lower:
        required_skills = ["HTML", "CSS", "JavaScript", "Python", "SQL", "React", "Node.js"]
    else:
        # Generic developer skills
        required_skills = ["Python", "JavaScript", "SQL", "Git", "Problem Solving"]

    # Add related skills to make it more comprehensive
    expanded_required = set(required_skills)
    for skill in required_skills:
        skill_lower = skill.lower()
        if skill_lower in _SKILL_DATA:
            skill_info = _SKILL_DATA[skill_lower]
            expanded_required.update(skill_info.get("related", []))
            expanded_required.update(skill_info.get("dependencies", []))

    required_skills = list(expanded_required)[:20]  # Max 20

    # Calculate missing skills
    missing_skills = [skill for skill in required_skills if skill.lower() not in user_skills_set]

    # Suggest focus skills (top missing skills by importance)
    suggested_focus = missing_skills[:5]

    # Generate job matches based on skill overlap
    base_match = len(user_skills_set & set(s.lower() for s in required_skills)) / len(required_skills) * 100
    job_matches = [
        {"role": f"{target_role} Specialist", "match_percent": min(100, int(base_match + 10))},
        {"role": f"Senior {target_role}", "match_percent": min(100, int(base_match - 5))},
        {"role": f"Junior {target_role}", "match_percent": min(100, int(base_match + 15))},
        {"role": f"{target_role} Intern", "match_percent": min(100, int(base_match + 20))}
    ]

    # Generate project ideas
    projects = _get_heuristic_project_ideas(target_role, user_skills)
    ai_projects_sample = [
        {"title": project, "short": f"Hands-on project to practice {target_role.lower()} skills"}
        for project in projects
    ]

    return {
        "schema_version": "v1",
        "candidate_required_skills": required_skills,
        "candidate_missing_skills": missing_skills,
        "suggested_focus_skills": suggested_focus,
        "job_matches": job_matches,
        "ai_projects_sample": ai_projects_sample
    }


def generate_ai_project_ideas(role, skills):
    """
    Generate project ideas using AI → Cache → Heuristic → Static hierarchy.
    Returns list[str] of 3 project titles.
    """
    global AI_AVAILABLE, AI_CACHE, LAST_AI_SOURCE

    # Input validation
    if not isinstance(role, str) or not role.strip():
        logger.warning("Invalid role provided to generate_ai_project_ideas")
        return [
            "Build a Portfolio Website with Dark Mode",
            "Create a Task Tracker using LocalStorage",
            "Design a Weather Dashboard using Public APIs",
        ]

    if not isinstance(skills, list):
        skills = []

    cache_key = _cache_key(f"{role}|project_ideas", skills)
    with _LOCK:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            LAST_AI_SOURCE = "cache"
            return cached

    # Try AI first
    if AI_AVAILABLE:
        try:
            prompt = (
                "Return EXACTLY 3 short project titles (strings) as a JSON array."
                " No markdown, no explanation. JSON ONLY."
                f" Target role: {role}. Current skills: {', '.join(skills) if skills else 'None'}."
            )

            if len(prompt) > 100000:
                logger.warning("Prompt too long in generate_ai_project_ideas: %d characters", len(prompt))
            else:
                raw = ai_router.get_ai_response(prompt)
                if raw and isinstance(raw, str):
                    raw = _strip_markdown(raw)
                    if raw.strip():
                        try:
                            json_str = _extract_json_like(raw)
                            if json_str:
                                arr = json.loads(json_str)
                                if isinstance(arr, list):
                                    titles = []
                                    for x in arr:
                                        if isinstance(x, str) and str(x).strip():
                                            titles.append(str(x).strip())
                                        if len(titles) >= 3:
                                            break
                                    if len(titles) == 3:
                                        provider_used = ai_router.get_last_successful_provider() or "ai"
                                        with _LOCK:
                                            _set_cache(cache_key, titles)
                                            LAST_AI_SOURCE = provider_used
                                            _manage_cache_size()
                                        return titles
                        except Exception as e:
                            logger.warning("JSON parsing failed in generate_ai_project_ideas: %s", e)
        except Exception as e:
            logger.warning("AI failed in generate_ai_project_ideas: %s", e)

    # Try heuristic fallback
    try:
        heuristic_result = _get_heuristic_project_ideas(role, skills)
        if heuristic_result and len(heuristic_result) >= 3:
            with _LOCK:
                _set_cache(cache_key, heuristic_result)
                LAST_AI_SOURCE = "heuristic"
                _manage_cache_size()
            return heuristic_result
    except Exception as e:
        logger.warning("Heuristic fallback failed in generate_ai_project_ideas: %s", e)

    # Static fallback
    static_result = [
        "Build a Portfolio Website with Dark Mode",
        "Create a Task Tracker using LocalStorage",
        "Design a Weather Dashboard using Public APIs",
    ]

    with _LOCK:
        _set_cache(cache_key, static_result)
        LAST_AI_SOURCE = "static"
        _manage_cache_size()
    return static_result


def generate_learning_path_for_skill(skill: str):
    # Single-skill helper that uses the batched `get_learning_paths_for_skills`
    # to avoid calling Gemini per-skill. If AI is unavailable, return fallback.
    fallback = {
        "summary": f"Learn core concepts of {skill} and build a small project.",
        "steps": [
            f"Follow an introductory tutorial for {skill}",
            f"Build a tiny project using {skill}",
            "Refine by adding tests and reading official docs",
        ],
    }

    if not skill:
        return {"summary": "", "steps": []}

    try:
        # Use centralized batched call for a single skill to respect single-entrypoint
        res = get_learning_paths_for_skills([skill])
        if isinstance(res, dict) and skill in res:
            return res.get(skill) or fallback
        return fallback
    except Exception:
        return fallback


def get_learning_paths_for_skills(skills: list):
    """
    Batch-generate learning paths for a list of skills using AI → Cache → Heuristic → Static hierarchy.
    Returns a dict mapping skill -> {summary, steps}.
    """
    global AI_AVAILABLE, AI_CACHE, LAST_AI_SOURCE

    # Input validation
    if not isinstance(skills, list):
        skills = []
    skills = [str(s).strip() for s in skills if s and isinstance(s, (str, int, float))]
    if not skills:
        return {}

    cache_key = _cache_key("learning_paths", skills + ["v1"])
    with _LOCK:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            LAST_AI_SOURCE = "cache"
            return cached

    # Limit skills to top 10 for token efficiency
    limited_skills = skills[:10]
    skills_json = json.dumps(limited_skills)

    # Try AI first
    if AI_AVAILABLE:
        try:
            prompt = f"Return JSON: {{skill: {{summary: str, steps: [{{day_from:int, day_to:int, title:str, tasks:[str], project:str, resources:[str]}} exactly 3 per skill]}}}} for skills {skills_json}. Output JSON only."

            if len(prompt) > 100000:
                logger.warning("Prompt too long in get_learning_paths_for_skills: %d characters", len(prompt))
            else:
                raw = ai_router.get_ai_response(prompt)
                if raw and isinstance(raw, str):
                    raw = _strip_markdown(raw)
                    if raw.strip():
                        json_str = _extract_json_like(raw)
                        if json_str:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict):
                                # Validate and clean the response
                                out = {}
                                for sk in skills:
                                    val = parsed.get(sk)
                                    if isinstance(val, dict):
                                        summary = val.get("summary") or ""
                                        steps = val.get("steps") or []
                                        cleaned_steps = []
                                        if isinstance(steps, list):
                                            for st in steps:
                                                if isinstance(st, dict):
                                                    try:
                                                        day_from = int(st.get("day_from") or 0)
                                                        day_to = int(st.get("day_to") or day_from)
                                                        title = str(st.get("title") or "").strip()
                                                        tasks = [str(t).strip() for t in (st.get("tasks") or []) if str(t).strip()]
                                                        project = str(st.get("project") or "").strip()
                                                        resources = [str(r).strip() for r in (st.get("resources") or []) if str(r).strip()]
                                                        cleaned_steps.append({"day_from": day_from, "day_to": day_to, "title": title, "tasks": tasks, "project": project, "resources": resources})
                                                    except (ValueError, TypeError) as e:
                                                        logger.warning("Skipping invalid step in learning path for %s: %s", sk, e)
                                                        continue
                                        out[sk] = {"summary": str(summary).strip(), "steps": cleaned_steps}

                                if out:  # Only cache if we got valid results
                                    provider_used = ai_router.get_last_successful_provider() or "ai"
                                    with _LOCK:
                                        _set_cache(cache_key, out)
                                        LAST_AI_SOURCE = provider_used
                                        _manage_cache_size()
                                    return out
        except Exception as e:
            logger.warning("AI failed in get_learning_paths_for_skills: %s", e)

    # Try heuristic fallback
    try:
        heuristic_result = _get_heuristic_learning_paths(skills)
        if heuristic_result:
            with _LOCK:
                _set_cache(cache_key, heuristic_result)
                LAST_AI_SOURCE = "heuristic"
                _manage_cache_size()
            return heuristic_result
    except Exception as e:
        logger.warning("Heuristic fallback failed in get_learning_paths_for_skills: %s", e)

    # Static fallback
    static_result = {}
    for skill in skills:
        static_result[skill] = {
            "summary": f"Learn core concepts of {skill} and build a small project.",
            "steps": [
                {"day_from": 1, "day_to": 3, "title": f"Introduction to {skill}", "tasks": [f"Follow introductory tutorial for {skill}"], "project": f"Build a simple {skill} project", "resources": ["Official documentation"]},
                {"day_from": 4, "day_to": 7, "title": f"Advanced {skill} Concepts", "tasks": [f"Practice advanced features of {skill}"], "project": f"Enhance the {skill} project", "resources": ["Online courses"]},
                {"day_from": 8, "day_to": 10, "title": f"{skill} Best Practices", "tasks": [f"Learn best practices and testing"], "project": f"Add tests to {skill} project", "resources": ["Community forums"]}
            ]
        }

    with _LOCK:
        _set_cache(cache_key, static_result)
        LAST_AI_SOURCE = "static"
        _manage_cache_size()
    return static_result


def get_unified_analysis(user_skills, target_role, requested_provider: str = None):
    """
    Generate unified analysis using AI → Cache → Heuristic → Static hierarchy.
    Returns a validated JSON object matching the task schema.
    """
    global AI_AVAILABLE, AI_CACHE, LAST_AI_SOURCE

    # Input validation
    if not isinstance(user_skills, list):
        user_skills = []
    user_skills = [str(s).strip() for s in user_skills if s and isinstance(s, (str, int, float))]
    target_role = str(target_role or "").strip()

    # Limit skills to top 10 for token efficiency
    limited_user_skills = user_skills[:10]

    cache_key = _cache_key(f"{target_role}|unified", limited_user_skills)
    with _LOCK:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            LAST_AI_SOURCE = "cache"
            return cached

    # Try AI first
    if AI_AVAILABLE:
        try:
            user_skills_list = json.dumps(limited_user_skills)
            prompt = f"Return JSON: {{schema_version:v1, candidate_required_skills:[str], candidate_missing_skills:[str], suggested_focus_skills:[str], job_matches:[{{role:str, match_percent:int}} exactly 3], ai_projects_sample:[{{title:str, short:str}} exactly 3]}} for role {target_role} and skills {user_skills_list}. Output JSON only."

            if len(prompt) > 100000:
                logger.warning("Prompt too long in get_unified_analysis: %d characters", len(prompt))
            else:
                raw = ai_router.get_ai_response(prompt, requested_provider)
                if raw and isinstance(raw, str):
                    raw = _strip_markdown(raw)
                    if raw.strip():
                        json_str = _extract_json_like(raw)
                        if json_str:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict) and parsed:
                                # Basic validation and normalization
                                result = {
                                    "schema_version": parsed.get("schema_version") or "v1",
                                    "candidate_required_skills": [str(s).strip() for s in (parsed.get("candidate_required_skills") or [])][:20],
                                    "candidate_missing_skills": [str(s).strip() for s in (parsed.get("candidate_missing_skills") or [])],
                                    "suggested_focus_skills": [str(s).strip() for s in (parsed.get("suggested_focus_skills") or [])][:5],
                                    "job_matches": parsed.get("job_matches") or [],
                                    "ai_projects_sample": parsed.get("ai_projects_sample") or [],
                                }

                                if result["candidate_required_skills"] or result["job_matches"] or result["ai_projects_sample"]:  # Only cache if we got meaningful results
                                    provider_used = ai_router.get_last_successful_provider() or "ai"
                                    with _LOCK:
                                        _set_cache(cache_key, result)
                                        LAST_AI_SOURCE = provider_used
                                        _manage_cache_size()
                                    return result
        except Exception as e:
            logger.warning("AI failed in get_unified_analysis: %s", e)

    # Try heuristic fallback
    try:
        heuristic_result = _get_heuristic_unified_analysis(user_skills, target_role)
        if heuristic_result:
            with _LOCK:
                _set_cache(cache_key, heuristic_result)
                LAST_AI_SOURCE = "heuristic"
                _manage_cache_size()
            return heuristic_result
    except Exception as e:
        logger.warning("Heuristic fallback failed in get_unified_analysis: %s", e)

    # Static fallback
    static_result = {
        "schema_version": "v1",
        "candidate_required_skills": ["JavaScript", "Python", "SQL", "Git", "Problem Solving"],
        "candidate_missing_skills": ["JavaScript", "SQL"],
        "suggested_focus_skills": ["JavaScript", "SQL"],
        "job_matches": [
            {"role": "Software Developer", "match_percent": 65},
            {"role": "Web Developer", "match_percent": 70},
            {"role": "Data Analyst", "match_percent": 60}
        ],
        "ai_projects_sample": [
            {"title": "Build a Web Application", "short": "Create a full-stack web app"},
            {"title": "Data Analysis Tool", "short": "Build a tool for data processing"},
            {"title": "API Development", "short": "Develop RESTful APIs"}
        ]
    }

    with _LOCK:
        _set_cache(cache_key, static_result)
        LAST_AI_SOURCE = "static"
        _manage_cache_size()
    return static_result
