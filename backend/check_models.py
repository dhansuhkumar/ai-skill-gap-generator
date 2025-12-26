# backend/check_models.py
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        import google.generativeai as genai
    except Exception as e:
        print("⚠️ google.generativeai import failed:", e)
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: API Key not found in .env")
        return

    try:
        genai.configure(api_key=api_key)
        print(f"✅ Key found: {api_key[:5]}... Testing connection...")
        print("\n--- AVAILABLE MODELS ---")
        for m in genai.list_models():
            if 'generateContent' in getattr(m, 'supported_generation_methods', []):
                print(f"- {getattr(m, 'name', '<unknown>')}")
        print("------------------------\n")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")


if __name__ == '__main__':
    main()