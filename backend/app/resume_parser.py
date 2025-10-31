from io import BytesIO
from pdfminer.high_level import extract_text
import spacy
import json

nlp = spacy.load("en_core_web_sm")

def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())

def extract_skills_from_pdf(file):
    # Read the file content into memory
    file_stream = BytesIO(file.read())
    text = extract_text(file_stream)
    doc = nlp(text)

    # Tokenize and lowercase all nouns and proper nouns
    tokens = set(token.text.strip().lower() for token in doc if token.pos_ in ["NOUN", "PROPN"])

    # Load known skills from your database
    known_skills = load_known_skills()

    # Match only known skills
    matched_skills = []
    for skill in known_skills:
        if skill.lower() in tokens:
            matched_skills.append(skill)

    return matched_skills