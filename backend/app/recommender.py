import os
import sys
import json
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.semantic_matcher import match_input_to_skill


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
def normalize_skill(s, skill_data):
    s = s.strip().lower()
    for skill, info in skill_data.items():
        if s == skill.lower() or s in [syn.lower() for syn in info.get("synonyms", [])]:
            return skill
    return match_input_to_skill(s)


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
    if not required_skills:
        return []

    normalized_user = [normalize_skill(s, skill_data) for s in user_skills]

    # Expand dependencies
    def expand_dependencies(skill, visited):
        if skill in visited:
            return []
        visited.add(skill)
        deps = skill_data.get(skill, {}).get("dependencies", [])
        result = []
        for dep in deps:
            result.append(dep)
            result.extend(expand_dependencies(dep, visited))
        return result

    expanded_required = set()
    for skill in required_skills:
        expanded_required.add(skill)
        expanded_required.update(expand_dependencies(skill, set()))

    missing_skills = [skill for skill in expanded_required if skill not in normalized_user]
    return sorted(set(missing_skills))
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
