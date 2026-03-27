import os
import sys

# Lazy import to avoid hard dependency at startup when env vars are not set
def get_supabase():
    """
    Get Supabase client for backend operations.
    Uses SERVICE_ROLE_KEY to bypass RLS policies.
    Falls back to SUPABASE_KEY if service role key is not available.
    """
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    
    # Prefer service role key for backend (bypasses RLS)
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        # import here to keep module import cheap when not used
        from supabase import create_client, ClientOptions
        import httpx
    except Exception:
        # If supabase client isn't installed, fail gracefully
        print("Supabase client not installed. Install 'supabase' in requirements.")
        return None

    try:
        print("Attempting to initialize Supabase client...")
        client = create_client(
            SUPABASE_URL, SUPABASE_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                postgrest_client_timeout=httpx.Timeout(10)  # 10s timeout for all operations
            )
        )
        print("Supabase client initialized successfully.")
        return client
    except Exception as e:
        print("Failed to create Supabase client:", e)
        return None
