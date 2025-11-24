# backend/check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print(f"✅ Key found: {api_key[:5]}... Testing connection...")
    
    try:
        print("\n--- AVAILABLE MODELS ---")
        # List all models that support 'generateContent'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        print("------------------------\n")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")