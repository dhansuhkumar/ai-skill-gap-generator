
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
    # 1. Parse Input
    data = request.get_json()
    try:
        require_keys(data, ['role', 'skills'])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    role = data.get('role')
    manual_skills = data.get('skills', [])
    requested_provider = data.get('provider')
    
    fetch_videos = bool(data.get("include_youtube", False))
    max_videos = int(data.get("max_video_results", 3))

    # 2. Extract Skills (Logic-Based) - If triggered separate from upload, this endpoint usually just receives list.
    # If the user uploaded a file, the frontend probably calls /upload_resume first, gets skills, and sends them here.
    # So we just use `manual_skills` as the source of truth here which is actually the Combined list from frontend.
    
    # Validation
    if not isinstance(manual_skills, list):
        manual_skills = []
        
    print(f"LOG: Orchestrator /recommend. Role: {role}, Skills: {len(manual_skills)}")

    # 3. AI Analysis (Deep Context)

    # Import locally to be safe or rely on top level if I fixed it. 
    # The file has lazy imports. I'll do a lazy import here for safety.
    from app.ai_generator import get_unified_analysis
    
    analysis = get_unified_analysis(manual_skills, role, requested_provider=requested_provider)


    
    # 4. Orchestrate YouTube (Python Logic)
    missing_skills = analysis.get("missing_skills", [])
    
    recommended_projects = []
    if missing_skills:
        # fetch videos using recommender
        # Recommender has generate_micro_projects which calls YouTube
        recommended_projects = generate_micro_projects(missing_skills, include_videos=fetch_videos, max_results_per_skill=max_videos)
    
    # 5. Construct Response
    # The frontend expects certain keys. We need to map our new AI structure to what frontend likely consumes 
    # OR update frontend.
    # User didn't ask to update frontend structure significantly, but `ai_projects` usage might need care.
    # The AI returns 'project_ideas' (calculated) and 'alternative_roles' (new).
    # We should pass these through.
    
    response_data = {
        "message": "Analysis complete.",
        "match_percentage": analysis.get("match_percentage", 0),
        "missing_skills": missing_skills,
        "recommended_projects": recommended_projects, # Contains videos
        "ai_projects": analysis.get("project_ideas", []),
        "alternative_roles": analysis.get("alternative_roles", []),
        "learning_path": analysis.get("learning_path", []),
        # Legacy/Support fields
        "required_skills_ai": analysis.get("required_skills", []), 
        "starter_projects": [] # We could generate zips if we want, logic from before:
    }
    
    # logic for starter zips
    starter_projects = []
    for skill in missing_skills:
        try:
             # simple check if we have a template
             zip_path = create_zip(skill)
             starter_projects.append(str(zip_path))
        except Exception:
             continue
    response_data["starter_projects"] = starter_projects

    return jsonify(response_data)

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
