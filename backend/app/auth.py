import os
import sqlite3
import datetime
import time
import logging
from functools import wraps
from flask import request, g, jsonify, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token

from app.utils.validators import validate_email, validate_password

# Security: Database path relative to the app
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "users.db")

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

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Register Endpoint
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

    conn = get_db()
    cur = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO auth_users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        logger.info(f"New user registered: {email}")
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500
    finally:
        conn.close()

# Login Endpoint
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

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM auth_users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # Create a local JWT token
        access_token = create_access_token(
            identity=str(user['id']), 
            expires_delta=datetime.timedelta(days=1)
        )
        logger.info(f"User logged in: {email}")
        return jsonify({"access_token": access_token, "email": email}), 200
    
    # Record failed attempt
    record_failed_attempt(email)
    return jsonify({"error": "Invalid email or password"}), 401

# Minimal health check endpoint
@auth.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "auth service ok", "timestamp": datetime.datetime.utcnow().isoformat()}), 200

def token_required(f):
    """
    A decorator to protect Flask routes, ensuring the user is authenticated with a valid local JWT.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.lower().startswith("bearer "):
            return jsonify({"message": "Authorization header is missing or invalid"}), 401

        token = auth_header.split(" ")[1]

        try:
            # Verify the token using the app's secret key
            decoded = decode_token(token)
            user_id = decoded.get("sub")
            
            if not user_id:
                raise ValueError("User ID ('sub') not found in token.")

            g.user = {
                "id": user_id,
                "provider": "local"
            }

        except Exception as e:
            return jsonify({"message": "Token is invalid or expired", "error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated
