import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# This module does not call Gemini directly. For interactive AI chat, integrate
# with the central `ai_generator` entrypoint to avoid distributed Gemini calls.


def _build_role_chat_prompt(role: str, messages: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the role-aware chat conversation.
    Messages format: [{"sender": "user"|"ai", "text": "..."}]
    """
    role = (role or "").strip()

    history_lines = []
    for msg in messages or []:
        # Support both formats: {role, content} (standard) and {sender, text} (legacy)
        sender = msg.get("role") or msg.get("sender") or ""
        text = msg.get("content") or msg.get("text") or ""
        
        sender = sender.lower()
        text = text.strip()
        
        if not text:
            continue
        
        tag = "User" if sender in ["user", "human"] else "Assistant"
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


def generate_role_chat_reply(role: str, messages: List[Dict[str, Any]], requested_provider: str = None) -> str:
    """
    Call central AI generator to generate the next chat reply for the role conversation.
    """
    from . import ai_generator
    prompt = _build_role_chat_prompt(role, messages)
    try:
        return ai_generator.generate_chat_response(prompt, requested_provider=requested_provider)
    except Exception as e:
        return "I'm having trouble connecting to my AI brain. Please try again in a moment."
