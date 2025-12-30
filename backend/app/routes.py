
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, request, jsonify, send_file, abort, current_app, g
from user_profile import get_user_profile, save_user_profile
from .auth import token_required

# Optional AI/ML-powered modules: import lazily or provide safe fallbacks
try:
    from app.recommender import find_missing_skills, generate_micro_projects
except Exception as _e:
    def find_missing_skills(user_skills, role):
        return []
    def generate_micro_projects(missing_skills, include_videos=False, max_results_per_skill=3):
        return []

try:
    from app.ai_skill_analyzer import find_required_and_missing_ai
except Exception as _e:
    def find_required_and_missing_ai(user_skills, role):
        # Fallback: return empty required list so caller can handle
        return {"required_skills": [], "missing_skills": []}

try:
    from app.generator import create_zip
except Exception:
    def create_zip(skill_name):
        # Fallback: just return a path-like string (no file created)
        return str((Path(__file__).parent / 'projects' / f"{skill_name}.zip").resolve())

try:
    from app.role_chat import generate_role_chat_reply
except Exception:
    def generate_role_chat_reply(role, messages):
        return "(AI role chat unavailable)"

try:
    from app.ai_generator import generate_ai_project_ideas
except Exception:
    def generate_ai_project_ideas(role, user_skills):
        return []

from app.utils.validators import require_keys
from pathlib import Path
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
    requested_provider = data.get('provider')
    
    fetch_videos = bool(data.get("include_youtube", False))
    max_videos = int(data.get("max_video_results", 3))

    print(f"LOG: /recommend hit via routes.py. Role: {role}, Fetch Videos: {fetch_videos}, Provider: {requested_provider}")

    # --- START OF AI PROJECTS SECTION ---
    ai_projects = generate_ai_project_ideas(role, user_skills, requested_provider=requested_provider)
    if not isinstance(ai_projects, list):
        ai_projects = ["Error generating AI project ideas."]
    # --- END OF AI PROJECTS SECTION ---

    # --- AI required + missing skills with fallback ---
    try:
        ai_skill_analysis = find_required_and_missing_ai(user_skills, role, requested_provider=requested_provider)
        required_skills_ai = ai_skill_analysis.get("required_skills", []) or []
        missing = ai_skill_analysis.get("missing_skills", [])
        
        if not isinstance(missing, list):
             raise ValueError("AI missing_skills invalid")
    except Exception as e:
        print("⚠️ AI skill analyzer failed, falling back to classic find_missing_skills.")
        print("Reason:", e)
        missing = find_missing_skills(user_skills, role)
        required_skills_ai = []

    if not missing:
        return jsonify({
            "message": "You are a perfect match for this role!",
            "missing_skills": [],
            "recommended_projects": [],
            "starter_projects": [],
            "ai_projects": ai_projects,
            "required_skills_ai": required_skills_ai
        }), 200
        
    projects = generate_micro_projects(missing, include_videos=fetch_videos, max_results_per_skill=max_videos)
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
    data = request.get_json() or {}
    role = (data.get("role") or "").strip()
    messages = data.get("messages") or []
    requested_provider = data.get("provider")

    if not isinstance(messages, list):
        return jsonify({"error": "messages must be a list"}), 400

    try:
        reply = generate_role_chat_reply(role, messages, requested_provider=requested_provider)
    except Exception as e:
        print("❌ Role chat generation failed:", e)
        reply = "I had trouble generating a response. Please try again."

    return jsonify({"reply": reply})

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
        return jsonify({"extracted_skills": skills})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Security: This endpoint is now protected by @token_required.
# The decorator handles JWT verification and attaches the user object to g.user.
@main.route('/save_profile', methods=['POST'])
@token_required
def save_profile():
    data = request.get_json()
    # Security: User identity is taken directly from the verified token, not from the request body.
    user_id = g.user['id']
    
    try:
        require_keys(data, ['role', 'skills', 'recommendations'])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    role = data.get('role')
    skills = data.get('skills', [])
    recommendations = data.get('recommendations', [])
    
    save_user_profile(user_id, role, skills, recommendations)
    return jsonify({"message": "Profile saved successfully"}), 200

# Security: This endpoint is protected. It fetches the profile for the authenticated user.
# The user ID is sourced from the token, preventing users from accessing other users' profiles.
@main.route('/profile', methods=['GET'])
@token_required
def profile():
    user_id = g.user['id']
    user_profile = get_user_profile(user_id)
    if user_profile:
        return jsonify(user_profile)
    return jsonify({"error": "Profile not found."}), 404

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
    # It's good practice to log the actual error for debugging.
    current_app.logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500
