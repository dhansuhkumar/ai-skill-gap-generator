import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, request, jsonify, send_file, abort
from user_profile import get_user_profile, save_user_profile
from app.recommender import find_missing_skills, generate_micro_projects
from app.generator import create_zip
from app.ai_generator import generate_ai_project_ideas
from app.utils.validators import require_keys

from flask_jwt_extended import jwt_required, get_jwt_identity,create_access_token
import json
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from app.resume_parser import extract_skills_from_pdf

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return jsonify({"message": "Skill Gap API is running!"})
@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')

    # TEMP: Hardcoded user for testing
    if user_id == "dhanush" and password == "test123":
        access_token = create_access_token(identity="dhanush123")
        return jsonify(token=access_token), 200

    return jsonify({"error": "Invalid credentials"}), 401



@main.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    try:
        require_keys(data, ['role', 'skills'])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    role = data.get('role')
    user_skills = data.get('skills', [])
    ai_projects = generate_ai_project_ideas(role, user_skills)

    # Load database safely (use absolute path)
    db_path = os.path.join(os.path.dirname(__file__), 'skill_db.json')
    with open(db_path) as f:
        skill_db = json.load(f)

    missing = find_missing_skills(user_skills, role)
    projects = generate_micro_projects(missing)
    starter_projects = [str(create_zip(skill)) for skill in missing]
    if missing is None:
        return jsonify({
            "error": "No matching skills found for this role.",
            "missing_skills": [],
            "recommended_projects": [],
            "starter_projects": []
        }),400
    return jsonify({
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": starter_projects 
    })
    
    return jsonify({
    "known_skills": known,
    "missing_skills": missing,
    "recommended_projects": projects,
    "starter_projects": starter_projects,
    "ai_projects": ai_projects
})
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        skills = extract_skills_from_pdf(file)  # ✅ Use file object
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

   # ✅ Serve starter ZIP files via API
PROJECTS_DIR = Path(__file__).parent / "projects"

@main.route('/api/starter/<skill>', methods=['GET'])
def get_starter(skill):
    zip_file = PROJECTS_DIR / f"{skill.replace(' ', '_')}.zip"
    if not zip_file.exists():
        abort(404)
    return send_file(zip_file, as_attachment=True, mimetype='application/zip')
