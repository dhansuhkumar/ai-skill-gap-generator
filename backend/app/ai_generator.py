# backend/app/ai_generator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_ai_project_ideas(role, skills):
    print(f"--- 🤖 AI Generator Started for: {role} ---")
    
    # 1. First, let's find a working model dynamically so this stops failing
    valid_model_name = "gemini-pro" # Safe fallback
    
    try:
        # List models to find the best available 'Flash' model
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Prefer 2.5, then 2.0, then 1.5
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
        # 2. Initialize with the valid name found above (NO 'model=' keyword!)
        model = genai.GenerativeModel(valid_model_name) 
        
        prompt = (
            f"I am a student wanting to be a {role}. I know {', '.join(skills)}. "
            f"Suggest 3 creative, small coding projects. "
            f"Format: Hyphen (-) at start of each line."
        )

        response = model.generate_content(prompt)
        
        ideas = [line.strip().lstrip('-* ') for line in response.text.split('\n') if line.strip()]
        final_ideas = ideas[:3]  # Take only first 3 ideas
        
        print(f"✅ AI Success: {final_ideas}")
        return final_ideas
        
    except Exception as e:
        print("❌ AI GENERATOR CRASHED ❌")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        
        return final_ideas