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
from pathlib import Path

load_dotenv()

# --- AI Client Setup ---
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
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Observability & Cache ---
_LOCK = threading.Lock()
AI_AVAILABLE = True
AI_CACHE = {}  # key -> (timestamp, data)
_MAX_CACHE_SIZE = 500
_CACHE_TTL = 86400 * 3  # 3 Days
GEMINI_AVAILABLE = False
OPENAI_AVAILABLE = False
GEMINI_EXHAUSTED_UNTIL = 0
OPENAI_EXHAUSTED_UNTIL = 0
EXHAUST_DURATION = 300  # 5 minutes

def _validate_api_keys():
    global GEMINI_AVAILABLE, OPENAI_AVAILABLE, AI_AVAILABLE
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            GEMINI_AVAILABLE = True
            logger.info("Gemini API key validated.")
        except Exception as e:
            logger.warning("Gemini API key invalid: %s", e)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        OPENAI_AVAILABLE = True # Lazy validation for OpenAI to avoid cost on startup
        logger.info("OpenAI API key present.")

    AI_AVAILABLE = GEMINI_AVAILABLE or OPENAI_AVAILABLE

_validate_api_keys()

def _get_available_providers(requested_provider: str = None) -> List[str]:
    providers = []
    now = time.time()
    if requested_provider:
        p = requested_provider.lower()
        if p in ["gemini", "openai"]:
            providers.append(p)
        elif p == "local":
            return ["heuristic"]
    
    # Cost optimization: Gemini (Flash Lite) -> OpenAI (Mini) -> Heuristic
    if GEMINI_AVAILABLE and now > GEMINI_EXHAUSTED_UNTIL and "gemini" not in providers:
        providers.append("gemini")
    if OPENAI_AVAILABLE and now > OPENAI_EXHAUSTED_UNTIL and "openai" not in providers:
        providers.append("openai")
    
    if "heuristic" not in providers:
        providers.append("heuristic")
    return providers

def _call_ai_provider(provider: str, prompt: str) -> str:
    global GEMINI_AVAILABLE, OPENAI_AVAILABLE, GEMINI_EXHAUSTED_UNTIL, OPENAI_EXHAUSTED_UNTIL
    
    try:
        if provider == "gemini":
            client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            # Use Flash Lite for strict cost control
            response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
            return response.text if response and hasattr(response, 'text') else ""
            
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Cheap model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return response.choices[0].message.content if response and response.choices else ""
            
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning(f"{provider} exhausted. Locking out.")
            if provider == "gemini": GEMINI_EXHAUSTED_UNTIL = time.time() + EXHAUST_DURATION
            if provider == "openai": OPENAI_EXHAUSTED_UNTIL = time.time() + EXHAUST_DURATION
        logger.error(f"AI Provider {provider} error: {e}")
        return ""
    return ""

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
    text = text.strip()
    # Remove markdown code blocks
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match: 
        return match.group(0)
    return text # Hope for the best

# --- Core Logic Functions (1 Step = 1 Call) ---

def extract_skills_with_ai(resume_text: str, requested_provider: str = None) -> List[str]:
    """Step 1: Parse Resume -> List[str]"""
    cache_key = _cache_key("resume_parse", resume_text[:500]) # Cache based on first 500 chars 
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        "Extract technical software skills from the resume text below. "
        "Return strictly a JSON object: {\"skills\": [\"Skill1\", \"Skill2\"]}. "
        "No output other than JSON. "
        f"RESUME TEXT:\n{resume_text[:4000]}" # Truncate for safety
    )

    for provider in _get_available_providers(requested_provider):
        if provider == "heuristic": break
        raw = _call_ai_provider(provider, prompt)
        try:
            json_str = _extract_json_like(raw)
            data = json.loads(json_str)
            skills = data.get("skills", [])
            skills = [s for s in skills if isinstance(s, str)]
            if skills:
                _set_cache(cache_key, skills)
                return skills
        except Exception:
            continue
    
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

    for provider in _get_available_providers(requested_provider):
        if provider == "heuristic": break
        raw = _call_ai_provider(provider, prompt)
        try:
            json_str = _extract_json_like(raw)
            data = json.loads(json_str)
            if "missing_skills" in data:
                _set_cache(cache_key, data)
                return data
        except Exception:
            continue

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

    provider_used = "heuristic"
    for provider in _get_available_providers(requested_provider):
        provider_used = provider
        if provider == "heuristic": break
        raw = _call_ai_provider(provider, prompt)
        try:
            json_str = _extract_json_like(raw)
            data = json.loads(json_str)
            # Basic validation
            if "learning_paths" in data and "projects" in data:
                data["source"] = provider  # Track which provider was used
                _set_cache(cache_key, data)
                return data
        except Exception as e:
            logger.error(f"Failed to parse plan from {provider}: {e}")
            continue

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
        "source": provider_used
    }
