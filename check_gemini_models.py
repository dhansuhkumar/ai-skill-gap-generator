import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in backend/.env")
        return

    genai.configure(api_key=api_key)
    try:
        print("Listing available Gemini models:")
        for m in genai.list_models():
            if 'gemini' in m.name:
                print(f"- {m.name} (Methods: {m.supported_generation_methods})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
