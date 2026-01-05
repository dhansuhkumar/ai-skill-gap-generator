# backend/app/ai_generator.py
import os
import json
import re
import hashlib
import logging
import threading
import time
import urllib.request
import urllib.error
from typing import List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Provider State & Configuration ---
_LOCK = threading.Lock()
AI_CACHE = {}  # key -> (timestamp, data)
_MAX_CACHE_SIZE = 500
_CACHE_TTL = 86400 * 3  # 3 Days

# Provider State Management
# available: Circuit breaker status (False = tripped)
# exhausted_until: Timestamp until which the provider is skipped
# enabled: Static configuration check (Env var exists)
PROVIDERS = {
    "gemini": {"available": True, "exhausted_until": 0, "enabled": bool(os.getenv("GEMINI_API_KEY"))},
    "groq":   {"available": True, "exhausted_until": 0, "enabled": bool(os.getenv("GROQ_API_KEY"))},
    "openai": {"available": True, "exhausted_until": 0, "enabled": bool(os.getenv("OPENAI_API_KEY"))}
}

COOLDOWN_SECONDS = 300  # 5 minutes

# --- Usage Helpers ---

def _cache_key(prefix: str, content: Any) -> str:
    s = f"{prefix}|{str(content)}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _get_from_cache(key):
    with _LOCK:
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
            parts = text.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    text = part.strip()[4:]
                    break
            else:
                 # Fallback if no json tag found but code blocks exist
                 if len(parts) > 1:
                    text = parts[1]
        except IndexError:
            pass
    
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match: 
        return match.group(0)
    return text # Hope for the best

# --- Provider Logic (Internal) ---

def _mark_provider_exhausted(provider_name: str):
    """Trigger circuit breaker for a specific provider."""
    global PROVIDERS
    with _LOCK:
        if provider_name in PROVIDERS:
            PROVIDERS[provider_name]["available"] = False
            PROVIDERS[provider_name]["exhausted_until"] = time.time() + COOLDOWN_SECONDS
            logger.warning(f"Provider '{provider_name}' marked exhausted until {time.time() + COOLDOWN_SECONDS}")

def _check_provider_recovery():
    """Reset available status if cooldown has passed."""
    global PROVIDERS
    now = time.time()
    with _LOCK:
        for name, state in PROVIDERS.items():
            if not state["available"] and now > state["exhausted_until"]:
                state["available"] = True
                state["exhausted_until"] = 0
                logger.info(f"Provider '{name}' recovered from cooldown")

def _get_provider_priority(requested_provider: str = None) -> List[str]:
    """Determine the order of providers to attempt."""
    _check_provider_recovery()
    
    # Standard priority: Gemini -> Groq -> OpenAI
    priority = ["gemini", "groq", "openai"]
    
    # If specific provider requested and enabled, try ONLY that one
    if requested_provider and requested_provider.lower() in PROVIDERS:
        p_name = requested_provider.lower()
        if PROVIDERS[p_name]["enabled"]:
            return [p_name]
        return [] # Requested provider not enabled
        
    if requested_provider == "auto" or not requested_provider:
        # Filter by enabled and available
        return [p for p in priority if PROVIDERS[p]["enabled"] and PROVIDERS[p]["available"]]
        
    return []

def _call_gemini(prompt: str) -> str:
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: return ""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash') # Using newer model if available or fallback
        response = model.generate_content(prompt)
        return response.text if response else ""
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err or "exhausted" in err:
            _mark_provider_exhausted("gemini")
        logger.warning(f"Gemini Error: {e}")
        return ""

