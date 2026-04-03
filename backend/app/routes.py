import os
import json
import logging
from typing import List
from flask import Blueprint, request, jsonify, g, current_app
from .auth import session_required
from .utils.validators import sanitize_filename
from .resume_parser import extract_skills_from_pdf
from .ai_generator import analyze_skill_gaps
from .skill_analyzer import analyze_skill_gaps_optimized
# Note: GitHub analysis is handled exclusively by the phase2 blueprint (routes_phase2.py)
# GithubProfileAnalyzer import removed to prevent duplicate route registration

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return jsonify({"message": "Skill Gap API (CSV-based Mode) is running!"})


@main.route("/job_titles", methods=["GET"])
def job_titles():
    """Get list of available job titles for autocomplete."""
    from .hf_data_loader import get_similar_job_titles

    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    titles = get_similar_job_titles(query, limit)
    return jsonify({"titles": titles})


@main.route("/upload_resume", methods=["POST"])
def upload_resume():
    """Step 1a: Upload Resume -> Extract Skills and return structured JSON"""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Sanitize filename
    filename = sanitize_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    # Check file size (limit to 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400

    try:
        from .resume_parser import extract_skills_with_context

        parsed_result = extract_skills_with_context(file)

        # Extract skill names from the structured response
        skills_list = [
            s.get("skill", s) if isinstance(s, dict) else s
            for s in parsed_result.get("skills", [])
        ]

        # Return structured JSON matching the contract
        parsed_data = {
            "skills": skills_list if isinstance(skills_list, list) else [],
            "summary": "",
            "experience": [],
            "global_context": parsed_result.get("global_context", "neutral"),
            "estimated_years": parsed_result.get("estimated_years"),
            "has_projects": parsed_result.get("has_projects", False),
        }

        return jsonify({"status": "ok", "parsed": parsed_data})
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
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

    # Validate role is not too long
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

    Uses CSV-based analysis (Kaggle job data) to find required skills.
    Also provides YouTube video resources for learning.
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

    # Validate role is not too long
    if len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400

    try:
        # Use HuggingFace-based analysis
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

    # Validate skills is a list
    if not isinstance(skills, list):
        return jsonify({"error": "Skills must be a list"}), 400

    if not isinstance(recommendations, list):
        return jsonify({"error": "Recommendations must be a list"}), 400

    # Validate role length
    if role and len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400

    # Get experience level from data
    experience_level = data.get("experience_level", "neutral")
    estimated_years = data.get("estimated_years")

    try:
        supabase = current_app.supabase
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
        logger.error(f"Save profile failed: {e}")
        return jsonify({"error": "Failed to save profile"}), 500


@main.route("/profile", methods=["GET"])
@session_required
def profile():
    user_id = g.user["id"]
    try:
        supabase = current_app.supabase
        result = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if not result.data:
            return jsonify({"error": "Not found"}), 404
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
        logger.error(f"Get profile failed: {e}")
        return jsonify({"error": "Failed to get profile"}), 500


