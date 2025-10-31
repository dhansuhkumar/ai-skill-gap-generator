from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta

auth = Blueprint('auth_routes', __name__)

# Dummy user store (replace with real DB later)
USERS = {
    "dhanush": "securepassword123",
    "admin": "adminpass"
}

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if USERS.get(username) != password:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username, expires_delta=timedelta(days=1))
    return jsonify({"access_token": access_token}), 200