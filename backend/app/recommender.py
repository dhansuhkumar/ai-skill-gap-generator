import json
from pathlib import Path

# Path to the skill database
DB_PATH = Path(__file__).parent / "skill_db.json"

# Project templates for each skill
PROJECT_TEMPLATES = {
    "React": "Build a personal portfolio website using React.",
    "JavaScript": "Build a calculator or simple interactive web app.",
    "SQL": "Create a small database and perform queries.",
    "Python": "Write a script to analyze data or automate a task.",
    "Machine Learning": "Train a simple ML model on a sample dataset."
}

# Load skill database
def load_skill_db():
    with open(DB_PATH) as f:
        return json.load(f)

# Compare user skills with required skills for the chosen role
def find_missing_skills(user_skills, target_role):
    db = load_skill_db()
    required_skills = db.get(target_role, [])
    user_set = set(skill.strip().lower() for skill in user_skills)
    missing = [skill for skill in required_skills if skill.lower() not in user_set]
    return missing

# Generate micro-project suggestions for missing skills
def generate_micro_projects(missing_skills):
    projects = []
    for skill in missing_skills:
        description = PROJECT_TEMPLATES.get(skill, f"Build a small project to learn {skill}.")
        projects.append({"skill": skill, "project": description})
    return projects