@main.route("/job_matches", methods=["POST", "OPTIONS"])
def get_job_matches():
    """
    Get matching jobs with success rate based on user skills and experience level.
    Uses real-time web search for fresher/experienced-appropriate listings.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    logger.info(
        f"job_matches request body keys: {list(data.keys()) if data else 'None'}"
    )
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    user_skills = data.get("skills", [])
    target_role = data.get("role", "")
    experience_level = data.get("experience_level", "neutral")
    logger.info(
        f"job_matches: role='{target_role}', exp='{experience_level}', skills_count={len(user_skills)}"
    )

    if not target_role:
        return jsonify(
            {
                "error": "Role is required",
                "received_role": target_role,
                "received_keys": list(data.keys()),
            }
        ), 400

    from .web_search import search_live_jobs
    from .hf_data_loader import hf_loader

    matched_jobs = search_live_jobs(
        role=target_role,
        experience_level=experience_level,
        skills=user_skills,
        max_results=30,
    )
    logger.info(
        f"job_matches: found {len(matched_jobs)} live jobs for role '{target_role}'"
    )

    results = []

    for job in matched_jobs:
        job_link = job.get("job_link", "")
        job_title = job.get("job_title", "")
        company = job.get("company", "")
        location = job.get("job_location", "")
        snippet = job.get("snippet", "")
        job_source = job.get("source", "unknown")

        # For live jobs, extract skills from snippet (primary path)
        # For cached/hf jobs, try the skills_map fallback
        required_skills = []

        if snippet:
            required_skills = _extract_skills_from_snippet(snippet, user_skills)

        # If still empty, try HF skills map for cached job links
        if not required_skills and job_source != "live_search":
            skills_map = hf_loader.get_skills_for_job_links([job_link])
            required_skills = skills_map.get(job_link, [])

        # If still empty, use user skills as proxy
        if not required_skills:
            required_skills = user_skills[:5]

        # Calculate match
        if required_skills:
            user_skills_lower = [s.lower().strip() for s in user_skills]
            required_lower = [s.lower().strip() for s in required_skills]
            matched = len(
                [
                    s
                    for s in required_lower
                    if any(us in s or s in us for us in user_skills_lower)
                ]
            )
            success_rate = (
                round((matched / len(required_lower)) * 100) if required_lower else 50
            )
        else:
            success_rate = 50
            matched = 0

        results.append(
            {
                "job_title": job_title,
                "company": company,
                "location": location,
                "job_link": job_link,
                "success_rate": success_rate,
                "required_skills": required_skills[:10],
                "matched_skills_count": matched,
                "total_required": len(required_skills),
            }
        )

    results.sort(key=lambda x: x["success_rate"], reverse=True)

    return jsonify(
        {
            "jobs": results[:20],
            "total_found": len(matched_jobs),
            "source": "live_search",
            "experience_filter": experience_level,
        }
    )


def _extract_skills_from_snippet(snippet: str, user_skills: List[str]) -> List[str]:
    """Extract required skills from job snippet by matching with user skills or common tech terms."""
    import re

    # Expanded common tech skills with variations
    skill_patterns = {
        "Python": ["python", "pytorch", "pandas", "django", "flask"],
        "JavaScript": ["javascript", "js", "node.js", "nodejs", "express"],
        "TypeScript": ["typescript", "ts"],
        "React": ["react", "reactjs", "react.js"],
        "Vue": ["vue", "vuejs", "vue.js"],
        "Angular": ["angular"],
        "SQL": ["sql", "mysql", "postgresql", "postgres", "mongodb", "redis"],
        "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
        "Azure": ["azure", "microsoft azure"],
        "GCP": ["gcp", "google cloud", "google cloud platform"],
        "Docker": ["docker", "container", "containerization"],
        "Kubernetes": ["kubernetes", "k8s", "k8"],
        "Git": ["git", "github", "gitlab", "version control"],
        "Machine Learning": ["machine learning", "ml", "deep learning", "ai"],
        "Data Science": ["data science", "data analysis", "analytics"],
        "TensorFlow": ["tensorflow", "tf"],
        "PyTorch": ["pytorch"],
        "Linux": ["linux", "unix"],
        "REST API": ["rest", "restful", "api"],
        "GraphQL": ["graphql"],
        "CI/CD": ["ci/cd", "jenkins", "github actions", "cicd"],
        "Agile": ["agile", "scrum", "kanban"],
        "DevOps": ["devops", "sre", "site reliability"],
        "HTML/CSS": ["html", "css", "html5", "css3"],
        "Java": ["java", "spring", "springboot"],
        "C++": ["c++", "cpp"],
        "Go": ["go", "golang"],
        "Rust": ["rust"],
        "Scala": ["scala"],
        "Ruby": ["ruby", "ruby on rails"],
        "PHP": ["php", "laravel"],
        "Swift": ["swift", "ios"],
        "Kotlin": ["kotlin", "android"],
        "Excel": ["excel", "spreadsheet"],
        "Tableau": ["tableau"],
        "Power BI": ["power bi", "powerbi"],
        "Spark": ["spark", "pyspark", "apache spark"],
        "Hadoop": ["hadoop", "hdfs", "mapreduce"],
        "Kafka": ["kafka", "confluent"],
        "Microservices": ["microservices", "microservice"],
    }

    snippet_lower = snippet.lower()
    found_skills = []

    # First add user skills that appear in snippet
    for skill in user_skills:
        skill_lower = skill.lower()
        if skill_lower in snippet_lower:
            if skill not in found_skills:
                found_skills.append(skill)

    # Then add common skills from the snippet
    for primary_skill, variations in skill_patterns.items():
        if primary_skill in found_skills:
            continue
        for variant in variations:
            if variant in snippet_lower:
                found_skills.append(primary_skill)
                break

    return found_skills[:10]


@main.app_errorhandler(500)
def internal_error(error):
    logger.exception(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500
