"""AI provider router: select provider (auto|gemini|openai|local) and cache last-successful provider.

This module exposes simple functions to pick the provider for a request
and to persist the last successful provider in-memory.
"""
import os
from threading import Lock
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    import openai
except Exception:
    openai = None

try:
    import groq
except Exception:
    groq = None

_GENAI_CONFIGURED = False

_LOCK = Lock()
# last successful provider name: 'gemini' | 'openai' | 'local' or None
LAST_SUCCESSFUL_PROVIDER = None


def get_last_successful_provider():
    with _LOCK:
        return LAST_SUCCESSFUL_PROVIDER


def set_last_successful_provider(name: str):
    global LAST_SUCCESSFUL_PROVIDER
    with _LOCK:
        LAST_SUCCESSFUL_PROVIDER = name


def select_provider(requested: str = None):
    """Select provider given requested string.

    - requested: 'auto'|'gemini'|'openai'|'local' or None
    - returns a single provider string to use for the request
    - does not attempt any network calls; selection is deterministic
    """
    requested = (requested or "auto").lower()
    # Normalize
    if requested not in ("auto", "gemini", "openai", "local"):
        requested = "auto"

    if requested == "auto":
        last = get_last_successful_provider()
        if last:
            return last
        # No last-known provider: prefer gemini, then openai, then local
        return "gemini" if os.getenv("GEMINI_API_KEY") else ("openai" if os.getenv("OPENAI_API_KEY") else "local")

    return requested


def _provider_available(name: str) -> bool:
    name = (name or "").lower()
    if name == "gemini":
        _ensure_genai_configured()
        return bool(genai and os.getenv("GEMINI_API_KEY"))
    if name == "openai":
        return bool(openai and os.getenv("OPENAI_API_KEY"))
    if name == "groq":
        return bool(os.getenv("GROQ_API_KEY") and groq)
    if name == "local":
        return True
    return False


def get_ai_response(prompt: str, requested_provider: Optional[str] = None) -> str:
    """Try providers in configured order and return the raw text response.

    - Reads `AI_PROVIDER_ORDER` env var (comma-separated) or defaults to
      'gemini,openai,groq,local'.
    - Caches last successful provider in `LAST_SUCCESSFUL_PROVIDER`.
    - Never retries the same provider twice in a single call.
    - Returns a string (should be valid JSON for our callers); on local
      fallback it returns a minimal valid JSON string.
    """
    order = os.getenv("AI_PROVIDER_ORDER", "gemini,openai,groq,local")
    providers = [p.strip().lower() for p in order.split(",") if p.strip()]

    requested = (requested_provider or "auto").lower()
    if requested != "auto" and requested in providers:
        # try requested first, then remaining in order
        providers = [requested] + [p for p in providers if p != requested]
    # ensure uniqueness
    seen = set()
    providers = [p for p in providers if not (p in seen or seen.add(p))]

    attempted = set()
    last_success = None
    for provider in providers:
        if provider in attempted:
            continue
        attempted.add(provider)

        if not _provider_available(provider):
            continue

        try:
            if provider == "gemini":
                _ensure_genai_configured()
                model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                raw = getattr(resp, "text", "") or ""
                if raw:
                    last_success = "gemini"
                    with _LOCK:
                        global LAST_SUCCESSFUL_PROVIDER
                        LAST_SUCCESSFUL_PROVIDER = last_success
                    return raw

            if provider == "openai":
                openai.api_key = os.getenv("OPENAI_API_KEY")
                resp = openai.ChatCompletion.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role": "user", "content": prompt}], max_tokens=1200)
                raw = resp.choices[0].message.content if resp and getattr(resp, 'choices', None) else ""
                if raw:
                    last_success = "openai"
                    with _LOCK:
                        LAST_SUCCESSFUL_PROVIDER = last_success
                    return raw

            if provider == "groq":
                # groq client usage is optional and may not be present; skip if not supported
                if groq:
                    # Placeholder: this may need to be adapted to your groq client
                    api_key = os.getenv("GROQ_API_KEY")
                    # Attempt a simplistic call if client supports it
                    try:
                        raw = groq.generate(prompt, api_key=api_key)  # type: ignore
                    except Exception:
                        raw = ""
                    if raw:
                        last_success = "groq"
                        with _LOCK:
                            LAST_SUCCESSFUL_PROVIDER = last_success
                        return raw

            if provider == "local":
                # Return a minimal valid JSON object as a string
                out = {
                    "schema_version": "v1",
                    "candidate_required_skills": [],
                    "candidate_missing_skills": [],
                    "suggested_focus_skills": [],
                    "job_matches": [],
                    "ai_projects_sample": [],
                }
                raw = json.dumps(out)
                with _LOCK:
                    LAST_SUCCESSFUL_PROVIDER = "local"
                return raw

        except Exception as e:
            logger.warning("Provider %s failed: %s", provider, e)
            # continue to next provider
            continue

    # If none succeeded, return minimal JSON
    out = {
        "schema_version": "v1",
        "candidate_required_skills": [],
        "candidate_missing_skills": [],
        "suggested_focus_skills": [],
        "job_matches": [],
        "ai_projects_sample": [],
    }
    return json.dumps(out)
