# routes_phase2.py
import os
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv

# Do NOT import openai globally to avoid circular import crashes during app startup
# from openai import AsyncOpenAI 

load_dotenv()

logger = logging.getLogger(__name__)

bp = Blueprint("phase2", __name__)

# Import Supabase client safely
try:
    from backend.supabase_client import get_supabase
except ImportError:
    from supabase_client import get_supabase

def get_supabase_client():
    """Get Supabase client, with fallback to app context if available."""
    # Try to get from Flask app context first
    try:
        if hasattr(current_app, 'supabase') and current_app.supabase:
            return current_app.supabase
    except RuntimeError:
        pass  # Outside app context
    
    # Fallback to direct client creation
    client = get_supabase()
    if not client:
        raise RuntimeError("Supabase client not available")
    return client

def ensure_skill_exists_supabase(supabase, skill_name):
    """Ensure a skill exists in Supabase, return its ID."""
    # Check if skill exists
    result = supabase.table("skills").select("id").eq("name", skill_name).execute()
    if result.data:
        return result.data[0]["id"]
    
    # Insert new skill
    insert_result = supabase.table("skills").insert({"name": skill_name}).execute()
    if insert_result.data:
        return insert_result.data[0]["id"]
    
    raise RuntimeError(f"Failed to create skill: {skill_name}")

def get_session_id():
    """
    Get session ID from X-Session-ID header.
    Falls back to 'anonymous' if not provided.
    No authentication required — this is a session-based app.
    """
    return request.headers.get("X-Session-ID") or "anonymous"


def ensure_auth_user_supabase(supabase, user_id):
    """Ensure a user exists in auth.users by utilizing admin api if they don't exist"""
    if user_id == "anonymous":
        return
    try:
        supabase.auth.admin.create_user({
            'id': user_id,
            'email': f'{user_id}@temp.com',
            'password': 'password123',
            'email_confirm': True
        })
    except Exception:
        # If user already exists, it will throw an exception which we can ignore
        pass




from backend.app.role_manager import role_manager

