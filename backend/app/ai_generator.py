# backend/app/ai_generator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_ai_project_ideas(role, skills):
    print(f"--- 🤖 AI Generator Started for: {role} ---")

    valid_model_name = "gemini-pro"  # Safe fallback

    try:
        # Dynamically pick the best available model
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if "gemini-2.5-flash" in m.name:
                    valid_model_name = m.name
                    break
                elif "gemini-2.0-flash" in m.name:
                    valid_model_name = m.name
                elif "gemini-1.5-flash" in m.name and "2.5" not in valid_model_name:
                    valid_model_name = m.name
        print(f"🔍 Selected Model: {valid_model_name}")
    except Exception as e:
        print(f"⚠️ Model list failed, using default: {e}")

    try:
        model = genai.GenerativeModel(valid_model_name)

        # Stronger prompt: force short, hyphenated titles only
        prompt = (
            f"I am a student wanting to be a {role}. I know {', '.join(skills)}. "
            f"Suggest exactly 3 creative, small coding project titles. "
            f"Each project must be a single short line starting with a hyphen (-). "
            f"No explanations, no goals, no extra text — just the titles."
        )

        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()
        print("🔍 Raw Gemini output:", raw_text)

        # Clean and filter lines
        ideas = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("-"):
                # Remove leading hyphen, numbers, or bullets
                clean = line.lstrip("-*0123456789. ").strip()
                if clean:
                    ideas.append(clean)

        # Guarantee exactly 3 ideas
        final_ideas = ideas[:3]
        if len(final_ideas) < 3:
            # Pad with fallback if Gemini gave fewer than 3
            fallback = [
                " FallBAck:Build a Portfolio Website with Dark Mode",
                "Create a Task Tracker using LocalStorage",
                "Design a Weather Dashboard using Public APIs"
            ]
            final_ideas += fallback[len(final_ideas):3]
        return final_ideas

    except Exception as e:
        print("❌ AI GENERATOR CRASHED ❌")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        return [
            "Build a Portfolio Website with Dark Mode",
            "Create a Task Tracker using LocalStorage",
            "Design a Weather Dashboard using Public APIs"
        ]