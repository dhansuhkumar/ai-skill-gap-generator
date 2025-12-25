# backend/run.py
import sys
import os
from dotenv import load_dotenv
from flask import request, jsonify
from pathlib import Path

# Ensure project root is on sys.path so package imports work when running this file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

load_dotenv()

# Import local backend bootstrap (database init) after adjusting sys.path
from backend.database import init_db
init_db()

# Use explicit package imports to avoid "No module named 'app'" when running as a module
from backend.app import create_app
from backend.app.ai_generator import generate_ai_project_ideas, get_unified_analysis
from backend.app import ai_generator as _ai_gen_module
from backend.app.recommender import generate_micro_projects, find_missing_skills
from backend.app.ai_role_matcher import _compute_match

app = create_app()

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Main endpoint used by the frontend.

    100% AI-based (no skill_db.json):

      1) AI finds required skills for the selected role.
      2) Code computes missing_skills = required - user_skills.
      3) AI recommends suitable roles (including the selected one).
      4) Code computes match % per role.
      5) Micro projects + (optionally) YouTube are built from missing_skills.
    """
    data = request.get_json() or {}
    user_skills = data.get("skills", []) or []
    target_role = data.get("role", "") or ""

    # ✅ Respect YouTube checkbox from frontend (include_youtube + max_video_results)
    fetch_videos = bool(data.get("include_youtube", False))
    max_videos = int(data.get("max_video_results", 3))

    # Attempt unified AI analysis (single Gemini call) with cache detection
    required_skills_ai = []
    missing = []
    ai_projects = []
    job_matches = []
    cache_hit = False
    ai_used = False
    ai_source = "fallback"

    try:
        # detect cache hit before call
        try:
            ck = _ai_gen_module._cache_key(target_role, user_skills)
            with _ai_gen_module._LOCK:
                cache_hit = ck in _ai_gen_module.AI_CACHE
        except Exception:
            cache_hit = False

        ai_result = get_unified_analysis(user_skills, target_role)

        # Map unified schema to frontend keys
        required_skills_ai = ai_result.get("candidate_required_skills", [])[:10]
        missing = ai_result.get("candidate_missing_skills", [])
        ai_projects = ai_result.get("ai_projects_sample", [])
        job_matches = ai_result.get("job_matches", [])

        ai_source = getattr(_ai_gen_module, "LAST_AI_SOURCE", "gemini") or "gemini"
        ai_used = ai_source in ("gemini", "cache")

    except Exception as e:
        print("⚠️ Unified AI analysis failed in /recommend:", e)
        # Fallback: deterministic DB-based missing skills
        try:
            missing = find_missing_skills(user_skills, target_role)
            required_skills_ai = []
            ai_projects = generate_ai_project_ideas(target_role, user_skills)
        except Exception as inner:
            print("❌ Fallback skill lookup also failed:", inner)
            return jsonify({
                "error": "AI skill analyzer failed and fallback unavailable",
                "details": str(e),
            }), 500

    # 3) Micro-projects for missing skills (can also include YouTube links if you've wired that)
    projects = generate_micro_projects(missing, include_videos=fetch_videos, max_results_per_skill=max_videos)

   

    # If unified did not provide job_matches, synthesize a minimal match for the selected role
    if not job_matches:
        try:
            if required_skills_ai:
                percent, known, total, missing_for_role = _compute_match(user_skills, required_skills_ai)
                job_matches = [{
                    "role": target_role or "Selected role",
                    "match_percent": int(percent),
                }]
            else:
                job_matches = [{
                    "role": target_role or "Selected role",
                    "match_percent": 0,
                }]
        except Exception:
            job_matches = [{"role": target_role or "Selected role", "match_percent": 0}]

    # Emit single structured log per request as required
    ai_used_flag = "true" if ai_used else "false"
    cache_hit_flag = "true" if cache_hit else "false"
    ai_src = ai_source or ("fallback" if not ai_used else "gemini")
    app.logger.info(f"AI_USED={ai_used_flag} AI_SOURCE={ai_src} ROLE={target_role} CACHE_HIT={cache_hit_flag}")

    # If the AI role matcher failed to return anything, synthesize a simple
    # fallback so the frontend can always display a job readiness card.
    if not job_matches:
        try:
            if required_skills_ai:
                percent, known, total, missing_for_role = _compute_match(user_skills, required_skills_ai)
                job_matches = [{
                    "role": target_role or "Selected role",
                    "match_percent": int(percent),
                    "known_count": int(known),
                    "total_required": int(total),
                    "missing_skills_for_role": missing_for_role,
                    "is_selected_role": True,
                }]
            else:
                # No AI required skills available — produce a minimal exploring state
                job_matches = [{
                    "role": target_role or "Selected role",
                    "match_percent": 0,
                    "known_count": 0,
                    "total_required": 0,
                    "missing_skills_for_role": [],
                    "is_selected_role": True,
                }]
        except Exception as e:
            print("⚠️ Fallback job match generation failed:", e)
            job_matches = []

    # If they already match all required skills, keep your "perfect match" message
    if not missing:
        return jsonify({
            "message": "You are a perfect match for this role!",
            "role": target_role,
            "known_skills": user_skills,
            "missing_skills": [],
            "required_skills_ai": required_skills_ai,
            "recommended_projects": [],
            "ai_projects": ai_projects,
            "job_matches": job_matches,
        }), 200

    return jsonify({
        "role": target_role,
        "known_skills": user_skills,
        "missing_skills": missing,
        "required_skills_ai": required_skills_ai,
        "recommended_projects": projects,
        "ai_projects": ai_projects,
        "job_matches": job_matches,
        "include_youtube": fetch_videos,
        "max_video_results_per_skill": max_videos,
    })


@app.route('/recommend/projects', methods=['POST'])
def recommend_projects():
        """
        Two-step flow endpoint: generate projects/videos for a user-selected list of missing skills.

        Expects JSON:
            {
                "selected_missing_skills": ["Skill A", "Skill B"],
                "raw_profile_text": "optional raw prompt text",
                "include_youtube": true,
                "max_video_results": 3
            }

        Returns:
            { "recommended_projects": [ {skill, project, videos?, learning_path_steps?}, ... ] }
        """
        data = request.get_json() or {}
        selected = data.get('selected_missing_skills') or []
        if not isinstance(selected, list):
                return jsonify({"error": "selected_missing_skills must be an array"}), 400

        fetch_videos = bool(data.get('include_youtube', False))
        max_videos = int(data.get('max_video_results', 3) or 3)

        try:
                projects = generate_micro_projects(selected, include_videos=fetch_videos, max_results_per_skill=max_videos)
        except Exception as e:
                print("⚠️ generate_micro_projects failed in /recommend/projects:", e)
                projects = []

        return jsonify({
                "recommended_projects": projects,
                "selected_missing_skills": selected,
        })

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Proceed with saving or processing
    return jsonify({'message': 'Resume uploaded successfully'}), 200

@app.after_request
def set_response_headers(response):
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    elif response.mimetype == 'text/html':
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Skill Gap API is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

