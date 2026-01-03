# backend/app/ai_generator.py
import os
import json
import re
import hashlib
import logging
import threading
import time
from typing import List, Optional, Any
from dotenv import load_dotenv
from app.ai.router import get_ai_response

load_dotenv()

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Observability & Cache ---
_LOCK = threading.Lock()
AI_CACHE = {}  # key -> (timestamp, data)
_MAX_CACHE_SIZE = 500
_CACHE_TTL = 86400 * 3  # 3 Days

# --- Usage Helpers ---

def _cache_key(prefix: str, content: Any) -> str:
    s = f"{prefix}|{str(content)}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _get_from_cache(key):
    if key in AI_CACHE:
        ts, data = AI_CACHE[key]
        if time.time() - ts < _CACHE_TTL:
            return data
    return None

def _set_cache(key, data):
    with _LOCK:
        if len(AI_CACHE) > _MAX_CACHE_SIZE:
             AI_CACHE.clear() # Simple purge
        AI_CACHE[key] = (time.time(), data)

def _extract_json_like(text: str) -> str:
    """Robust JSON extraction searching for outer brackets."""
    if not text: return "{}"
    text = text.strip()
    # Remove markdown code blocks
    if "```" in text:
        try:
            text = text.split("```")[1]
            if text.strip().startswith("json"):
                text = text.strip()[4:]
        except IndexError:
            pass
    
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match: 
        return match.group(0)
    return text # Hope for the best

# --- Core Logic Functions (1 Step = 1 Call) ---

def _load_skill_keywords() -> dict:
    """
    Load skill database and build a mapping of 'lowercase_token' -> 'Canonical Name'.
    Include synonyms.
    """
    mapping = {}
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'skill_data.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        for skill, info in data.items():
            # Add main skill name
            mapping[skill.lower()] = skill
            # Add synonyms
            for syn in info.get("synonyms", []):
                mapping[syn.lower()] = skill
    except Exception as e:
        logger.error(f"Failed to load skill_data.json: {e}")
    return mapping

SKILL_MAPPING = _load_skill_keywords()

def extract_skills_deterministic(text: str) -> List[str]:
    """
    Extract skills using keyword matching against known database.
    Case-insensitive.
    """
    if not SKILL_MAPPING:
        return []
        
    text_lower = text.lower()
    found_skills = set()
    
    # Sort keys by length descending to match longest phrases first
    sorted_keys = sorted(SKILL_MAPPING.keys(), key=len, reverse=True)
    
    import re
    
    for token in sorted_keys:
        escaped_token = re.escape(token)
        # Regex check for token presence
        if re.search(r'(?:^|[^a-z0-9])' + escaped_token + r'(?:$|[^a-z0-9])', text_lower):
             found_skills.add(SKILL_MAPPING[token])

    return list(found_skills)

def extract_skills_with_ai(resume_text: str, requested_provider: str = None) -> List[str]:
    """Step 1: Parse Resume -> List[str]"""
    
    # 1. Deterministic Extraction (Cost: 0)
    local_skills = extract_skills_deterministic(resume_text)
    if local_skills:
        logger.info(f"Deterministic parser found {len(local_skills)} skills: {local_skills}. Skipping AI.")
        return local_skills

    # 2. AI Extraction (Fallback)
    logger.info("No deterministic matches found. Falling back to AI.")
    
    cache_key = _cache_key("resume_parse", resume_text[:500]) 
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        "Extract technical software skills from the resume text below. "
        "Return strictly a JSON object: {\"skills\": [\"Skill1\", \"Skill2\"]}. "
        "No output other than JSON. "
        f"RESUME TEXT:\n{resume_text[:4000]}"
    )

    # Use router
    raw_response = get_ai_response(prompt, requested_provider)
    
    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
        skills = data.get("skills", [])
        
        # Validate list of strings
        skills = [s for s in skills if isinstance(s, str)]
        
        if skills:
            _set_cache(cache_key, skills)
            return skills
    except Exception as e:
        logger.warning(f"AI extraction failed to parse: {e}")
    
    # Fallback: Naive regex extraction
    keywords = ["python", "java", "sql", "react", "javascript", "node", "aws", "docker"]
    found = [k.title() for k in keywords if k in resume_text.lower()]
    return found

def analyze_skill_gaps(current_skills: List[str], target_role: str, requested_provider: str = None) -> dict:
    """Step 2: Compare Skills vs Role -> Missing Skills"""
    cache_key = _cache_key(f"gap_analysis|{target_role}", current_skills)
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        f"Compare these skills: {json.dumps(current_skills)} with the requirements for the role: '{target_role}'. "
        "Identify MISSING technical skills. "
        "Return strict JSON: {\"missing_skills\": [\"SkillA\", \"SkillB\"]}. "
        "JSON ONLY. No markdown."
    )

    raw_response = get_ai_response(prompt, requested_provider)
    
    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
        if "missing_skills" in data:
            _set_cache(cache_key, data)
            return data
    except Exception as e:
        logger.warning(f"Gap analysis failed to parse: {e}")

    return {"missing_skills": ["Review Role Requirements"]} # Safe fallback

def generate_learning_plan(selected_skills: List[str], role: str, days: int, hours: float, project_type: str, context: str = "", requested_provider: str = None) -> dict:
    """Step 3: Generate Detailed Plan -> Strict JSON"""
    if not selected_skills:
        return {"error": "No skills selected"}
        
    cache_key = _cache_key(f"plan|{role}|{days}|{project_type}", selected_skills)
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        f"Create a {days}-day learning path for a '{role}' to learn these skills: {json.dumps(selected_skills)}. "
        f"Constraints: {hours} hours/day, Focus: {project_type}. Context: {context}. "
        "Return strictly this JSON structure:\n"
        "{\n"
        "  \"learning_paths\": {\n"
        "    \"SkillName\": {\n"
        "      \"steps\": [{\"day_from\": 1, \"day_to\": 3, \"title\": \"...\", \"tasks\": [\"...\"], \"project\": \"...\"}]\n"
        "    }\n"
        "  },\n"
        "  \"projects\": [{\"title\": \"...\", \"skills\": [\"...\"], \"description\": \"...\"}],\n"
        "  \"matching_score\": 75\n"
        "}\n"
        "JSON ONLY. NO MARKDOWN."
    )

    raw_response = get_ai_response(prompt, requested_provider)
    
    # Track provider used for metadata
    # (The router doesn't return which provider was used in the response string, 
    # but we can infer or just report 'ai-router' or the requested one)
    provider_used = requested_provider if requested_provider else "auto"

    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
        # Basic validation
        if "learning_paths" in data and "projects" in data:
            data["source"] = provider_used 
            _set_cache(cache_key, data)
            return data
    except Exception as e:
        logger.error(f"Failed to parse plan: {e}")

    # Fallback structure
    return {
        "learning_paths": {
            s: {
                "summary": f"Learn {s} for {role}",
                "steps": [{"day_from": 1, "day_to": days, "title": f"Learn {s}", "tasks": ["Read Docs", "Build Demo"], "project": f"Simple {s} App", "resources": []}]
            }
            for s in selected_skills
        },
        "projects": [{"title": "Portfolio Project", "skills": selected_skills, "description": "Combine all skills."}],
        "matching_score": 50,
        "source": "heuristic_fallback"
    }
