from io import BytesIO
from pdfminer.high_level import extract_text
import json

def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())

def extract_skills_from_pdf(file):
    # Read the file content into memory
    file_stream = BytesIO(file.read())
    text = extract_text(file_stream)
    known_skills = load_known_skills()

    # Simple substring matching against known skills
    text_lower = text.lower()
    matched = []
    for skill in known_skills:
        sk = skill.lower()
        if sk in text_lower:
            matched.append(skill)
    return matched