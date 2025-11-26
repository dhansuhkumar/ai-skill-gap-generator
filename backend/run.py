# backend/run.py
import sys
import os
from dotenv import load_dotenv
from flask import request, jsonify
from backend.database import init_db


# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
init_db()

from app import create_app
from app.ai_generator import generate_ai_project_ideas
from app.recommender import find_missing_skills, generate_micro_projects
from app.generator import create_zip
from app.ai_skill_analyzer import find_required_and_missing_ai




app = create_app()

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Main recommend endpoint used by the frontend.

    Now uses AI to:
      1) Generate required/core skills for the role.
      2) Compute missing_skills = required - user_skills (in code).

    Output shape remains the same as before, plus an extra
    "required_skills_ai" field that frontend can use if it wants.
    """
    data = request.get_json() or {}
    user_skills = data.get("skills", []) or []
    target_role = data.get("role", "") or ""

    # 🤖 AI-generated project ideas (unchanged behavior: list of 3 titles)
    ai_projects = generate_ai_project_ideas(target_role, user_skills)
    if not isinstance(ai_projects, list):
        ai_projects = ["Error generating AI project ideas."]

    # 🤖 AI-based required + missing skills, with safe fallback
    required_skills_ai = []
    try:
        ai_result = find_required_and_missing_ai(user_skills, target_role)
        required_skills_ai = ai_result.get("required_skills", []) or []
        missing = ai_result.get("missing_skills", []) or []

        # If AI returns nothing useful, force fallback
        if not isinstance(missing, list) or len(missing) == 0:
            raise ValueError("AI missing_skills invalid or empty")
    except Exception as e:
        print("⚠️ AI skill analyzer failed in /recommend, using classic find_missing_skills.")
        print("Reason:", e)
        missing = find_missing_skills(user_skills, target_role)
        required_skills_ai = []

    # If still no missing skills, keep your original nice message
    if not missing:
        return jsonify({
            "message": "You are a perfect match for this role!",
            "role": target_role,
            "known_skills": user_skills,
            "missing_skills": [],
            "recommended_projects": [],
            "starter_projects": [],
            "ai_projects": ai_projects,
            "required_skills_ai": required_skills_ai
        }), 200

    # Project suggestions & starter zips
    projects = generate_micro_projects(missing)
    zip_files = [str(create_zip(skill)) for skill in missing]

    print("Received:", data)
    print("Response:", {
        "missing": missing,
        "projects": projects,
        "ai_projects": ai_projects,
        "required_skills_ai": required_skills_ai
    })

    return jsonify({
        "role": target_role,
        "known_skills": user_skills,
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": zip_files,
        "ai_projects": ai_projects,
        # New (for frontend to display core role skills if desired)
        "required_skills_ai": required_skills_ai
    })

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Proceed with saving or processing
    return jsonify({'message': 'Resume uploaded successfully'}), 200

@app.after_request
def set_response_headers(response):
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    elif response.mimetype == 'text/html':
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Skill Gap API is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

