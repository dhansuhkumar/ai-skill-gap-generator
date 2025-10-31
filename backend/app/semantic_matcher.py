from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())

def match_input_to_skill(user_input):
    known_skills = load_known_skills()
    all_texts = known_skills + [user_input]
    embeddings = model.encode(all_texts)
    scores = cosine_similarity([embeddings[-1]], embeddings[:-1])[0]
    best_match = known_skills[scores.argmax()]
    return best_match if scores.max() > 0.6 else user_input