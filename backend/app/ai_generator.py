# backend/app/ai_generator.py
import os
import json
import re
import hashlib
import logging
import threading
import time
from typing import List, Any
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

try:
    from google import genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

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

# Provider availability flags (set on startup)
GEMINI_AVAILABLE = False
OPENAI_AVAILABLE = False

# Exhausted flags (temporary lockout)
GEMINI_EXHAUSTED_UNTIL = 0
OPENAI_EXHAUSTED_UNTIL = 0
EXHAUST_DURATION = 300  # 5 minutes lockout for 429

# Validate API keys on startup
def _validate_api_keys():
    """Validate API keys and set availability flags."""
    global GEMINI_AVAILABLE, OPENAI_AVAILABLE, AI_AVAILABLE

    # Check Gemini
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        try:
            # Test client creation
            test_client = genai.Client(api_key=gemini_key)
            GEMINI_AVAILABLE = True
            logger.info("Gemini API key validated successfully")
        except Exception as e:
            logger.warning("Gemini API key validation failed: %s", e)
            GEMINI_AVAILABLE = False
    else:
        logger.warning("GEMINI_API_KEY not set")
        GEMINI_AVAILABLE = False

    # Check OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            # Test client creation
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            # Minimal test call could be here, but just validating key presence for now
            OPENAI_AVAILABLE = True
            logger.info("OpenAI API key validated successfully")
        except Exception as e:
            logger.warning("OpenAI API key validation failed: %s", e)
            OPENAI_AVAILABLE = False
    else:
        logger.warning("OPENAI_API_KEY not set")
        OPENAI_AVAILABLE = False

    # Set overall AI availability
    AI_AVAILABLE = GEMINI_AVAILABLE or OPENAI_AVAILABLE
    if not AI_AVAILABLE:
        logger.warning("No AI providers available - falling back to heuristic/static responses")

# Initialize provider validation
_validate_api_keys()

def _get_available_providers(requested_provider: str = None) -> List[str]:
    """Get a list of available providers in priority order.
    
    If a provider is requested specifically, it comes first (even if exhausted, 
    we try and let error handling lockout if it fails).
    """
    providers = []
    now = time.time()

    if requested_provider:
        requested_provider = requested_provider.lower()
        if requested_provider in ["gemini", "openai"]:
            providers.append(requested_provider)
        elif requested_provider == "local":
            return ["heuristic"]

    # Add other variants for 'auto' or as backup
    # Priority: Gemini -> OpenAI
    if GEMINI_AVAILABLE and now > GEMINI_EXHAUSTED_UNTIL:
        if "gemini" not in providers:
            providers.append("gemini")
    
    if OPENAI_AVAILABLE and now > OPENAI_EXHAUSTED_UNTIL:
        if "openai" not in providers:
            providers.append("openai")
            
    # Heuristic always available
    if "heuristic" not in providers:
        providers.append("heuristic")
        
    return providers

def _call_ai_provider(provider: str, prompt: str) -> str:
    """Call the specified AI provider with error handling."""
    global AI_AVAILABLE, GEMINI_AVAILABLE, OPENAI_AVAILABLE, GEMINI_EXHAUSTED_UNTIL, OPENAI_EXHAUSTED_UNTIL

    try:
        if provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise RuntimeError("Gemini not available")
            client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
            return response.text if response and hasattr(response, 'text') else ""

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI not available")
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200
            )
            return response.choices[0].message.content if response and response.choices else ""

        else:
            raise ValueError(f"Unknown provider: {provider}")

    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
            logger.warning("AI provider %s exhausted: %s. Locking out for %d seconds.", provider, e, EXHAUST_DURATION)
            if provider == "gemini":
                GEMINI_EXHAUSTED_UNTIL = time.time() + EXHAUST_DURATION
            elif provider == "openai":
                OPENAI_EXHAUSTED_UNTIL = time.time() + EXHAUST_DURATION
        elif "api_key_invalid" in error_msg or "invalid api key" in error_msg:
            logger.error("API key invalid for provider %s: %s", provider, e)
            if provider == "gemini":
                GEMINI_AVAILABLE = False
            elif provider == "openai":
                OPENAI_AVAILABLE = False
            AI_AVAILABLE = GEMINI_AVAILABLE or OPENAI_AVAILABLE
        else:
            logger.warning("AI provider %s failed: %s", provider, e)
        raise

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
    
    # Use regex to find JSON object or array, handling multiline content
    # This will match from first { to last } or first [ to last ]
    match = re.search(r'(\{.*\}|\[.*\])', s, re.DOTALL)
    
    if match:
        return match.group(0)
    
    # Fallback to original logic if regex doesn't match
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
            "missing_skills": ["JavaScript", "SQL"],
            "roadmap": [
                {"title": "Learn JavaScript Basics", "description": "Master fundamental JavaScript concepts and syntax."},
                {"title": "Practice SQL Queries", "description": "Understand database querying and manipulation."},
                {"title": "Build a Simple Web App", "description": "Combine skills to create a basic application."}
            ],
            "matching_score": 65
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

    # Calculate matching score based on skill overlap
    base_match = len(user_skills_set & set(s.lower() for s in required_skills)) / len(required_skills) * 100
    matching_score = min(100, int(base_match))

    # Generate roadmap as a list of steps
    roadmap = []
    for i, skill in enumerate(missing_skills[:5], 1):
        roadmap.append({
            "title": f"Learn {skill}",
            "description": f"Focus on mastering {skill} to improve your fit for {target_role}."
        })
    if not roadmap:
        roadmap = [
            {"title": "Review Core Skills", "description": "Ensure proficiency in basic skills for the role."},
            {"title": "Practice Projects", "description": "Build projects to apply your knowledge."},
            {"title": "Seek Feedback", "description": "Get feedback on your skills and progress."}
        ]

    return {
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "roadmap": roadmap,
        "matching_score": matching_score
    }


