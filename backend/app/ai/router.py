"""AI provider router: select provider (auto|gemini|openai|local) and cache last-successful provider.

This module exposes simple functions to pick the provider for a request
and to persist the last successful provider in-memory.
"""
import os
import asyncio
import time
from threading import Lock
import logging
import json
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    import google.genai as genai
except ImportError:
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

if genai is None:
    logger.warning("Neither google.genai nor google.generativeai is available")

try:
    import openai
except Exception:
    openai = None

try:
    import groq
except Exception:
    groq = None

_GENAI_CONFIGURED = False
_GENAI_CONFIGURED_LOCK = Lock()

_LOCK = Lock()
# last successful provider name: 'gemini' | 'openai' | 'local' or None
LAST_SUCCESSFUL_PROVIDER = None
AI_AVAILABLE = True
# Circuit breaker recovery: track failures and allow recovery
_FAILURE_COUNT = 0
_LAST_FAILURE_TIME = 0
_MAX_FAILURES = 5
_RECOVERY_TIME = 300  # 5 minutes


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


def _ensure_genai_configured():
    """Thread-safe configuration of genai client."""
    global _GENAI_CONFIGURED
    if _GENAI_CONFIGURED:
        return

    with _GENAI_CONFIGURED_LOCK:
        if _GENAI_CONFIGURED:
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set")
            return

        try:
            genai.configure(api_key=api_key)
            _GENAI_CONFIGURED = True
            logger.info("GenAI configured successfully")
        except Exception as e:
            logger.error("Failed to configure GenAI: %s", e)
            raise


def _is_ai_available() -> bool:
    """Check if AI is available with circuit breaker recovery."""
    global AI_AVAILABLE, _FAILURE_COUNT, _LAST_FAILURE_TIME

    with _LOCK:
        # Allow recovery after cooldown period
        if not AI_AVAILABLE and time.time() - _LAST_FAILURE_TIME > _RECOVERY_TIME:
            AI_AVAILABLE = True
            _FAILURE_COUNT = 0
            logger.info("AI circuit breaker recovered")

        return AI_AVAILABLE


def _record_failure():
    """Record a failure for circuit breaker logic."""
    global AI_AVAILABLE, _FAILURE_COUNT, _LAST_FAILURE_TIME

    with _LOCK:
        _FAILURE_COUNT += 1
        _LAST_FAILURE_TIME = time.time()

        if _FAILURE_COUNT >= _MAX_FAILURES:
            AI_AVAILABLE = False
            logger.warning("AI circuit breaker triggered after %d failures", _FAILURE_COUNT)


def _provider_available(name: str) -> bool:
    name = (name or "").lower()
    if name == "gemini":
        try:
            _ensure_genai_configured()
            return bool(genai and os.getenv("GEMINI_API_KEY"))
        except Exception:
            return False
    if name == "openai":
        return bool(openai and os.getenv("OPENAI_API_KEY"))
    if name == "groq":
        return bool(os.getenv("GROQ_API_KEY") and groq)
    if name == "local":
        return True
    return False


