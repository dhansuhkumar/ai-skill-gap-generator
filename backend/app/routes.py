import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, request, jsonify, send_file, abort, current_app
from user_profile import get_user_profile, save_user_profile
from app.recommender import find_missing_skills, generate_micro_projects
from app.ai_skill_analyzer import find_required_and_missing_ai
from app.generator import create_zip
from app.role_chat import generate_role_chat_reply
from app.ai_generator import generate_ai_project_ideas
from app.utils.validators import require_keys
from flask import send_file, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from app.resume_parser import extract_skills_from_pdf

main = Blueprint('main', __name__)
PROJECTS_DIR = Path(__file__).parent / "projects"

@main.route('/')
def home():
    return jsonify({"message": "Skill Gap API is running!"})

@main.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    try:
        require_keys(data, ['role', 'skills'])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    role = data.get('role')
    user_skills = data.get('skills', [])
    
    # ✅ CORRECT: Read the 'include_youtube' flag sent by frontend
    fetch_videos = bool(data.get("include_youtube", False))
    max_videos = int(data.get("max_video_results", 3))

    print(f"LOG: /recommend hit via routes.py. Role: {role}, Fetch Videos: {fetch_videos}")

    # --- START OF AI PROJECTS SECTION ---
    ai_projects = []
    ai_projects = generate_ai_project_ideas(role, user_skills)
    if not isinstance(ai_projects, list):
        ai_projects = ["Error generating AI project ideas."]
    # --- END OF AI PROJECTS SECTION ---

    # --- AI required + missing skills with fallback ---
    required_skills_ai = []
    try:
        ai_skill_analysis = find_required_and_missing_ai(user_skills, role)
        required_skills_ai = ai_skill_analysis.get("required_skills", []) or []
        missing = ai_skill_analysis.get("missing_skills", [])
        
        if not isinstance(missing, list) or not missing:
            # Fallback if AI returns valid JSON but empty content that shouldn't be empty
            # But technically empty missing skills IS valid (perfect match), so we proceed
            if not missing and not required_skills_ai: 
                 raise ValueError("AI missing_skills invalid")
    except Exception as e:
        print("⚠️ AI skill analyzer failed, falling back to classic find_missing_skills.")
        print("Reason:", e)
        missing = find_missing_skills(user_skills, role)

    
    # If perfect match
    if not missing:
        return jsonify({
            "message": "You are a perfect match for this role!",
            "missing_skills": [],
            "recommended_projects": [],
            "starter_projects": [],
            "ai_projects": ai_projects,
            "required_skills_ai": required_skills_ai
        }), 200
        
    # ✅ CORRECT: Pass the include_videos flag to recommender
    projects = generate_micro_projects(missing, include_videos=fetch_videos, max_results=max_videos)
    
    starter_projects = [str(create_zip(skill)) for skill in missing] 
    
    return jsonify({
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": starter_projects,
        "ai_projects": ai_projects,
        "required_skills_ai": required_skills_ai
    })


@main.route("/api/role-chat", methods=["POST"])
def role_chat():
    """
    Lightweight role-aware chat endpoint used by the frontend chatbox.

    Expects JSON:
      {
        "role": "Frontend Developer",
        "messages": [
          {"sender": "user", "text": "..."},
          {"sender": "ai", "text": "..."}
        ]
      }

    Returns JSON:
      { "reply": "..." }
    """
    data = request.get_json() or {}
    role = (data.get("role") or "").strip()
    messages = data.get("messages") or []

    if not isinstance(messages, list):
        return jsonify({"error": "messages must be a list"}), 400

    try:
        reply = generate_role_chat_reply(role, messages)
    except Exception as e:
        print("❌ Role chat generation failed:", e)
        return jsonify({
            "reply": "I had trouble generating a response just now. Please try again in a moment."
        }), 200

    return jsonify({"reply": reply})

# upload and parse resume
@main.route("/upload_resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    try:
        skills = extract_skills_from_pdf(file)
        print("Extracted skills:", skills)
        return jsonify({"extracted_skills": skills})
    except Exception as e:
        print("Error extracting skills:", str(e))
        return jsonify({"error": str(e)}), 500

# save user profile
@main.route('/save_profile', methods=['POST'])
@jwt_required()
def save_profile():
    data = request.get_json()
    user_id = get_jwt_identity()
    try:
        require_keys(data, ['role', 'skills', 'recommendations'])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    role = data.get('role')
    skills = data.get('skills', [])
    recommendations = data.get('recommendations', [])
    save_user_profile(user_id, role, skills, recommendations)
    return jsonify({"message": "Profile saved successfully"}), 200

# retrieve user profile
@main.route('/profile/<user_id>', methods=['GET'])
@jwt_required()
def profile(user_id):
    profile = get_user_profile(user_id)
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found."}), 404

# Serve starter ZIP files
@main.route('/api/starter/<skill>', methods=['GET'])
def get_starter(skill):
    zip_file = PROJECTS_DIR / f"{skill.replace(' ', '_')}.zip"
    if not zip_file.exists():
        abort(404)
    return send_file(zip_file, as_attachment=True, mimetype='application/zip')

@main.app_errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@main.app_errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404

@main.app_errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500