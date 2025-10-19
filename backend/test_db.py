from backend.app.recommender import find_missing_skills, generate_micro_projects

user_skills = ["HTML", "CSS"]
role = "Web Developer"

missing = find_missing_skills(user_skills, role)
projects = generate_micro_projects(missing)

print("Missing Skills:", missing)
print("Suggested Projects:", projects)