@bp.route("/sync_profile", methods=["POST", "OPTIONS"])
def sync_profile():
    """
    Sync user profile — session-based, no auth required.
    Creates Supabase profile if it doesn't exist.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    user_id = get_session_id()
    
    try:
        supabase = get_supabase_client()
        
        # Check if profile exists
        result = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
        
        if result.data:
            profile_id = result.data[0]["id"]
        else:
            # Create dummy auth user first to prevent foreign key errors
            ensure_auth_user_supabase(supabase, user_id)
            
            # Create new profile
            insert_result = supabase.table("profiles").insert({"user_id": user_id}).execute()
            if insert_result.data:
                profile_id = insert_result.data[0]["id"]
            else:
                return jsonify({"error": "Failed to create profile"}), 500
        
        return jsonify({
            "status": "ok",
            "profile_id": profile_id,
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Failed to sync profile: {e}")
        return jsonify({"error": f"Failed to sync profile: {str(e)}"}), 500

@bp.route("/analyze_role_gaps", methods=["POST"])
def analyze_role_gaps():
    """
    Optimized CSV-based skill gap analysis.
    Returns top 10 most important skills with caching for speed.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
        
    role = data.get("role", "")
    user_skills = data.get("skills", [])
    
    if not role:
        return jsonify({"error": "Role is required"}), 400
    
    # Use optimized CSV-based analysis (top 10 skills, cached)
    from backend.app.ai_generator import analyze_skill_gaps
    
    try:
        # Pass top_n=30 for more skill options
        gap_analysis = analyze_skill_gaps(user_skills, role, top_n=30)
        
        required_skills = gap_analysis.get("required_skills", [])
        missing_skills = gap_analysis.get("missing_skills", [])
        matched_count = gap_analysis.get("matched_count", 0)
        
        # Calculate match score
        if len(required_skills) > 0:
            user_has_count = len(required_skills) - len(missing_skills)
            match_score = int((user_has_count / len(required_skills)) * 100)
        else:
            match_score = 0
        
        # Get alternative role suggestions
        from backend.app.role_suggestions import get_alternative_roles
        alternative_roles = get_alternative_roles(user_skills, limit=5)
        
        return jsonify({
            "status": "ok",
            "missing_skills": missing_skills,  # Top 10 cleaned skills
            "required_skills": required_skills,  # Top 10 required skills
            "match_score": match_score,
            "user_skills_count": len(required_skills) - len(missing_skills),
            "required_skills_count": len(required_skills),
            "matched_jobs_count": matched_count,
            "alternative_roles": alternative_roles,
            "source": gap_analysis.get("source", "csv_optimized")
        })
    except Exception as e:
        print(f"Error in analyze_role_gaps: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@bp.route("/confirm_skills", methods=["POST", "OPTIONS"])
def confirm_skills():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    user_id = get_session_id()

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return jsonify({"error": "skills[] must be a list"}), 400

    try:
        supabase = get_supabase_client()
        
        # Auto-resolve profile_id from user_id
        result = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
        
        if result.data:
            profile_id = result.data[0]["id"]
        else:
            # Create dummy auth user first to prevent foreign key errors
            ensure_auth_user_supabase(supabase, user_id)
            
            # Create new profile if it doesn't exist
            insert_result = supabase.table("profiles").insert({"user_id": user_id}).execute()
            if insert_result.data:
                profile_id = insert_result.data[0]["id"]
            else:
                return jsonify({"error": "Failed to create profile"}), 500

        saved = []
        for sk in skills:
            name = sk.get("name")
            confidence = int(sk.get("confidence", 80))
            source = sk.get("source", "user")
            skill_id = ensure_skill_exists_supabase(supabase, name)
            
            # Check if profile_skill already exists
            existing = supabase.table("profile_skills")\
                .select("id")\
                .eq("profile_id", profile_id)\
                .eq("skill_id", skill_id)\
                .execute()
            
            if not existing.data:
                insert_result = supabase.table("profile_skills").insert({
                    "profile_id": profile_id,
                    "skill_id": skill_id,
                    "confidence": confidence,
                    "source": source
                }).execute()
                if insert_result.data:
                    saved.append({"skill_id": insert_result.data[0]["id"], "name": name, "confidence": confidence})
            else:
                saved.append({"name": name, "status": "already_exists"})

        return jsonify({"status": "ok", "saved": saved, "profile_id": profile_id})
    except Exception as e:
        logger.error(f"Failed to confirm skills: {e}")
        return jsonify({"error": f"Failed to confirm skills: {str(e)}"}), 500

@bp.route("/generate_learning_path", methods=["POST"])
def generate_learning_path():
    user_id = get_session_id()

    req = request.get_json()
    if not req:
        return jsonify({"error": "Invalid JSON body"}), 400

    target_role = req.get("target_role")
    selected_skills = req.get("selected_skills", [])
    
    # New params
    learning_pace = req.get("learning_pace", "Balanced")
    time_commitment = req.get("time_commitment", "1 hour")
    duration_pref = req.get("duration", "1 month") # e.g. "1 month", "2 weeks"
    
    # Map duration string to days (approximate) if raw days not provided
    raw_days = req.get("days")
    if not raw_days:
        if "week" in str(duration_pref).lower():
            if "2" in str(duration_pref): days = 14
            else: days = 7
        elif "month" in str(duration_pref).lower():
            if "2" in str(duration_pref): days = 60
            elif "3" in str(duration_pref): days = 90
            else: days = 30
        else:
            days = 30
    else:
        days = int(raw_days)

    # Use time_commitment to parse hours if not explicitly provided
    raw_hours = req.get("daily_hours")
    if not raw_hours:
        if "30" in str(time_commitment): daily_hours = 0.5
        elif "2" in str(time_commitment): daily_hours = 2.0
        else: daily_hours = 1.0
    else:
        daily_hours = float(raw_hours)

    project_type = req.get("project_type", "portfolio")
    include_youtube = req.get("include_youtube", False)
    print(f"DEBUG: generate_learning_path called. include_youtube={include_youtube}, selected_skills_count={len(selected_skills)}", flush=True)
    additional_context = req.get("additional_context", "")
    provider = req.get("provider", "auto")
    profile_id = req.get("profile_id")

    # Validation
    if not target_role:
        return jsonify({"error": "target_role is required"}), 400
    if not selected_skills or not isinstance(selected_skills, list) or len(selected_skills) == 0:
        return jsonify({"error": "selected_skills must be a non-empty list"}), 400
    
    # CRITICAL: Limit to 10 skills max (prevent 5014 skills issue)
    if len(selected_skills) > 10:
        print(f"⚠️ Limiting selected_skills from {len(selected_skills)} to 10")
        selected_skills = selected_skills[:10]

    # Resolve profile_id from user_id if not provided using Supabase
    try:
        supabase = get_supabase_client()
        
        if not profile_id:
            result = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
            if result.data:
                profile_id = result.data[0]["id"]
            else:
                # Create profile if it doesn't exist
                ensure_auth_user_supabase(supabase, user_id)
                insert_result = supabase.table("profiles").insert({"user_id": user_id}).execute()
                if insert_result.data:
                    profile_id = insert_result.data[0]["id"]
                else:
                    return jsonify({"error": "Failed to create profile"}), 500

        # Get user's current skills for matching score calculation
        # Query profile_skills joined with skills
        skills_result = supabase.table("profile_skills")\
            .select("skill_id, skills(name)")\
            .eq("profile_id", profile_id)\
            .execute()
        
        user_skills = []
        if skills_result.data:
            for row in skills_result.data:
                if row.get("skills") and row["skills"].get("name"):
                    user_skills.append(row["skills"]["name"])
    except Exception as e:
        logger.error(f"Failed to get profile/skills: {e}")
        user_skills = []  # Continue with empty skills if DB fails

    # Import AI generator functions
    from backend.app.ai_generator import generate_learning_plan
    from backend.app.youtube_search import search_youtube_videos

    # Generate learning plan using AI generator
    try:
        print(f"✅ Generating learning plan for {len(selected_skills)} skills: {selected_skills}")
        
        plan_result = generate_learning_plan(
            selected_skills=selected_skills,
            role=target_role,
            days=days,
            hours=daily_hours,
            project_type=project_type,
            learning_pace=learning_pace,     # NEW
            time_commitment=time_commitment, # NEW
            context=additional_context,
            requested_provider=provider if provider != "auto" else None
        )

        if "error" in plan_result:
            return jsonify({"error": plan_result["error"]}), 400

        # Extract source/provider used (track from generate_learning_plan if possible)
        # For now, use provider from request or "heuristic" as fallback
        source_used = provider if provider != "auto" else "heuristic"

        # Compute matching score: compare user skills vs selected skills + role requirements
        # Simple heuristic: if user has some of the selected skills, score is higher
        user_skill_set = {s.lower() for s in user_skills}
        selected_skill_set = {s.lower() for s in selected_skills}
        matching_skills = user_skill_set & selected_skill_set
        
        # Base score on how many selected skills user already has
        if len(selected_skill_set) > 0:
            base_score = int((len(matching_skills) / len(selected_skill_set)) * 100)
        else:
            base_score = 0

        # Use matching_score from plan if available, otherwise use computed
        matching_score = plan_result.get("matching_score", base_score)
        matching_score = max(0, min(100, int(matching_score)))  # Clamp 0-100

        # Get learning paths and projects from plan
        learning_paths = plan_result.get("learning_paths", {})
        projects = plan_result.get("projects", [])

        # Ensure projects have correct structure
        formatted_projects = []
        for proj in projects:
            if isinstance(proj, str):
                formatted_projects.append({
                    "title": proj,
                    "description": f"Project focusing on {', '.join(selected_skills)}",
                    "skills": selected_skills
                })
            elif isinstance(proj, dict):
                formatted_projects.append({
                    "title": proj.get("title", "Untitled Project"),
                    "description": proj.get("description", ""),
                    "skills": proj.get("skills", selected_skills)
                })

        # Format learning paths to match contract (skills object with summary and steps)
        formatted_learning_paths = {}
        for skill_name, skill_data in learning_paths.items():
            if isinstance(skill_data, dict):
                formatted_learning_paths[skill_name] = {
                    "summary": skill_data.get("summary", f"Learning path for {skill_name}"),
                    "steps": skill_data.get("steps", [])
                }
            else:
                # Fallback if structure is different
                formatted_learning_paths[skill_name] = {
                    "summary": f"Learning path for {skill_name}",
                    "steps": []
                }

        # Get YouTube videos if requested
        videos = []
        skill_videos = {}  # Map skill -> list of videos
        
        if include_youtube:
            try:
                from backend.app.youtube_search import search_youtube_videos
                
                logger.info(f"🎥 Fetching YouTube videos for {len(selected_skills)} skills")
                print(f"DEBUG: Entering YouTube search loop. Querying for: {selected_skills}", flush=True)
                
                for skill in selected_skills:
                    # Search for skill-specific tutorials
                    video_results = search_youtube_videos(
                        f"{skill} tutorial {target_role}",
                        max_results=3,  # 3 videos per skill
                        allow_search=True
                    )
                    
                    if video_results:
                        # Store videos for this skill
                        skill_videos[skill] = video_results[:3]
                        logger.info(f"   ✅ Found {len(video_results)} videos for {skill}")
                    else:
                        logger.warning(f"   ⚠️ No videos found for {skill}")
                        skill_videos[skill] = []
                
                # Also collect all videos for general display
                for vids in skill_videos.values():
                    videos.extend(vids)
                
                # Deduplicate by URL
                seen_urls = set()
                unique_videos = []
                for vid in videos:
                    url = vid.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_videos.append({
                            "title": vid.get("title", "Untitled"),
                            "url": url,
                            "channel": vid.get("channel", ""),
                            "thumbnail": vid.get("thumbnail", "")
                        })
                videos = unique_videos[:10]  # Max 10 videos total for general display
                
                logger.info(f"   ✅ Total unique videos: {len(videos)}")
                
            except Exception as e:
                logger.error(f"   ❌ YouTube search failed: {e}")
                # YouTube search failed, continue without videos
                videos = []
                skill_videos = {}

        # Attach YouTube videos to each skill's learning path
        for skill_name, skill_data in formatted_learning_paths.items():
            if skill_name in skill_videos:
                skill_data["youtube_videos"] = skill_videos[skill_name]
            else:
                skill_data["youtube_videos"] = []

        # Build response matching exact contract
        response_data = {
            "status": "ok",
            "learning_path": {
                "summary": f"{days}-day learning plan for {target_role}",
                "skills": formatted_learning_paths,  # Now includes youtube_videos per skill
                "projects": formatted_projects,
                "videos": videos  # General videos for backward compatibility
            },
            "matching_score": matching_score,
            "source": source_used
        }

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to generate learning path", "details": str(e)}), 500

@bp.route("/role-chat", methods=["POST"])
def role_chat_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
            
        role = data.get("role")
        messages = data.get("messages", [])
        provider = data.get("provider", "auto")
        
        from backend.app.role_chat import generate_role_chat_reply
        reply = generate_role_chat_reply(role, messages, requested_provider=provider)
        
        return jsonify({"response": reply, "reply": reply, "status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# SKILL TRIANGULATION ENGINE ENDPOINTS
# ============================================================

@bp.route("/analyze-github", methods=["POST", "OPTIONS"])
def analyze_github():
    """
    Analyze a GitHub profile for skill proficiency indicators.
    
    Input: { "github_username": "user123", "github_token": "optional_token" }
    
    Output: {
        "status": "ok",
        "username": "user123",
        "languages": {
            "Python": { "repos": 3, "score": 55, "has_tests": true, ... },
            ...
        },
        "total_repos": 8,
        "diversity_bonus": 10,
        "language_count": 5
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    github_username = data.get("github_username")
    if not github_username:
        return jsonify({"error": "github_username is required"}), 400
    
    # Optional: GitHub token for higher rate limits
    github_token = data.get("github_token") or os.getenv("GITHUB_TOKEN")
    
    try:
        from backend.app.github_analyzer import analyze_github_profile
        
        result = analyze_github_profile(github_username, github_token)
        
        if result.get("error"):
            return jsonify({
                "status": "error",
                "error": result["error"],
                "username": github_username
            }), 400
        
        return jsonify({
            "status": "ok",
            "username": result["username"],
            "languages": result["languages"],
            "total_repos": result["total_repos"],
            "diversity_bonus": result["diversity_bonus"],
            "language_count": result["language_count"]
        })
        
    except Exception as e:
        logger.error(f"GitHub analysis failed for {github_username}: {e}")
        return jsonify({
            "status": "error",
            "error": f"Analysis failed: {str(e)}"
        }), 500


@bp.route("/fuse-profile", methods=["POST", "OPTIONS"])
def fuse_profile():
    """
    Fuse skill data from multiple sources to calculate proficiency scores.
    
    Input: {
        "skills": [
            { "name": "Python", "manual_score": 70 },
            { "name": "React", "manual_score": 60 }
        ],
        "github_username": "optional_user123",
        "resume_data": { ... }  // Optional: output from extract_skills_with_context
    }
    
    Output: {
        "status": "ok",
        "proficiencies": [
            { "skill": "Python", "score": 75, "level": "Advanced", "breakdown": {...} },
            ...
        ],
        "average_score": 65,
        "skill_count": 2,
        "diversity_bonus_applied": true
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    skills = data.get("skills", [])
    if not skills or not isinstance(skills, list):
        return jsonify({"error": "skills must be a non-empty list"}), 400
    
    # Validate skill format
    for skill in skills:
        if not isinstance(skill, dict) or "name" not in skill:
            return jsonify({"error": "Each skill must have a 'name' field"}), 400
        if "manual_score" in skill:
            score = skill["manual_score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                return jsonify({"error": "manual_score must be 0-100"}), 400
    
    try:
        # Get GitHub data if username provided
        github_analysis = None
        github_username = data.get("github_username")
        if github_username:
            from backend.app.github_analyzer import analyze_github_profile
            github_token = data.get("github_token") or os.getenv("GITHUB_TOKEN")
            github_analysis = analyze_github_profile(github_username, github_token)
            if github_analysis.get("error"):
                # Log but continue without GitHub data
                logger.warning(f"GitHub analysis failed: {github_analysis['error']}")
                github_analysis = None
        
        # Get resume data (already parsed, passed directly)
        resume_data = data.get("resume_data")
        
        # Fuse the profile
        from backend.app.services.fusion_engine import fuse_skill_profile
        
        result = fuse_skill_profile(
            skills=skills,
            resume_data=resume_data,
            github_analysis=github_analysis
        )
        
        return jsonify({
            "status": "ok",
            "proficiencies": result["proficiencies"],
            "average_score": result["average_score"],
            "skill_count": result["skill_count"],
            "diversity_bonus_applied": result["diversity_bonus_applied"]
        })
        
    except Exception as e:
        logger.error(f"Profile fusion failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": f"Fusion failed: {str(e)}"
        }), 500


@bp.route("/upload-resume-with-context", methods=["POST", "OPTIONS"])
def upload_resume_with_context():
    """
    Upload resume and extract skills with context analysis.
    
    Input: Multipart form with 'file' field (PDF)
    
    Output: {
        "status": "ok",
        "parsed": {
            "skills": [{ "skill": "Python", "context": "fresher", "has_projects": true }],
            "global_context": "fresher",
            "estimated_years": null,
            "has_projects": true,
            "raw_skills": ["Python", "React", ...]
        }
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400
    
    # Check file size (limit to 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400
    
    try:
        from backend.app.resume_parser import extract_skills_with_context
        
        parsed_data = extract_skills_with_context(file)
        
        return jsonify({
            "status": "ok",
            "parsed": parsed_data
        })
        
    except Exception as e:
        logger.error(f"Resume parsing with context failed: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# DYNAMIC VISUALIZATION & DATA FUSION ENDPOINTS
# ============================================================

@bp.route("/update_github_data", methods=["POST", "OPTIONS"])
def update_github_data():
    """
    Refresh GitHub analysis data for a user — session-based, no auth required.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    user_id = get_session_id()
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    github_username = data.get("github_username")
    if not github_username:
        return jsonify({"error": "github_username is required"}), 400
    
    try:
        # Get or create profile
        from backend.supabase_client import get_supabase
        from backend.app.github_analyzer import analyze_github_profile
        
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Database connection not available"}), 500
        
        # Get profile_id
        profile_res = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
        if not profile_res.data:
            # Create profile
            ensure_auth_user_supabase(supabase, user_id)
            profile_res = supabase.table("profiles").insert({"user_id": user_id}).execute()
            profile_id = profile_res.data[0]["id"]
        else:
            profile_id = profile_res.data[0]["id"]
        
        # Analyze GitHub profile
        github_token = data.get("github_token") or os.getenv("GITHUB_TOKEN")
        result = analyze_github_profile(github_username, github_token)
        
        if result.get("error"):
            return jsonify({"error": result["error"]}), 400
        
        # Store in Supabase
        analysis_record = {
            "profile_id": profile_id,
            "username": github_username,
            "analysis_data": result.get("languages", {}),
            "commit_timeline": {},  # TODO: Add commit timeline data
            "total_repos": result.get("total_repos", 0),
            "diversity_bonus": result.get("diversity_bonus", 0),
            "language_count": result.get("language_count", 0),
            "last_updated": "now()"
        }
        
        # Upsert (update if exists, insert if not)
        existing = supabase.table("github_analysis")\
            .select("id")\
            .eq("profile_id", profile_id)\
            .execute()
        
        if existing.data:
            # Update existing
            supabase.table("github_analysis")\
                .update(analysis_record)\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            # Insert new
            supabase.table("github_analysis").insert(analysis_record).execute()
        
        return jsonify({
            "status": "ok",
            "github_data": result,
            "profile_id": profile_id
        })
        
    except Exception as e:
        logger.error(f"GitHub data update failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to update GitHub data: {str(e)}"}), 500


@bp.route("/save_learning_progress", methods=["POST", "OPTIONS"])
def save_learning_progress():
    """
    Save user's progress on a learning path step.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    skill_name = data.get("skill_name")
    step_index = data.get("step_index")
    completed = data.get("completed", False)
    
    if not skill_name or step_index is None:
        return jsonify({"error": "skill_name and step_index are required"}), 400
    
    try:
        from backend.supabase_client import get_supabase
        
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Database connection not available"}), 500
        
        # Get profile_id
        profile_res = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
        if not profile_res.data:
            return jsonify({"error": "Profile not found"}), 404
        
        profile_id = profile_res.data[0]["id"]
        
        # Upsert progress
        progress_record = {
            "profile_id": profile_id,
            "skill_name": skill_name,
            "step_index": step_index,
            "step_title": data.get("step_title", ""),
            "completed": completed,
            "completed_at": "now()" if completed else None,
            "notes": data.get("notes", ""),
            "updated_at": "now()"
        }
        
        # Check if already exists
        existing = supabase.table("learning_progress")\
            .select("id")\
            .eq("profile_id", profile_id)\
            .eq("skill_name", skill_name)\
            .eq("step_index", step_index)\
            .execute()
        
        if existing.data:
            # Update
            supabase.table("learning_progress")\
                .update(progress_record)\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            # Insert
            supabase.table("learning_progress").insert(progress_record).execute()
        
        return jsonify({"status": "ok", "message": "Progress saved"})
        
    except Exception as e:
        logger.error(f"Save learning progress failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to save progress: {str(e)}"}), 500


@bp.route("/get_dashboard_data", methods=["POST", "OPTIONS"])
def get_dashboard_data():
    """
    Get unified dashboard data combining all sources.
    Returns data structured for all visualization components.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400
    
    try:
        from backend.supabase_client import get_supabase
        from backend.app.services.fusion_service import create_unified_dashboard_data
        
        supabase = get_supabase()
        if not supabase:
            return jsonify({"error": "Database connection not available"}), 500
        
        # Get profile_id
        profile_res = supabase.table("profiles").select("id").eq("user_id", user_id).execute()
        if not profile_res.data:
            return jsonify({"error": "Profile not found"}), 404
        
        profile_id = profile_res.data[0]["id"]
        
        # Get user skills
        skills_res = supabase.table("profile_skills")\
            .select("skills(name)")\
            .eq("profile_id", profile_id)\
            .execute()
        user_skills = [s["skills"]["name"] for s in skills_res.data if s.get("skills")]
        
        # Get GitHub data
        github_res = supabase.table("github_analysis")\
            .select("*")\
            .eq("profile_id", profile_id)\
            .order("last_updated", desc=True)\
            .limit(1)\
            .execute()
        github_data = github_res.data[0] if github_res.data else None
        if github_data:
            github_data["languages"] = github_data.get("analysis_data", {})
        
        # Get learning progress
        progress_res = supabase.table("learning_progress")\
            .select("*")\
            .eq("profile_id", profile_id)\
            .execute()
        progress_data = progress_res.data
        
        # Get role analysis and learning path from request
        role_analysis = data.get("role_analysis", {})
        learning_path = data.get("learning_path", {})
        
        # Create unified dashboard data
        dashboard_data = create_unified_dashboard_data(
            user_skills=user_skills,
            role_analysis=role_analysis,
            github_data=github_data,
            learning_path=learning_path,
            progress_data=progress_data
        )
        
        return jsonify({
            "status": "ok",
            "dashboard_data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Get dashboard data failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to get dashboard data: {str(e)}"}), 500


@bp.route("/test_youtube", methods=["GET"])
def test_youtube():
    """Temporary endpoint to verify YouTube search functionality."""
    try:
        from backend.app.youtube_search import search_youtube_videos
        query = request.args.get("q", "Python tutorial")
        print(f"DEBUG: Testing YouTube search for query: {query}", flush=True)
        results = search_youtube_videos(query, max_results=3, allow_search=True)
        return jsonify({"status": "ok", "results": results, "query": query})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