async def get_ai_response(prompt: str, requested_provider: Optional[str] = None) -> str:
    """Try providers in configured order and return the raw text response.

    - Reads `AI_PROVIDER_ORDER` env var (comma-separated) or defaults to
      'gemini,openai,groq,local'.
    - Caches last successful provider in `LAST_SUCCESSFUL_PROVIDER`.
    - Never retries the same provider twice in a single call.
    - Returns a string (should be valid JSON for our callers); on local
      fallback it returns a minimal valid JSON string.
    """
    # Validate input
    if not isinstance(prompt, str) or not prompt.strip():
        logger.warning("Invalid prompt provided to get_ai_response")
        return _get_fallback_response()

    # Enforce prompt size limit
    if len(prompt) > 100000:
        logger.warning("Prompt too long: %d characters, max 100000", len(prompt))
        return _get_fallback_response()

    # Check circuit breaker
    if not _is_ai_available():
        logger.info("AI unavailable due to circuit breaker")
        return _get_fallback_response()

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
    timeout = int(os.getenv("AI_TIMEOUT", "30"))  # Default 30 seconds

    for provider in providers:
        if provider in attempted:
            continue
        attempted.add(provider)

        if not _provider_available(provider):
            continue

        try:
            # Add timeout protection
            if provider == "gemini":
                _ensure_genai_configured()
                model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
                model = genai.GenerativeModel(model_name)

                # Use asyncio.wait_for for timeout
                resp = await asyncio.wait_for(
                    model.generate_content_async(prompt),
                    timeout=timeout
                )
                raw = getattr(resp, "text", "") or ""
                if raw and _is_valid_response(raw):
                    last_success = "gemini"
                    with _LOCK:
                        global LAST_SUCCESSFUL_PROVIDER
                        LAST_SUCCESSFUL_PROVIDER = last_success
                    return raw

            elif provider == "openai":
                # OpenAI doesn't have async in this version, wrap in thread
                import concurrent.futures
                import threading

                def openai_call():
                    openai.api_key = os.getenv("OPENAI_API_KEY")
                    return openai.ChatCompletion.create(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1200,
                        timeout=timeout
                    )

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(openai_call)
                    resp = await asyncio.wait_for(
                        asyncio.wrap_future(future),
                        timeout=timeout + 2  # Extra time for thread overhead
                    )

                raw = resp.choices[0].message.content if resp and getattr(resp, 'choices', None) else ""
                if raw and _is_valid_response(raw):
                    last_success = "openai"
                    global LAST_SUCCESSFUL_PROVIDER
                    with _LOCK:
                        LAST_SUCCESSFUL_PROVIDER = last_success
                    return raw

            elif provider == "groq":
                # groq client usage is optional and may not be present; skip if not supported
                if groq:
                    # Placeholder: this may need to be adapted to your groq client
                    api_key = os.getenv("GROQ_API_KEY")
                    # Attempt a simplistic call if client supports it
                    try:
                        raw = groq.generate(prompt, api_key=api_key)  # type: ignore
                        if raw and _is_valid_response(raw):
                            last_success = "groq"
                            global LAST_SUCCESSFUL_PROVIDER
                            with _LOCK:
                                LAST_SUCCESSFUL_PROVIDER = last_success
                            return raw
                    except Exception:
                        pass

            elif provider == "local":
                # Return a minimal valid JSON object as a string
                return _get_fallback_response()

        except asyncio.TimeoutError:
            logger.warning("Provider %s timed out after %d seconds", provider, timeout)
            _record_failure()
        except Exception as e:
            error_msg = str(e).lower()
            # Comprehensive error detection
            error_tokens = [
                "429", "resourceexhausted", "defaultcredentialserror", "permission",
                "quota", "notfound", "502", "503", "504", "timeout", "connection",
                "network", "dns", "ssl", "certificate", "unavailable", "internal",
                "server error", "bad gateway", "service unavailable"
            ]

            if any(token in error_msg for token in error_tokens):
                logger.error("Provider %s API/network error: %s", provider, e)
                _record_failure()
            else:
                logger.warning("Provider %s failed: %s", provider, e)
                _record_failure()
            # continue to next provider
            continue

    # If none succeeded, record failure and return fallback
    _record_failure()
    return _get_fallback_response()


def _is_valid_response(response: str) -> bool:
    """Basic validation that response is not empty and contains expected content."""
    if not response or not isinstance(response, str):
        return False
    response = response.strip()
    if len(response) > 50000:
        logger.warning("Response too long: %d characters, max 50000", len(response))
        return False
    return len(response) > 10  # Basic length check


def _get_fallback_response() -> str:
    """Return standardized fallback JSON response."""
    out = {
        "schema_version": "v1",
        "candidate_required_skills": [],
        "candidate_missing_skills": [],
        "suggested_focus_skills": [],
        "job_matches": [],
        "ai_projects_sample": [],
    }
    return json.dumps(out)
