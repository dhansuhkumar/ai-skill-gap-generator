import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Blueprint, request, jsonify
from recommender import find_missing_skills, generate_micro_projects
from generator import create_zip
import json
import os


main = Blueprint('main', __name__)

@main.route('/')
def home():
    return jsonify({"message": "Skill Gap API is running!"})

@main.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    role = data.get('role')
    user_skills = data.get('skills', [])

    # Load database safely (use absolute path)
    db_path = os.path.join(os.path.dirname(__file__), 'skill_db.json')
    with open(db_path) as f:
        skill_db = json.load(f)

    missing = find_missing_skills(user_skills, skill_db.get(role, []))
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
    response = jsonify({
        "missing_skills": missing,
        "recommended_projects": projects,
        "starter_projects": starter_projects
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
