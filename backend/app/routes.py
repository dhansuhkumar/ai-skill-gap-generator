import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, request, jsonify, g, current_app
from user_profile import get_user_profile, save_user_profile
from .auth import token_required
from .utils.validators import sanitize_filename
from .resume_parser import extract_skills_from_pdf
from .ai_generator import analyze_skill_gaps
from .skill_analyzer import analyze_skill_gaps_optimized
from .services.github_analyzer import GithubProfileAnalyzer

import logging
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return jsonify({"message": "Skill Gap API (CSV-based Mode) is running!"})

@main.route('/job_titles', methods=['GET'])
def job_titles():
    """Get list of available job titles for autocomplete."""
    from .hf_data_loader import get_similar_job_titles
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
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
    if not filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    # Check file size (limit to 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400

    try:
        skills = extract_skills_from_pdf(file)
        
        # Return structured JSON matching the contract
        parsed_data = {
            "skills": skills if isinstance(skills, list) else [],
            "summary": "",
            "experience": []
        }
        
        return jsonify({
            "status": "ok",
            "parsed": parsed_data
        })
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        return jsonify({"error": str(e)}), 500

@main.route('/analyze-github', methods=['POST', 'OPTIONS'])
def analyze_github():
    """Analyze GitHub profile for language proficiency scores.
    
    Returns skill scores and radar chart data based on repository analysis.
    """
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "GitHub username is required"}), 400
    
    # Validate username format (basic check)
    if not isinstance(username, str) or len(username) == 0 or len(username) > 39:
        return jsonify({"error": "Invalid GitHub username"}), 400
    
    try:
        analyzer = GithubProfileAnalyzer()
        result = analyzer.analyze_profile(username)
        
        # Check if there was an error
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        return jsonify({"error": "Failed to analyze GitHub profile", "details": str(e)}), 500

@main.route('/analyze_gaps', methods=['POST'])
@token_required
def analyze_gaps():
    """Step 2->3 Transition: Get Missing Skills based on Role."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    role = data.get('target_role')
    user_skills = data.get('skills', [])
    
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

@main.route('/recommend', methods=['POST', 'OPTIONS'])
def recommend():
    """Gap analysis endpoint - returns missing skills and recommended resources.
    
    Uses CSV-based analysis (Kaggle job data) to find required skills.
    Also provides YouTube video resources for learning.
    """
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    role = data.get('role')
    user_skills = data.get('skills', [])
    
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
        
        missing_skills = result.get('missing_skills', [])
        required_skills = result.get('required_skills', [])
        matched_jobs_count = result.get('matched_jobs_count', 0)
        source = result.get('source', 'unknown')
        
        return jsonify({
            "missing_skills": missing_skills,
            "required_skills": required_skills,
            "recommended_projects": [],
            "matched_jobs_count": matched_jobs_count,
            "source": source
        })
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500

@main.route('/save_profile', methods=['POST'])
@token_required
def save_profile():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    user_id = g.user['id']
    role = data.get('role')
    skills = data.get('skills', [])
    recommendations = data.get('recommendations', [])
    
    # Validate skills is a list
    if not isinstance(skills, list):
        return jsonify({"error": "Skills must be a list"}), 400
    
    if not isinstance(recommendations, list):
        return jsonify({"error": "Recommendations must be a list"}), 400
    
    # Validate role length
    if role and len(role) > 100:
        return jsonify({"error": "Role name too long"}), 400
    
    try:
        save_user_profile(user_id, role, skills, recommendations)
        return jsonify({"message": "Profile saved"}), 200
    except Exception as e:
        logger.error(f"Save profile failed: {e}")
        return jsonify({"error": "Failed to save profile"}), 500

@main.route('/profile', methods=['GET'])
@token_required
def profile():
    user_id = g.user['id']
    user_profile = get_user_profile(user_id)
    if not user_profile:
        return jsonify({"error": "Not found"}), 404
    return jsonify(user_profile), 200

@main.app_errorhandler(500)
def internal_error(error):
    logger.exception(f"Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500
