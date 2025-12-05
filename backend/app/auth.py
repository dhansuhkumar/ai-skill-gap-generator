import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from database import DB_NAME

auth = Blueprint('auth_routes', __name__)


def _get_db_connection():
    return sqlite3.connect(DB_NAME)


def _find_user(username: str):
    conn = _get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash FROM auth_users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "password_hash": row[2]}
    return None


def _create_user(username: str, password: str):
    password_hash = generate_password_hash(password)
    conn = _get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO auth_users (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, password_hash, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters long"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    if _find_user(username):
        return jsonify({"error": "Username already exists"}), 409

    try:
        _create_user(username, password)
    except Exception as e:
        return jsonify({"error": "Failed to create user", "details": str(e)}), 500

    return jsonify({"message": "User registered successfully"}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = _find_user(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username, expires_delta=timedelta(days=1))
    return jsonify({"access_token": access_token}), 200