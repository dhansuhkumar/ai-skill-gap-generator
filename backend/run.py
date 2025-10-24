import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai_generator import generate_ai_project_ideas
from app.recommender import find_missing_skills, generate_micro_projects
from app.generator import create_zip
from app.__init__ import create_app
from database import init_db

from flask import Flask, request, jsonify
from flask_cors import CORS
init_db()
app = create_app()
from app.routes import main 


@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    user_skills = data.get("skills", [])
    target_role = data.get("role", "")
    ai_projects = generate_ai_project_ideas(target_role,user_skills)
    missing = find_missing_skills(user_skills, target_role)
    projects = generate_micro_projects(missing)
    
    zip_files = [str(create_zip(skill)) for skill in missing]
    
    print("Received:", data)
    print("Response:", {"missing": missing, "projects": projects, "ai_projects": ai_projects})

    return jsonify({
        "role": target_role,
        "known_skills": user_skills,
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": zip_files,
        "ai_projects": ai_projects
    })
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


