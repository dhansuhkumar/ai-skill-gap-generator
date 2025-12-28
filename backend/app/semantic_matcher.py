import json
import difflib
from flask import current_app

def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())

def match_input_to_skill(user_input):
    """
    Matches user input to a known skill using a simple keyword-based heuristic match.
    """
    return simple_keyword_match(user_input)

def simple_keyword_match(user_input):
    """
    Simple heuristic matcher: prefers exact or substring matches to known skills.
    """
    known_skills = load_known_skills()
    ui = (user_input or "").strip().lower()
    if not ui:
        return user_input

    # Exact match
    for skill in known_skills:
        if ui == skill.lower():
            return skill

    # Substring preference (short inputs prefer exact, longer inputs may include skill name)
    for skill in known_skills:
        skl = skill.lower()
        if ui in skl or skl in ui:
            return skill

    return user_input

def match_skills(user_skills, required_skills):
    """
    Match user skills to required skills using fallback methods if embedding model is None.
    """
    model = current_app.config.get('EMBEDDING_MODEL')
    if model is None:
        # Fallback: Use set intersection and difflib for matching
        user_set = set(s.lower().strip() for s in user_skills if s)
        required_set = set(s.lower().strip() for s in required_skills if s)

        # Exact matches
        matched = user_set & required_set

        # Fuzzy matches using difflib
        fuzzy_matched = set()
        for req in required_skills:
            req_lower = req.lower().strip()
            if req_lower not in matched:
                # Find close matches
                close_matches = difflib.get_close_matches(req_lower, user_set, n=1, cutoff=0.8)
                if close_matches:
                    fuzzy_matched.add(req_lower)

        # Combine exact and fuzzy matches
        all_matched = matched | fuzzy_matched

        # Missing skills
        missing = [req for req in required_skills if req.lower().strip() not in all_matched]

        return {
            "matched_skills": list(all_matched),
            "missing_skills": missing
        }
    else:
        # Use the embedding model for matching (if available)
        # This part is not implemented as per the task, since model is None
        pass
