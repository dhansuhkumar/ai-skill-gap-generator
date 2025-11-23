import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure with your API Key (Best to put this in a .env file later!)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



def generate_ai_project_ideas(role, skills):
    """
    Uses Gemini to generate creative micro-projects.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 🟢 CRITICAL: Update the prompt to ask for a very specific, clean format.
        # This increases the chances of successful parsing.
        prompt = (
            f"I am a student wanting to be a {role}. I know {', '.join(skills)}. "
            f"Suggest 3 creative, small coding projects that will help me get hired. "
            f"Each project must be on a new line and start with a hyphen (-). "
            f"Keep descriptions short (under 15 words)."
        )

        response = model.generate_content(prompt)
        print("Gemini raw response:", response)
                # ✅ Handle different SDK versions
        text_out = getattr(response, "text", None)
     
        if not text_out and hasattr(response, "candidates"):
            text_out = response.candidates[0].content.parts[0].text

        if not text_out:
            raise ValueError("Gemini response did not contain text")


        
        # 🟢 CRITICAL FIX: Robust Parsing
        # 1. Split by newline
        # 2. Filter lines starting with '*' or '-' or a number
        # 3. Clean up leading characters
        ideas = [
            line.strip().lstrip('1234567890.-* ')
            for line in response.text.split('\n') 
            if line.strip().startswith(('-', '*')) or line.strip().startswith(tuple(str(i) for i in range(10)))
        ]
        
        # Ensure we return exactly 3 (or fewer) clean projects
        return [i for i in ideas if i][:3] 
      
        
    except Exception as e:
        # If the API call fails (Quota, invalid key, or any crash), return the default list.
        print(f"AI Error: {e}")
        return [
            "Build a Portfolio Website with Dark Mode",
            "Create a Task Tracker using LocalStorage",
            "Design a Weather Dashboard using Public APIs"
        ]
    