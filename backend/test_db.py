# backend/test_ai.py

import os
from dotenv import load_dotenv
from app.ai_generator import generate_ai_project_ideas

load_dotenv()

print("▶ Running Gemini AI Test...")

role = "AI Engineer"
skills = ["Python", "TensorFlow"]

ideas = generate_ai_project_ideas(role, skills)

print("✅ Output Type:", type(ideas))
print("✅ Generated Ideas:")
for i, idea in enumerate(ideas, 1):
    print(f"{i}. {idea}")
