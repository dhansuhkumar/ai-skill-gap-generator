from io import BytesIO
from pdfminer.high_level import extract_text
import json
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
        print("⚠️ spaCy model not available, falling back to simple text parsing for resume extraction")
except Exception:
    spacy = None
    nlp = None
    print("⚠️ spaCy not installed; resume parsing will use simple heuristics")

def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())

def extract_skills_from_pdf(file):
    # Read the file content into memory
    file_stream = BytesIO(file.read())
    text = extract_text(file_stream)

    # If spaCy is available, use it for more accurate extraction
    known_skills = load_known_skills()
    if nlp:
        doc = nlp(text)
        tokens = set(token.text.strip().lower() for token in doc if token.pos_ in ["NOUN", "PROPN"])
        matched_skills = [skill for skill in known_skills if skill.lower() in tokens]
        return matched_skills

    # Fallback: simple substring matching against known skills
    text_lower = text.lower()
    matched = []
    for skill in known_skills:
        sk = skill.lower()
        if sk in text_lower:
            matched.append(skill)
    return matched