def generate_ai_project_ideas(role, skills, requested_provider: str = None):
    """
    Generate project ideas using AI → Cache → Heuristic → Static hierarchy.
    Returns list[str] of 3 project titles.
    """
    global AI_CACHE, LAST_AI_SOURCE

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

    # Try AI providers in order
    providers_to_try = _get_available_providers(requested_provider)
    
    for provider in providers_to_try:
        if provider == "heuristic":
            break
            
        logger.info("AI_PROVIDER_TRYING=%s for generate_ai_project_ideas", provider)
        try:
            prompt = (
                "Return EXACTLY 3 short project titles (strings) as a JSON array."
                " No markdown, no explanation. JSON ONLY."
                f" Target role: {role}. Current skills: {', '.join(skills) if skills else 'None'}."
            )

            if len(prompt) > 100000:
                logger.warning("Prompt too long in generate_ai_project_ideas: %d characters", len(prompt))
                continue
                
            raw = _call_ai_provider(provider, prompt)
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
                                    with _LOCK:
                                        _set_cache(cache_key, titles)
                                        LAST_AI_SOURCE = provider
                                        _manage_cache_size()
                                    return titles
                    except Exception as e:
                        logger.warning("JSON parsing failed in generate_ai_project_ideas from %s: %s", provider, e)
        except Exception as e:
            logger.warning("AI %s failed in generate_ai_project_ideas: %s", provider, e)
            continue # Try next provider

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


def generate_learning_path_for_skill(skill: str, requested_provider: str = None):
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
        res = get_learning_paths_for_skills([skill], requested_provider)
        if isinstance(res, dict) and skill in res:
            return res.get(skill) or fallback
        return fallback
    except Exception:
        return fallback


