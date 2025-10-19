from backend.app.recommender import find_missing_skills, generate_micro_projects

def test_find_missing():
    user = ["HTML","CSS"]
    missing = find_missing_skills(user, "Web Developer")
    assert "JavaScript" in missing

def test_projects():
    projects = generate_micro_projects(["SQL","React"])
    assert any(p["skill"] == "SQL" for p in projects)
