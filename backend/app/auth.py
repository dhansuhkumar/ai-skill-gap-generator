
import os
from functools import wraps
import jwt
from flask import request, g, jsonify
import requests

# Security: Fetch the Supabase URL from environment variables to avoid hardcoding secrets.
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Note: The SUPABASE_KEY here is the anon key, which is public and safe to use in a browser.
# For server-to-server interactions, you would use the service_role key.
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# In-memory cache for Supabase public keys (JWKS)
# Caching keys prevents fetching them on every request, reducing latency.
_jwks_cache = {}

def _get_public_key(kid):
    """
    Fetches Supabase public keys (JWKS) and returns the key matching the given Key ID (kid).
    """
    global _jwks_cache
    # Check cache first
    if _jwks_cache and kid in _jwks_cache:
        return _jwks_cache[kid]

    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set.")

    # Security: JWKS endpoint is a standard way to securely fetch public keys for JWT verification.
    jwks_url = f"{SUPABASE_URL}/auth/v1/jwks"
    try:
        jwks = requests.get(jwks_url, timeout=5).json()
    except requests.exceptions.RequestException as e:
        # If we can't fetch the keys, we can't verify tokens.
        raise ConnectionError(f"Could not fetch Supabase JWKS: {e}") from e

    # Reset and rebuild cache
    _jwks_cache = {}
    public_key = None
    for key in jwks["keys"]:
        # Security: Convert the JWK to a format the 'pyjwt' library can use.
        _jwks_cache[key["kid"]] = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        if key["kid"] == kid:
            public_key = _jwks_cache[key["kid"]]

    if not public_key:
        # Security: If the token's 'kid' doesn't match any of our public keys, it's a forgery.
        raise ValueError("Matching public key not found for the given kid.")
    
    return public_key


def token_required(f):
    """
    A decorator to protect Flask routes, ensuring the user is authenticated with a valid Supabase JWT.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("authorization")

        # Security: Ensure the Authorization header is present and correctly formatted as "Bearer <token>".
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return jsonify({"message": "Authorization header is missing or invalid"}), 401

        token = auth_header.split(" ")[1]

        try:
            # Security: First, get the token's header to find the Key ID (kid) without verifying the signature.
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise ValueError("'kid' not found in token header.")

            public_key = _get_public_key(kid)

            # Security: Now, decode and verify the token's signature, expiration, and audience.
            # The 'audience' claim ensures the token was issued for our application.
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="authenticated",
            )
            
            # Standardize the user object and attach it to the request context ('g').
            # 'g' is a thread-safe object for storing data during a single request.
            g.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "provider": "supabase"
            }
            if not g.user["id"]:
                raise ValueError("User ID ('sub') not found in token.")

        except jwt.ExpiredSignatureError:
            # Security: Reject tokens that have passed their expiration time.
            return jsonify({"message": "Token has expired"}), 401
        except (jwt.InvalidTokenError, ValueError) as e:
            # Security: Catch all other JWT-related errors, like signature mismatches or formatting issues.
            return jsonify({"message": "Token is invalid", "error": str(e)}), 401
        except ConnectionError as e:
            # Handle failure to connect to Supabase to get keys
            return jsonify({"message": "Cannot verify token", "error": str(e)}), 503


        return f(*args, **kwargs)

    return decorated
