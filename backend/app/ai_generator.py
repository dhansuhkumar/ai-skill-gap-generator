# backend/app/ai_generator.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def _select_model_fallback(default_name: str = "gemini-pro") -> str:
    """
    Small helper to pick a reasonable Gemini model, with a safe fallback.
    """
    model_name = default_name
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
    except Exception as e:
        print(f"⚠️ Model list failed, using default '{model_name}': {e}")
    return model_name


def generate_ai_project_ideas(role, skills):
    """
    Generate AI-based project ideas for the given role and skills.

    🧠 External behavior (NO CHANGE):
        - Returns a list of 3 strings (project titles) just like before.

    🧠 Internal upgrade:
        - Asks Gemini for a JSON array of objects:
          [
            {
              "title": "...",
              "description": "...",
              "difficulty": "beginner|intermediate|advanced",
              "youtube_search_query": "..."
            },
            ...
          ]

        - Parses that JSON safely.
        - Extracts just the 'title' field for the current API output.
        - Falls back to your OLD hyphen-line parsing if JSON fails.
        - If everything fails, returns your old hardcoded 3 defaults.
    """
    print(f"--- 🤖 AI Generator Started for: {role} ---")

    valid_model_name = _select_model_fallback()
    print(f"🔍 Selected Model: {valid_model_name}")

    # ✅ 2) Helper: your old-style fallback parser (kept for safety)
    def _fallback_text_to_titles(raw_text: str):
        """
        Use your previous hyphen-line logic to extract up to 3 ideas.
        """
        ideas = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("-"):
                # Remove leading hyphen, numbers, or bullets
                clean = line.lstrip("-*0123456789. ").strip()
                if clean:
                    ideas.append(clean)

        final_ideas = ideas[:3]
        if len(final_ideas) < 3:
            # Same fallback list you had before
            fallback = [
                "Build a Portfolio Website with Dark Mode",
                "Create a Task Tracker using LocalStorage",
                "Design a Weather Dashboard using Public APIs"
            ]
            final_ideas += fallback[len(final_ideas):3]
        return final_ideas

    # ✅ 3) Try the NEW structured-JSON prompt first
    try:
        model = genai.GenerativeModel(valid_model_name)

        # 🧾 New, stronger prompt: JSON output with rich data.
        prompt = (
            "You are a senior software engineer helping a student choose small projects.\n\n"
            f"Target role: {role}\n"
            f"Current skills: {', '.join(skills) if skills else 'None listed'}\n\n"
            "Generate EXACTLY 3 project ideas as a JSON array.\n"
            "NO markdown, NO explanation, JSON ONLY.\n\n"
            "JSON format:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"short project title, 6-12 words\",\n"
            "    \"description\": \"1-2 sentence explanation of what they will build\",\n"
            "    \"difficulty\": \"beginner\" | \"intermediate\" | \"advanced\",\n"
            "    \"youtube_search_query\": \"best tutorial search query to learn this project\"\n"
            "  }\n"
            "]\n"
        )

        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "").strip()
        print("🔍 Raw Gemini output (structured attempt):", raw_text)

        # Try to extract JSON array from the text
        start = raw_text.find("[")
        end = raw_text.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("No JSON array found in model output")

        json_str = raw_text[start:end + 1]
        projects = json.loads(json_str)

        if not isinstance(projects, list) or len(projects) == 0:
            raise ValueError("Parsed JSON is not a non-empty list")

        # Extract just the titles for now (to keep existing API behavior)
        titles = []
        for p in projects:
            if isinstance(p, dict):
                title = p.get("title") or p.get("name") or ""
                if title:
                    titles.append(title.strip())

        titles = [t for t in titles if t]

        # Ensure exactly 3 titles
        titles = titles[:3]
        if len(titles) < 3:
            # Pad using the fallback logic on the original text
            more = _fallback_text_to_titles(raw_text)
            # merge, avoiding duplicates
            for t in more:
                if t not in titles and len(titles) < 3:
                    titles.append(t)

        print("✅ Final AI Project Titles:", titles)
        return titles

    except Exception as e:
        print("⚠️ Structured JSON generation failed, falling back to old-style parsing.")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")

        # Try old behavior: hyphen-based lines
        try:
            model = genai.GenerativeModel(valid_model_name)

            old_prompt = (
                f"I am a student wanting to be a {role}. I know {', '.join(skills)}. "
                f"Suggest exactly 3 creative, small coding project titles. "
                f"Each project must be a single short line starting with a hyphen (-). "
                f"No explanations, no goals, no extra text — just the titles."
            )

            old_response = model.generate_content(old_prompt)
            old_raw_text = getattr(old_response, "text", "").strip()
            print("🔍 Raw Gemini output (fallback mode):", old_raw_text)

            return _fallback_text_to_titles(old_raw_text)

        except Exception as inner_e:
            print("❌ AI GENERATOR CRASHED EVEN IN FALLBACK ❌")
            print(f"Error Type: {type(inner_e).__name__}")
            print(f"Error Message: {inner_e}")
            # Absolute last-resort fallback (your old static list)
            return [
                "Build a Portfolio Website with Dark Mode",
                "Create a Task Tracker using LocalStorage",
                "Design a Weather Dashboard using Public APIs"
            ]


def generate_learning_path_for_skill(skill: str):
    """
    Generate an AI-based learning path for a single skill.

    Returns a dict:
        {
          "summary": "Short overview of why this skill matters and how to learn it",
          "steps": ["Step 1 ...", "Step 2 ...", ...]
        }
    """
    if not skill:
        return {"summary": "", "steps": []}

    model_name = _select_model_fallback()
    print(f"🔍 Learning-path model for '{skill}': {model_name}")

    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"""
You are a friendly tech mentor.

Skill: "{skill}"

Create a focused learning path for an aspiring developer who wants to get job-ready using this skill.

Return JSON ONLY in this exact format (no markdown, no extra text):
{{
  "summary": "1–2 sentence overview of why this skill matters and what they will be able to do with it.",
  "steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
    "Step 4: ... (optional)",
    "Step 5: ... (optional)"
  ]
}}
"""
        response = model.generate_content(prompt)
        raw = getattr(response, "text", "").strip()
        print(f"🔍 Raw learning-path output for {skill}:", raw)

        # Extract JSON object
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object in learning-path output")

        obj = json.loads(raw[start : end + 1])
        if not isinstance(obj, dict):
            raise ValueError("Learning-path JSON is not an object")

        summary = (obj.get("summary") or "").strip()
        steps = obj.get("steps") or []
        if not isinstance(steps, list):
            steps = []
        steps = [str(s).strip() for s in steps if str(s).strip()]

        return {
            "summary": summary,
            "steps": steps,
        }
    except Exception as e:
        print(f"⚠️ Learning-path generation failed for '{skill}': {e}")
        return {
            "summary": f"Aim to build a few small, practical projects using {skill} and follow high-quality tutorials.",
            "steps": [],
        }
