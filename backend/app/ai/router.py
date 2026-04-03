"""AI provider router: Groq (LLaMA 3) primary, local fallback."""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except Exception:
    Groq = None
    GROQ_AVAILABLE = False


def get_ai_response(prompt: str, requested_provider: Optional[str] = None, is_json: bool = True) -> str:
    """Try Groq first (LLaMA 3), then fallback to local heuristic."""
    if not isinstance(prompt, str) or not prompt.strip():
        logger.warning("Invalid prompt provided to get_ai_response")
        return _get_fallback_response(is_json)

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and GROQ_AVAILABLE:
        try:
            client = Groq(api_key=groq_key)
            
            sys_msg = "You are a career development AI assistant. Always respond with valid JSON only."
            if not is_json:
                sys_msg = "You are a helpful career development AI assistant. Be conversational, helpful, and keep it concise. Do not use JSON formatting."
                
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": sys_msg,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content
            if raw and len(raw) > 10:
                return raw
        except Exception as e:
            logger.error(f"Groq failed: {e}")

    return _get_fallback_response(is_json)


def _get_fallback_response(is_json: bool = True) -> str:
    """Return standardized fallback response."""
    if not is_json:
        return "I'm having trouble connecting right now, but I'm here to help with your career path!"
        
    out = {
        "schema_version": "v1",
        "candidate_required_skills": [],
        "candidate_missing_skills": [],
        "suggested_focus_skills": [],
        "job_matches": [],
        "ai_projects_sample": [],
    }
    return json.dumps(out)

