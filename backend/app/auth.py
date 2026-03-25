import os
import time
import logging
from functools import wraps
from flask import request, g, jsonify, Blueprint, current_app

from .utils.validators import validate_email, validate_password

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory, use Redis for production)
_rate_limit_store = {}
LOGIN_ATTEMPTS_LIMIT = 5  # Max login attempts
LOGIN_WINDOW_SECONDS = 300  # 5 minute window

def get_rate_limit_key(email):
    """Generate rate limit key based on IP and email."""
    ip = request.remote_addr or "unknown"
    return f"{ip}:{email}"

def check_rate_limit(email):
    """
    Check if email/IP is rate limited.
    Returns (is_allowed, remaining_seconds)
    """
    key = get_rate_limit_key(email)
    now = time.time()
    
    # Clean old entries
    for k, v in list(_rate_limit_store.items()):
        if now - v['window_start'] > LOGIN_WINDOW_SECONDS:
            del _rate_limit_store[k]
    
    if key in _rate_limit_store:
        entry = _rate_limit_store[key]
        if now - entry['window_start'] < LOGIN_WINDOW_SECONDS:
            if entry['attempts'] >= LOGIN_ATTEMPTS_LIMIT:
                remaining = int(LOGIN_WINDOW_SECONDS - (now - entry['window_start']))
                return False, remaining
        else:
            # Window expired, reset
            del _rate_limit_store[key]
    
    return True, 0

def record_failed_attempt(email):
    """Record a failed login attempt."""
    key = get_rate_limit_key(email)
    now = time.time()
    
    if key not in _rate_limit_store:
        _rate_limit_store[key] = {'attempts': 1, 'window_start': now}
    else:
        _rate_limit_store[key]['attempts'] += 1
    
    logger.warning(f"Failed login attempt for {email}, attempts: {_rate_limit_store[key]['attempts']}")

# Initialize the Blueprint
auth = Blueprint('auth', __name__)

# Register Endpoint - Supabase Auth
@auth.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    email = data.get('email')
    password = data.get('password')

    # Validate email format
    valid, email_error = validate_email(email)
    if not valid:
        return jsonify({"error": email_error}), 400

    # Validate password strength
    valid, password_error = validate_password(password)
    if not valid:
        return jsonify({"error": password_error}), 400

    # Use Supabase Auth to register
    try:
        supabase = current_app.supabase
        if not supabase:
            return jsonify({"error": "Authentication service unavailable"}), 503
        
        # Sign up with Supabase
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            logger.info(f"New user registered via Supabase: {email}")
            
            # Create profile entry in profiles table
            try:
                supabase.table('profiles').insert({
                    "id": response.user.id
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to create profile for {email}: {e}")
            
            return jsonify({
                "message": "User registered successfully",
                "user_id": response.user.id,
                "email": email
            }), 201
        else:
            return jsonify({"error": "Registration failed"}), 500
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Supabase registration error: {error_msg}")
        
        # Handle common Supabase errors
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            return jsonify({"error": "Email already exists"}), 409
        
        return jsonify({"error": "Registration failed"}), 500

# Login Endpoint - Supabase Auth
@auth.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Check rate limit
    allowed, remaining = check_rate_limit(email)
    if not allowed:
        logger.warning(f"Rate limit exceeded for {email}, retry in {remaining}s")
        return jsonify({
            "error": "Too many login attempts. Please try again later.",
            "retry_after": remaining
        }), 429

    # Use Supabase Auth to login
    try:
        supabase = current_app.supabase
        if not supabase:
            return jsonify({"error": "Authentication service unavailable"}), 503
        
        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session:
            logger.info(f"User logged in via Supabase: {email}")
            
            # Return Supabase session token
            return jsonify({
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }), 200
        else:
            # Record failed attempt
            record_failed_attempt(email)
            return jsonify({"error": "Invalid email or password"}), 401
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Supabase login error: {error_msg}")
        
        # Record failed attempt
        record_failed_attempt(email)

        # Handle common Supabase errors
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return jsonify({"error": "Invalid email or password"}), 401

        # Handle timeout errors
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            return jsonify({"error": "Authentication service is slow. Please try again."}), 503

        return jsonify({"error": "Login failed"}), 500

# Health check endpoint
@auth.route('/ping', methods=['GET'])
def ping():
    import datetime
    return jsonify({
        "status": "auth service ok", 
        "provider": "supabase",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

def token_required(f):
    """
    Decorator to protect Flask routes using Supabase token verification.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Let CORS preflight requests pass through without auth
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.lower().startswith("bearer "):
            return jsonify({"message": "Authorization header is missing or invalid"}), 401

        token = auth_header.split(" ")[1]

        try:
            supabase = current_app.supabase
            if not supabase:
                return jsonify({"message": "Authentication service unavailable"}), 503
            
            # Verify token with Supabase
            user_response = supabase.auth.get_user(token)
            
            if not user_response or not user_response.user:
                return jsonify({"message": "Token is invalid or expired"}), 401

            # Store user info in request context
            g.user = {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "provider": "supabase"
            }

        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return jsonify({"message": "Token is invalid or expired"}), 401

        return f(*args, **kwargs)

    return decorated
