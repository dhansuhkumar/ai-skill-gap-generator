import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
import pytest
from recommender import find_missing_skills, generate_micro_projects

def test_find_missing_skills_frontend():
    user_skills = ["js", "html5"]
    role = "Web Developer"
    missing = find_missing_skills(user_skills, role)
    assert "CSS" in missing
    assert "React" in missing

def test_generate_micro_projects():
    skills = ["React", "CSS"]
    projects = generate_micro_projects(skills)
    assert len(projects) == 2
    assert projects[0]["skill"] == "React"