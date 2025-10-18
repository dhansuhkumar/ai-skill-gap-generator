from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import find_missing_skills, generate_micro_projects
from generator import create_zip

app = Flask(__name__)
CORS(app)  # <-- This line allows requests from frontend

@app.route('/')
def home():
    return "Skill Gap & Micro-Project Generator is Running!"

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json or {}
    user_skills = data.get("skills", [])
    target_role = data.get("role", "")
    
    missing = find_missing_skills(user_skills, target_role)
    projects = generate_micro_projects(missing)
    
    # Generate starter project zips for missing skills
    zip_files = [str(create_zip(skill)) for skill in missing]
    
    return jsonify({
        "role": target_role,
        "known_skills": user_skills,
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": zip_files
    })


if __name__ == "__main__":
    app.run(debug=True)
