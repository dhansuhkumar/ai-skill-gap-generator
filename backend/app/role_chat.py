import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv
try:
    import google.generativeai as genai
except Exception as _e:
    genai = None
    print("⚠️ google.generativeai import failed (role chat disabled):", _e)

load_dotenv()

# Do not configure genai at import time here; centralize configuration in ai_generator


def _build_role_chat_prompt(role: str, messages: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the role-aware chat conversation.
    Messages format: [{\"sender\": \"user\"|\"ai\", \"text\": \"...\"}, ...]
    """
    role = (role or "").strip()

    history_lines = []
    for msg in messages or []:
        sender = (msg.get("sender") or "").lower()
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        tag = "User" if sender == "user" else "Assistant"
        history_lines.append(f"{tag}: {text}")

    history_block = "\n".join(history_lines[-12:]) if history_lines else "User: (no previous conversation)"

    prompt = f"""
You are an expert career coach for technology roles.

Target role: "{role or "Unknown"}"

Conversation so far:
{history_block}

Your job now:
- Ask focused, practical questions to clearly understand the user's background
  for this specific role: skills, tools, years of experience, real projects, and current learning progress.
- When the user already provided details, reflect them briefly and ask for the
  next most important missing info.
- Use short paragraphs or bullet-like sentences (1–4 lines).
- Avoid JSON or code blocks in your reply.
- Keep the tone encouraging but concise.

Respond with a single conversational message only.
"""
    return prompt


def generate_role_chat_reply(role: str, messages: List[Dict[str, Any]]) -> str:
    """
    Call Gemini to generate the next chat reply for the role conversation.
    """
    if not GEMINI_API_KEY:
        # Fallback: simple deterministic reply if AI is not configured
        return (
            "AI chat is not fully configured yet (missing GEMINI_API_KEY), "
            "but you can still describe your skills, projects, and goals for this role. "
            "Focus on concrete technologies you've used and years of experience."
        )

    model_name = "gemini-2.5-flask"
    try:
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                name = getattr(m, "name", "")
                if "gemini-2.5-flash" in name:
                    model_name = name
                    break
                elif "gemini-2.0-flash" in name:
                    model_name = name
                elif "gemini-1.5-flash" in name and "2.5" not in model_name:
                    model_name = name
        print(f"🔍 Selected Model for Role Chat: {model_name}")
    except Exception as e:
        print(f"⚠️ Error selecting model for role chat: {e}")

    model = genai.GenerativeModel(model_name)
    prompt = _build_role_chat_prompt(role, messages)

    response = model.generate_content(prompt)
    text = getattr(response, "text", "").strip()
    if not text:
        return (
            "I couldn't generate a detailed response just now. "
            "Could you briefly list your main skills and recent projects for this role?"
        )
    return text