def get_learning_paths_for_skills(skills: list, requested_provider: str = None):
    """
    Batch-generate learning paths for a list of skills using AI → Cache → Heuristic → Static hierarchy.
    Returns a dict mapping skill -> {summary, steps}.
    """
    global AI_CACHE, LAST_AI_SOURCE

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

    # Try AI providers in order
    providers_to_try = _get_available_providers(requested_provider)

    # Limit skills to top 10 for token efficiency
    limited_skills = skills[:10]
    skills_json = json.dumps(limited_skills)

    for provider in providers_to_try:
        if provider == "heuristic":
            break
        try:
            prompt = f"Return JSON: {{skill: {{summary: str, steps: [{{day_from:int, day_to:int, title:str, tasks:[str], project:str, resources:[str]}} exactly 3 per skill]}}}} for skills {skills_json}. Output JSON only."

            if len(prompt) > 100000:
                logger.warning("Prompt too long in get_learning_paths_for_skills: %d characters", len(prompt))
            else:
                raw = _call_ai_provider(provider, prompt)
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
                                    with _LOCK:
                                        _set_cache(cache_key, out)
                                        LAST_AI_SOURCE = provider
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
    Master Analyzer: Generates deep insights (gaps, role fit, projects) using AI.
    Does NOT access YouTube.
    """
    global AI_CACHE, LAST_AI_SOURCE

    # Input validation
    if not isinstance(user_skills, list):
        user_skills = []
    user_skills = [str(s).strip() for s in user_skills if s and isinstance(s, (str, int, float))]
    target_role = str(target_role or "").strip()

    # Limit skills to top 20 for context
    limited_user_skills = user_skills[:20]

    cache_key = _cache_key(f"{target_role}|unified_v2", limited_user_skills)
    with _LOCK:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            LAST_AI_SOURCE = "cache"
            return cached

    # Try AI providers in order
    providers_to_try = _get_available_providers(requested_provider)

    for provider in providers_to_try:
        if provider == "heuristic":
            break

        logger.info("AI_PROVIDER_TRYING=%s for get_unified_analysis", provider)
        try:
            user_skills_list = json.dumps(limited_user_skills)
            prompt = (
                f"Analyze the fit between these skills: {user_skills_list} and the role: '{target_role}'. "
                "Return a JSON object with EXACTLY these keys: "
                "match_percentage (int 0-100), "
                "missing_skills (list of specific technical skills missing), "
                "learning_path (list of strings, specific actionable steps/milestones), "
                "project_ideas (list of 3 specific project titles to bridge the gap), "
                "alternative_roles (list of 2-3 other job titles the user is qualified for). "
                "Do NOT include YouTube links. Output JSON only."
            )

            if len(prompt) > 100000:
                logger.warning("Prompt too long in get_unified_analysis")
                continue
                
            raw = _call_ai_provider(provider, prompt)
            if raw and isinstance(raw, str):
                raw = _strip_markdown(raw)
                if raw.strip():
                    json_str = _extract_json_like(raw)
                    if json_str:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and parsed:
                            # Basic validation/normalization
                            result = {
                                "match_percentage": int(parsed.get("match_percentage") or 0),
                                "missing_skills": [str(s).strip() for s in (parsed.get("missing_skills") or [])],
                                "learning_path": [str(s).strip() for s in (parsed.get("learning_path") or [])],
                                "project_ideas": [str(s).strip() for s in (parsed.get("project_ideas") or [])],
                                "alternative_roles": [str(s).strip() for s in (parsed.get("alternative_roles") or [])],
                                "required_skills": [] # Legacy field, can be inferred or left empty
                            }

                            if result["missing_skills"] or result["project_ideas"]:
                                with _LOCK:
                                    _set_cache(cache_key, result)
                                    LAST_AI_SOURCE = provider
                                    _manage_cache_size()
                                return result
        except Exception as e:
            logger.warning("AI %s failed in get_unified_analysis: %s", provider, e)
            continue 

    # Try heuristic fallback
    try:
        # Fallback to older heuristic method if AI fails, but adapt structure
        heuristic = _get_heuristic_unified_analysis(user_skills, target_role)
        fallback_result = {
             "match_percentage": heuristic.get("matching_score", 0),
             "missing_skills": heuristic.get("missing_skills", []),
             "learning_path": [h["title"] + ": " + h["description"] for h in heuristic.get("roadmap", [])],
             "project_ideas": _get_heuristic_project_ideas(target_role, user_skills),
             "alternative_roles": ["Frontend Developer", "Backend Developer"] # Generic fallback
        }
        with _LOCK:
            _set_cache(cache_key, fallback_result)
            LAST_AI_SOURCE = "heuristic"
            _manage_cache_size()
        return fallback_result
    except Exception as e:
        logger.warning("Heuristic fallback failed: %s", e)

    # Absolute static fallback
    static_result = {
        "match_percentage": 50,
        "missing_skills": ["Python", "SQL"],
        "learning_path": ["Learn Python basics", "Build a small project"],
        "project_ideas": ["Portfolio Website", "Task Tracker", "Weather App"],
        "alternative_roles": ["Web Developer"]
    }
    return static_result


def generate_chat_response(prompt: str, requested_provider: str = None) -> str:
    """
    Generate a chat response using AI → Heuristic hierarchy.
    """
    global LAST_AI_SOURCE

    # Try AI providers in order
    providers_to_try = _get_available_providers(requested_provider)

    for provider in providers_to_try:
        if provider == "heuristic":
            break

        logger.info("AI_PROVIDER_TRYING=%s for generate_chat_response", provider)
        try:
            res = _call_ai_provider(provider, prompt)
            if res and isinstance(res, str) and res.strip():
                LAST_AI_SOURCE = provider
                return res.strip()
        except Exception as e:
            logger.warning("AI %s failed in generate_chat_response: %s", provider, e)
            continue

    return "AI chat is currently unavailable. Please try again later."
