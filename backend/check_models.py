import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    try:
        client = genai.Client(api_key=api_key)
        print(f"✅ Key found: {api_key[:5]}... Testing connection...")
        
        # Test a simple generation to confirm it's NOT a 404
        model_id = 'gemini-2.5-flash'
        print(f"Testing model: {model_id}")
        response = client.models.generate_content(model=model_id, contents="Hello")
        print(f"✅ Connection test successful! Response: {response.text[:10]}...")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == '__main__':
    main()