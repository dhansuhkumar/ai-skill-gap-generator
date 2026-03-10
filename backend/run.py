# backend/run.py
import sys
import os
from dotenv import load_dotenv
from flask import request, jsonify
from pathlib import Path

# Ensure project root is on sys.path so package imports work when running this file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

load_dotenv()

# Import local backend bootstrap (database init) after adjusting sys.path
# Prefer Supabase when configured; otherwise initialize local SQLite
supabase_client = None
_get_supabase_func = None

# Supabase is REQUIRED - validate credentials first
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("=" * 60)
    print("ERROR: Supabase credentials are REQUIRED!")
    print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
    print("=" * 60)
    raise RuntimeError("Supabase credentials missing. Cannot start application.")

# Attempt to import get_supabase function
try:
    from backend.supabase_client import get_supabase as _get_supabase_func
except ImportError:
    try:
        from supabase_client import get_supabase as _get_supabase_func
    except ImportError:
        print("=" * 60)
        print("ERROR: Supabase client module not found!")
        print("Ensure supabase_client.py exists in backend/")
        print("=" * 60)
        raise RuntimeError("Supabase client module not found")

# Initialize Supabase client
print("Attempting to initialize Supabase client...")
try:
    supabase_client = _get_supabase_func()
    if supabase_client:
        print("Supabase client initialized successfully.")
    else:
        print("Failed to initialize Supabase client (returned None).")
        raise RuntimeError("Supabase client initialization failed")
except Exception as e:
    print(f"ERROR initializing Supabase client: {e}")
    print("Ensure SUPABASE_URL and SUPABASE_KEY are correct.")
    raise RuntimeError(f"Failed to initialize Supabase client: {e}") from e

# Use explicit package imports to avoid "No module named 'app'" when running as a module
from backend.app import create_app

app = create_app()

# Add security headers to all responses
from backend.app.security_config import add_security_headers

@app.after_request
def set_response_headers(response):
    """Add content type and security headers to all responses"""
    # Set content type headers
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    elif response.mimetype == 'text/html':
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    
    # Add security headers (production-safe)
    response = add_security_headers(response)
    
    return response


if __name__ == "__main__":
    # Detect production mode
    flask_env = os.getenv("FLASK_ENV", "development")
    is_production = flask_env == "production"
   
    # Validate required environment variables
    required_vars = []
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file. Use .env.example as a template.")
        sys.exit(1)
    
    # Warn about missing optional variables
    optional_vars = {
        "GEMINI_API_KEY": "AI features will use fallback heuristics",
        "OPENAI_API_KEY": "OpenAI fallback unavailable",
        "YOUTUBE_API_KEY": "Video recommendations disabled"
    }
    
    for var, impact in optional_vars.items():
        if not os.getenv(var):
            print(f"WARNING: {var} not set - {impact}")
    
    # Production warnings
    if is_production:
        print("Starting in PRODUCTION mode")
        print("   - Debug mode: DISABLED")
        print("   - Security headers: ENABLED")
        print("   - CORS wildcard: BLOCKED")
        
        # Run with production settings
        port = int(os.getenv("PORT", 8080))
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        print("Starting in DEVELOPMENT mode")
        print("   - Debug mode: ENABLED")
        print("   - Auto-reload: ENABLED")
        
        # Run with development settings
        app.run(host="0.0.0.0", port=8080, debug=True)


