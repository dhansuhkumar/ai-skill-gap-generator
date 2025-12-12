import json


def load_known_skills():
    with open("backend/app/skill_data.json") as f:
        data = json.load(f)
    return list(data.keys())


def match_input_to_skill(user_input):
    """Simple heuristic matcher: prefers exact or substring matches to known skills.

    This avoids importing heavy ML libraries at module import time. If you want
    embed-based matching, consider adding a separate service or enabling it
    explicitly (not enabled by default).
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