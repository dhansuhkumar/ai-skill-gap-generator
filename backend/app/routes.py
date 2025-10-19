from flask import Blueprint, request, jsonify
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

    return jsonify({
        "missing_skills": missing,
        "recommended_projects": projects
    })
