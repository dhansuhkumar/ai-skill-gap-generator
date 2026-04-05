import os
import json
import logging
from typing import List
from flask import Blueprint, request, jsonify, g, current_app
from .auth import session_required
from .utils.validators import sanitize_filename
from .resume_parser import extract_skills_from_pdf, extract_resume_deep
from .ai_generator import analyze_skill_gaps
from .skill_analyzer import analyze_skill_gaps_optimized
from .web_skill_extractor import extract_skills_from_snippet

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

_local_profiles = {}


def home():
    return jsonify({"message": "Skill Gap API v3 (Web-Search Mode) is running!"})


@main.route("/job_titles", methods=["GET"])
def job_titles():
    """Get list of job titles from web search for autocomplete."""
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    titles = _get_job_titles_suggestions(query, limit)
    return jsonify({"titles": titles})


def _get_job_titles_suggestions(query: str, limit: int = 10) -> List[str]:
    """Get job title suggestions from web search."""
    try:
        from ddgs import DDGS

        suggestions = []
        seen = set()

        queries = [
            f'"{query}" job titles tech',
            f"{query} developer roles",
        ]

        with DDGS() as ddgs:
            for q in queries:
                if len(suggestions) >= limit:
                    break
                for r in ddgs.text(q, max_results=limit):
                    title = r.get("title", "").split(" - ")[0].split(" | ")[0].strip()
                    if title and title.lower() not in seen and len(title) > 3:
                        seen.add(title.lower())
                        suggestions.append(title)

        return suggestions[:limit]
    except Exception as e:
        logger.error(f"Job title suggestions failed: {e}")
        return []


@main.route("/upload_resume", methods=["POST"])
def upload_resume():
    """Step 1a: Upload Resume -> Extract Skills with Deep AI Analysis."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = sanitize_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400

    try:
        deep_result = extract_resume_deep(file)

        skills_list = deep_result.get("skills", [])

        parsed_data = {
            "skills": skills_list,
            "education": deep_result.get("education", []),
            "experience": deep_result.get("experience", []),
            "certifications": deep_result.get("certifications", []),
            "languages": deep_result.get("languages", []),
            "global_context": deep_result.get("global_context", "neutral"),
            "estimated_years": deep_result.get("estimated_years"),
            "has_projects": deep_result.get("has_projects", False),
            "total_experience_years": deep_result.get("total_experience_years"),
            "github_url": deep_result.get("github_url", ""),
            "linkedin_url": deep_result.get("linkedin_url", ""),
            "location": deep_result.get(
                "location", {"city": "", "state": "", "country": ""}
            ),
            "filled_boxes": deep_result.get("filled_boxes", 0),
            "total_boxes": deep_result.get("total_boxes", 7),
            "filled_percentage": deep_result.get("filled_percentage", 0),
        }

        return jsonify({"status": "ok", "parsed": parsed_data})
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@main.route("/analyze_gaps", methods=["POST"])
@session_required
def analyze_gaps():
    """Step 2->3 Transition: Get Missing Skills based on Role."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    role = data.get("target_role")
    user_skills = data.get("skills", [])

    if not role:
        return jsonify({"error": "Target role is required"}), 400

    if not isinstance(user_skills, list):
        return jsonify({"error": "Skills must be a list"}), 400

    if len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400

    try:
        result = analyze_skill_gaps(user_skills, role)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Gap analysis failed: {e}")
        return jsonify({"error": "Analysis failed"}), 500


