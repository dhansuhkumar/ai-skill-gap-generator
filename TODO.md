# AI Integration Fixes TODO

## 1. Centralize AI Provider Logic
- [ ] Create provider switch in ai_generator.py supporting "gemini", "openai", "heuristic"
- [ ] Validate API keys on startup and set availability flags
- [ ] Implement circuit breaker for failed providers

## 2. Fix Gemini API Handling
- [ ] Move client initialization inside functions with error handling
- [ ] Set AI_AVAILABLE = False on API_KEY_INVALID and log once
- [ ] Prevent further Gemini attempts until restart

## 3. Improve get_unified_analysis() Logic
- [ ] Update function signature: def get_unified_analysis(user_skills, target_role, requested_provider=None)
- [ ] Enforce priority: Gemini → OpenAI → Heuristic → Static
- [ ] Prevent infinite retry loops
- [ ] Cache negative results

## 4. Add Explicit Provider Selection
- [ ] Support requested_provider parameter ("gemini", "openai", "local")
- [ ] Force specific provider when requested

## 5. Fix Pydantic Warning
- [ ] Replace `any` with `from typing import Any`

## 6. Improve Logging
- [ ] Add structured logs: logger.info("AI_PROVIDER_USED=%s", provider)
- [ ] Add fallback triggered warnings with extra details

## 7. Ensure System Stability
- [ ] App must never crash when API keys missing
- [ ] AI endpoints must still respond with heuristic results
- [ ] Test backward compatibility
