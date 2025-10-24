import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Blueprint, request, jsonify
from recommender import find_missing_skills, generate_micro_projects
from generator import create_zip
from ai_generator import generate_ai_project_ideas
from user_profile import get_user_profile, save_user_profile
import json
import os


main = Blueprint('main_routes', __name__)

@main.route('/')
def home():
    return jsonify({"message": "Skill Gap API is running!"})

@main.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
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
    response = jsonify({
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
@main.route('/save_profile', methods=['POST'])
def save_profile():
    data = request.get_json()
    user_id = data.get('user_id')
    role = data.get('role')
    skills = data.get('skills', [])
    recommendations = data.get('recommendations', [])
    save_user_profile(user_id, role, skills, recommendations)
    return jsonify({"message": "Profile saved successfully"}), 200

@main.route('/profile/<user_id>', methods=['GET'])
def profile(user_id):
    profile = get_user_profile(user_id)
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found."}), 404

    save_user_profile(user_id, role, skills, recommendations)
    return jsonify({"message": "Profile saved successfully."})

    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