@main.route("/recommend", methods=["POST", "OPTIONS"])
def recommend():
    """Gap analysis endpoint - returns missing skills and recommended resources.

    Uses web-search-based analysis (no HuggingFace).
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    role = data.get("role")
    user_skills = data.get("skills", [])

    if not role:
        return jsonify({"error": "Role is required"}), 400

    if not isinstance(user_skills, list):
        return jsonify({"error": "Skills must be a list"}), 400

    if len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400

    try:
        result = analyze_skill_gaps_optimized(user_skills, role)

        missing_skills = result.get("missing_skills", [])
        required_skills = result.get("required_skills", [])
        matched_jobs_count = result.get("matched_jobs_count", 0)
        source = result.get("source", "unknown")

        return jsonify(
            {
                "missing_skills": missing_skills,
                "required_skills": required_skills,
                "recommended_projects": [],
                "matched_jobs_count": matched_jobs_count,
                "source": source,
            }
        )
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


@main.route("/save_profile", methods=["POST"])
@session_required
def save_profile():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    user_id = g.user["id"]
    role = data.get("role")
    skills = data.get("skills", [])
    recommendations = data.get("recommendations", [])

    if not isinstance(skills, list):
        return jsonify({"error": "Skills must be a list"}), 400

    if not isinstance(recommendations, list):
        return jsonify({"error": "Recommendations must be a list"}), 400

    if role and len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400

    experience_level = data.get("experience_level", "neutral")
    estimated_years = data.get("estimated_years")

    try:
        supabase = current_app.supabase
        if supabase:
            supabase.table("profiles").upsert(
                {
                    "user_id": user_id,
                    "role": role,
                    "skills": json.dumps(skills),
                    "recommendations": json.dumps(recommendations),
                    "experience_level": experience_level,
                    "estimated_years": estimated_years,
                },
                on_conflict="user_id",
            ).execute()
            return jsonify({"message": "Profile saved"}), 200
    except Exception as e:
        logger.warning(
            f"Supabase save failed (table may not exist), using in-memory: {e}"
        )

    _local_profiles[user_id] = {
        "role": role,
        "skills": skills,
        "recommendations": recommendations,
        "experience_level": experience_level,
        "estimated_years": estimated_years,
    }
    return jsonify(
        {
            "message": "Profile saved (in-memory)",
            "note": "Run SQL migration for persistence",
        }
    ), 200


@main.route("/profile", methods=["GET"])
@session_required
def profile():
    user_id = g.user["id"]
    try:
        supabase = current_app.supabase
        if supabase:
            result = (
                supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            )
            if result.data:
                row = result.data[0]
                return jsonify(
                    {
                        "user_id": user_id,
                        "role": row.get("role"),
                        "skills": json.loads(row.get("skills", "[]"))
                        if isinstance(row.get("skills"), str)
                        else row.get("skills", []),
                        "recommendations": json.loads(row.get("recommendations", "[]"))
                        if isinstance(row.get("recommendations"), str)
                        else row.get("recommendations", []),
                        "experience_level": row.get("experience_level", "neutral"),
                        "estimated_years": row.get("estimated_years"),
                    }
                ), 200
    except Exception as e:
        logger.warning(f"Supabase query failed (table may not exist): {e}")

    if user_id in _local_profiles:
        local = _local_profiles[user_id]
        return jsonify(
            {
                "user_id": user_id,
                "role": local.get("role"),
                "skills": local.get("skills", []),
                "recommendations": local.get("recommendations", []),
                "experience_level": local.get("experience_level", "neutral"),
                "estimated_years": local.get("estimated_years"),
            }
        ), 200

    return jsonify(
        {
            "user_id": user_id,
            "role": None,
            "skills": [],
            "recommendations": [],
            "experience_level": "neutral",
            "estimated_years": None,
        }
    ), 200


@main.route("/job_matches", methods=["POST", "OPTIONS"])
def get_job_matches():
    """
    Get matching jobs with success rate based on user skills and experience level.
    Uses Job API Client (Remotive/Jooble/Adzuna) for REAL job posting URLs.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    user_skills = data.get("skills", [])
    target_role = data.get("role", "")
    experience_level = data.get("experience_level", "neutral")
    user_location = data.get("location", {})

    logger.info(
        f"job_matches: role='{target_role}', exp='{experience_level}', location={user_location}"
    )

    if not target_role:
        return jsonify({"error": "Role is required"}), 400

    try:
        from .job_api_client import search_jobs, get_job_match_stats

        result = search_jobs(
            skills=user_skills,
            role=target_role,
            experience_level=experience_level,
            max_results=20,
            user_location=user_location,
        )

        jobs = result.get("jobs", [])
        logger.info(
            f"job_matches: found {len(jobs)} jobs from sources: {result.get('sources', [])}"
        )

        stats = get_job_match_stats(jobs, user_skills)

        return jsonify(
            {
                "jobs": jobs,
                "total_found": result.get("total_found", len(jobs)),
                "sources": result.get("sources", []),
                "experience_filter": experience_level,
                "user_location": user_location,
                "stats": stats,
            }
        )

    except Exception as e:
        logger.error(f"Job search failed: {e}")
        return jsonify(
            {
                "jobs": [],
                "total_found": 0,
                "sources": ["error"],
                "experience_filter": experience_level,
                "error": str(e),
            }
        )


@main.app_errorhandler(500)
def internal_error(error):
    logger.exception(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500
