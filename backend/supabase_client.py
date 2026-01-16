import os
import sys

# Lazy import to avoid hard dependency at startup when env vars are not set
def get_supabase():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        # import here to keep module import cheap when not used
        from supabase import create_client
    except Exception:
        # If supabase client isn't installed, fail gracefully
        print("Supabase client not installed. Install 'supabase' in requirements.")
        return None

    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception as e:
        print("Failed to create Supabase client:", e)
        return None
