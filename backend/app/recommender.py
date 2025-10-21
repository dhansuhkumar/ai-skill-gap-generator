import os
import json
from pathlib import Path

# Paths
DB_PATH = Path(__file__).parent / "skill_db.json"
DATA_PATH = Path(__file__).parent / "skill_data.json"

# Project templates
PROJECT_TEMPLATES = {
    "React": "Build a personal portfolio website using React.",
    "JavaScript": "Build a calculator or simple interactive web app.",
    "SQL": "Create a small database and perform queries.",
    "Python": "Write a script to analyze data or automate a task.",
    "Machine Learning": "Train a simple ML model on a sample dataset."
}

# Load databases
def load_skill_db():
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        return {}
    with open(DB_PATH) as f:
        return json.load(f)

def load_skill_data():
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        return {}  # return empty dict instead of crashing
    with open(DATA_PATH) as f:
        return json.load(f)

# Normalize skill names (handle synonyms)
def normalize_skill(user_input, skill_data):
    user_input_lower = user_input.strip().lower()
    for skill, info in skill_data.items():
        if user_input_lower == skill.lower():
            return skill
        if any(user_input_lower == s.lower() for s in info.get("synonyms", [])):
            return skill
    return user_input  # fallback

# Compare user skills with required skills
def find_missing_skills(user_skills, target_role):
    db = load_skill_db()
    skill_data = load_skill_data()

    required_skills = db.get(target_role, [])
    normalized_user = [normalize_skill(s, skill_data) for s in user_skills]

    matched_skills = [skill for skill in required_skills if skill not in normalized_user]
    return matched_skills

    if not matched_skills:
        return None
    missing = [skill for skill in required_skills if skill not in matched_skills]
    return missing

# Generate micro-project suggestions
def generate_micro_projects(missing_skills):
    projects = []
    for skill in missing_skills:
        description = PROJECT_TEMPLATES.get(skill, f"Build a small project to learn {skill}.")
        projects.append({"skill": skill, "project": description})
    return projects

# Suggest related skills (optional extra feature)
def suggest_related_skills(user_skills):
    skill_data = load_skill_data()
    related = []
    for skill in user_skills:
        canonical = normalize_skill(skill, skill_data)
        related.extend(skill_data.get(canonical, {}).get("related", []))
    return list(set(related))