def _call_groq(prompt: str) -> str:
    """Use urllib to access Groq API to avoid extra dependencies."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return ""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    data = {
        "model": "llama3-70b-8192", # Fast and capable
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _mark_provider_exhausted("groq")
        logger.warning(f"Groq API Error {e.code}: {e.reason}")
    except Exception as e:
        logger.warning(f"Groq connection failed: {e}")
    return ""

def _call_openai(prompt: str) -> str:
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key: return ""
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err or "rate limit" in err:
            _mark_provider_exhausted("openai")
        logger.warning(f"OpenAI Error: {e}")
        return ""

def _execute_provider(provider: str, prompt: str) -> str:
    """Execute a single provider call safely."""
    try:
        logger.info(f"Attempting provider: {provider}")
        if provider == "gemini":
            return _call_gemini(prompt)
        elif provider == "groq":
            return _call_groq(prompt)
        elif provider == "openai":
            return _call_openai(prompt)
    except Exception as e:
         logger.error(f"Unexpected error executing {provider}: {e}")
    return ""

def _generate_ai_response(prompt: str, requested_provider: str = None) -> str:
    """Orchestrate provider selection and execution."""
    providers = _get_provider_priority(requested_provider)
    
    if not providers:
        logger.warning(f"No available providers for request (requested: {requested_provider})")
        return ""

    for provider in providers:
        response = _execute_provider(provider, prompt)
        if response and len(response.strip()) > 5:
            return response
            
    logger.error("All AI providers failed or returned empty responses.")
    return ""

# --- Domain Specific Logic ---

def _load_skill_keywords() -> dict:
    """Load skill database and build a mapping."""
    mapping = {}
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'skill_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            for skill, info in data.items():
                mapping[skill.lower()] = skill
                for syn in info.get("synonyms", []):
                    mapping[syn.lower()] = skill
    except Exception as e:
        logger.error(f"Failed to load skill_data.json: {e}")
    return mapping

SKILL_MAPPING = _load_skill_keywords()

def extract_skills_deterministic(text: str) -> List[str]:
    """Extract skills using keyword matching."""
    if not SKILL_MAPPING: return []
    text_lower = text.lower()
    found = set()
    # Sort by length desc to match longest first
    sorted_keys = sorted(SKILL_MAPPING.keys(), key=len, reverse=True)
    
    for token in sorted_keys:
        escaped = re.escape(token)
        if re.search(r'(?:^|[^a-z0-9])' + escaped + r'(?:$|[^a-z0-9])', text_lower):
             found.add(SKILL_MAPPING[token])
    return list(found)

def extract_skills_with_ai(resume_text: str, requested_provider: str = None) -> List[str]:
    """Step 1: Parse Resume -> List[str]"""
    # 1. Deterministic Extraction
    local_skills = extract_skills_deterministic(resume_text)
    if local_skills:
        logger.info(f"Deterministic parser found {len(local_skills)} skills. Skipping AI.")
        return local_skills

    # 2. AI Extraction
    cache_key = _cache_key("resume_parse", resume_text[:500])
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        "Extract technical software skills from the resume text below. "
        "Return strictly a JSON object: {\"skills\": [\"Skill1\", \"Skill2\"]}. "
        "No output other than JSON. "
        f"RESUME TEXT:\n{resume_text[:4000]}"
    )
    
    raw_response = _generate_ai_response(prompt, requested_provider)
    
    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
        skills = data.get("skills", [])
        skills = [s for s in skills if isinstance(s, str)]
        
        if skills:
            _set_cache(cache_key, skills)
            return skills
    except Exception as e:
        logger.warning(f"AI extraction failed to parse: {e}")
    
    # 3. Fallback Heuristic
    keywords = ["python", "java", "sql", "react", "javascript", "node", "aws", "docker"]
    return [k.title() for k in keywords if k in resume_text.lower()]

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

    raw_response = _generate_ai_response(prompt, requested_provider)
    
    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
        if "missing_skills" in data:
            _set_cache(cache_key, data)
            return data
    except Exception as e:
        logger.warning(f"Gap analysis failed to parse: {e}")

    return {"missing_skills": ["Review Role Requirements"]} # Safe fallback

def generate_learning_plan(
    selected_skills: List[str], 
    role: str, 
    days: int, 
    hours: float, 
    project_type: str, 
    context: str = "", 
    learning_pace: str = "Balanced",
    time_commitment: str = "1 hour",
    requested_provider: str = None
) -> dict:
    """
    Step 6: Generate Detailed Plan -> Strict JSON
    Single AI invocation incorporating all user inputs.
    """
    if not selected_skills:
        return {"error": "No skills selected"}
        
    cache_key = _cache_key(f"plan_v2|{role}|{days}|{project_type}|{learning_pace}", selected_skills)
    cached = _get_from_cache(cache_key)
    if cached: return cached

    prompt = (
        f"You are an expert technical mentor. Create a detailed learning plan for a '{role}'.\n"
        f"Goal: Learn these missing skills: {json.dumps(selected_skills)}.\n"
        f"Profile/Preferences:\n"
        f"- Time Commitment: {time_commitment} per day ({hours} hours)\n"
        f"- Duration: {days} days\n"
        f"- Learning Pace: {learning_pace}\n"
        f"- Preferred Project Type: {project_type}\n"
        f"- Additional Context: {context}\n\n"
        "Requirements:\n"
        "1. Create a day-by-day or week-by-week schedule split by skill.\n"
        "2. Suggest 1-2 concrete projects that apply these skills.\n"
        "3. Provide a 'matching_score' (0-100) estimating how close they are to the role after this plan.\n\n"
        "Return strictly valid JSON with this structure:\n"
        "{\n"
        "  \"learning_paths\": {\n"
        "    \"SkillName\": {\n"
        "      \"summary\": \"Brief goal for this skill\",\n"
        "      \"steps\": [\n"
        "        {\"day_from\": 1, \"day_to\": 3, \"title\": \"Topic Title\", \"tasks\": [\"Task 1\", \"Task 2\"], \"resources\": [\"Topic keywords\"]}\n"
        "      ]\n"
        "    }\n"
        "  },\n"
        "  \"projects\": [\n"
        "    {\"title\": \"Project Name\", \"skills\": [\"Skill1\", \"Skill2\"], \"description\": \"What to build and why.\"}\n"
        "  ],\n"
        "  \"matching_score\": 85\n"
        "}\n"
        "JSON ONLY. NO MARKDOWN. NO PREAMBLE."
    )

    raw_response = _generate_ai_response(prompt, requested_provider)
    provider_used = requested_provider if requested_provider else "auto"

    try:
        json_str = _extract_json_like(raw_response)
        data = json.loads(json_str)
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

def generate_chat_response(prompt: str, requested_provider: str = None) -> str:
    """
    Simple wrapper for chat interactions.
    """
    return _generate_ai_response(prompt, requested_provider)
