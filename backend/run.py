# backend/run.py
import sys
import os
from dotenv import load_dotenv
from flask import request, jsonify
from backend.database import init_db
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
init_db()

from app import create_app
from app.ai_generator import generate_ai_project_ideas
from app.recommender import find_missing_skills, generate_micro_projects
from app.generator import create_zip
from app.ai_skill_analyzer import find_required_and_missing_ai
from app.ai_role_matcher import find_role_matches_ai

app = create_app()

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Main endpoint used by the frontend.

    100% AI-based (no skill_db.json):

      1) AI finds required skills for the selected role.
      2) Code computes missing_skills = required - user_skills.
      3) AI recommends suitable roles (including the selected one).
      4) Code computes match % per role.
      5) Micro projects + (optionally) YouTube are built from missing_skills.
    """
    data = request.get_json() or {}
    user_skills = data.get("skills", []) or []
    target_role = data.get("role", "") or ""

    # ✅ Respect YouTube checkbox from frontend (include_youtube + max_video_results)
    fetch_videos = bool(data.get("include_youtube", False))
    max_videos = int(data.get("max_video_results", 3))

    # 1) AI project ideas (existing behavior)
    ai_projects = generate_ai_project_ideas(target_role, user_skills)
    if not isinstance(ai_projects, list):
        ai_projects = ["Error generating AI project ideas."]

    # 2) AI-based required + missing skills (NO JSON fallback)
    required_skills_ai = []
    missing = []
    try:
        ai_result = find_required_and_missing_ai(user_skills, target_role)
        required_skills_ai = ai_result.get("required_skills", []) or []
        missing = ai_result.get("missing_skills", []) or []
    except Exception as e:
        print("❌ AI skill analyzer failed in /recommend:", e)
        # If AI fails completely, we can't honestly compute gaps
        return jsonify({
            "error": "AI skill analyzer failed",
            "details": str(e),
        }), 500

    # 3) Micro-projects for missing skills (can also include YouTube links if you've wired that)
    projects = generate_micro_projects(missing, include_videos=fetch_videos, max_results=max_videos)

   

    # 5) AI-based role matches (selected role prioritized)
    job_matches = []
    try:
        job_matches = find_role_matches_ai(
            user_skills=user_skills,
            selected_role=target_role,
            required_skills_for_selected=required_skills_ai,
            max_roles=5,
        )
    except Exception as e:
        print("⚠️ AI role matcher failed:", e)
        job_matches = []

    print("Received:", data)
    print("Missing skills:", missing)
    print("Required (AI):", required_skills_ai)
    print("Job matches:", job_matches)

    # If they already match all required skills, keep your "perfect match" message
    if not missing:
        return jsonify({
            "message": "You are a perfect match for this role!",
            "role": target_role,
            "known_skills": user_skills,
            "missing_skills": [],
            "required_skills_ai": required_skills_ai,
            "recommended_projects": [],
            "ai_projects": ai_projects,
            "job_matches": job_matches,
        }), 200

    return jsonify({
        "role": target_role,
        "known_skills": user_skills,
        "missing_skills": missing,
        "required_skills_ai": required_skills_ai,
        "recommended_projects": projects,
        "ai_projects": ai_projects,
        "job_matches": job_matches,
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

