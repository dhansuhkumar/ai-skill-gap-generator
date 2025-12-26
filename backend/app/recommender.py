import os
import sys
import json
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.semantic_matcher import match_input_to_skill
from app.youtube_search import search_youtube_videos
from app.ai_generator import generate_learning_path_for_skill

# Paths
DB_PATH = Path(__file__).parent / "skill_db.json"
DATA_PATH = Path(__file__).parent / "skill_data.json"

def load_skill_db():
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        return {}
    with open(DB_PATH) as f:
        return json.load(f)

def load_skill_data():
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        return {}
    with open(DATA_PATH) as f:
        return json.load(f)

def normalize_skill(user_input, skill_data):
    user_input_lower = user_input.strip().lower()
    for skill, info in skill_data.items():
        if user_input_lower == skill.lower():
            return skill
        if any(user_input_lower == s.lower() for s in info.get("synonyms", [])):
            return skill
    return match_input_to_skill(user_input)

def find_missing_skills(user_skills, target_role):
    db = load_skill_db()
    skill_data = load_skill_data()

    required_skills = db.get(target_role, [])
    if not required_skills:
        return []

    normalized_user = [normalize_skill(s, skill_data) for s in user_skills]

    def expand_dependencies(skill, visited):
        if skill in visited:
            return []
        visited.add(skill)
        deps = skill_data.get(skill, {}).get("dependencies", [])
        result = []
        for dep in deps:
            result.append(dep)
            result.extend(expand_dependencies(dep, visited))
        return result

    expanded_required = set()
    for skill in required_skills:
        expanded_required.add(skill)
        expanded_required.update(expand_dependencies(skill, set()))

    missing_skills = [skill for skill in expanded_required if skill not in normalized_user]
    return sorted(set(missing_skills))

# ✅ FIXED: Handles include_videos logic internally, calls search correctly
LEARNING_PATH_CACHE = {}
YT_CACHE = {}


def generate_micro_projects(missing_skills, include_videos=False, max_results_per_skill=3):
    """
    Generate micro-projects + learning paths for selected skills.
    - `max_results_per_skill` is capped at 10 for safety.
    """
    projects = []
    max_results_per_skill = int(max_results_per_skill or 3)
    if max_results_per_skill > 10:
        max_results_per_skill = 10

    # Batch-request learning paths for skills not in cache to ensure a single
    # Gemini call per request (centralized in ai_generator.get_learning_paths_for_skills).
    skills_to_fetch = [s for s in missing_skills if s not in LEARNING_PATH_CACHE]
    if skills_to_fetch:
        try:
            from app.ai_generator import get_learning_paths_for_skills
            fetched = get_learning_paths_for_skills(skills_to_fetch)
            if isinstance(fetched, dict):
                for k, v in fetched.items():
                    LEARNING_PATH_CACHE[k] = v
        except Exception as e:
            # If AI fails, leave cache missing; per-skill fallbacks will be applied below
            print(f"⚠️ Batched learning path fetch failed: {e}")

    for skill in missing_skills:
        # learning path caching to avoid repeated AI calls
        lp = LEARNING_PATH_CACHE.get(skill)
        if lp is None:
            try:
                lp = generate_learning_path_for_skill(skill)
            except Exception:
                lp = {"summary": f"Learn {skill}", "steps": []}
            LEARNING_PATH_CACHE[skill] = lp

        description = lp.get("summary") or ""
        steps = lp.get("steps") or []

        videos = []
        if include_videos:
            # cache YouTube search results per skill+limit
            yk = f"{skill}:{max_results_per_skill}"
            videos = YT_CACHE.get(yk)
            if videos is None:
                try:
                    query = f"{skill} tutorial for beginners"
                    videos = search_youtube_videos(query, max_results=max_results_per_skill)
                except Exception as e:
                    print(f"⚠️ YouTube search failed for '{skill}': {e}")
                    videos = []
                YT_CACHE[yk] = videos

        projects.append({
            "skill": skill,
            "project": description,
            "learning_path_steps": steps,
            "videos": videos,
        })

    return projects

def suggest_related_skills(user_skills):
    skill_data = load_skill_data()
    related = []
    for skill in user_skills:
        canonical = normalize_skill(skill, skill_data)
        related.extend(skill_data.get(canonical, {}).get("related", []))
    return list(set(related))