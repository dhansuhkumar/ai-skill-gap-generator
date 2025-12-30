
import os
import sqlite3
import datetime
from functools import wraps
from flask import request, g, jsonify, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token

# Security: Database path relative to the app
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "users.db")

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
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO auth_users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    finally:
        conn.close()

# Login Endpoint
@auth.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM auth_users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # Create a local JWT token
        access_token = create_access_token(identity=str(user['id']), expires_delta=datetime.timedelta(days=1))
        return jsonify({"access_token": access_token, "username": username}), 200
    
    return jsonify({"error": "Invalid username or password"}), 401

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

