# routes_phase2.py
import os
import sqlite3
import json
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Do NOT import openai globally to avoid circular import crashes during app startup
# from openai import AsyncOpenAI 

load_dotenv()

bp = Blueprint("phase2", __name__)

DB_PATH = os.getenv("DB_PATH", "users.db")

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_skill_exists(conn, skill_name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO skills (name) VALUES (?)", (skill_name,))
    conn.commit()
    return cur.lastrowid

def verify_jwt_token(authorization_header):
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return None
    
    token = authorization_header.split()[1]
    
    # Try Supabase token verification first if configured
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    supabase_key = os.getenv("VITE_SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        try:
            from backend.supabase_client import get_supabase
            supabase = get_supabase()
            if supabase:
                # Verify token with Supabase
                user_response = supabase.auth.get_user(token)
                if user_response and user_response.user:
                    return user_response.user.id
        except Exception as e:
            # If Supabase verification fails, fall back to local JWT
            pass
    
    # Fallback to local JWT verification
    try:
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        return decoded.get("sub")
    except Exception:
        return None

@bp.route("/confirm_skills", methods=["POST", "OPTIONS"])
def confirm_skills():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return jsonify({"error": "skills[] must be a list"}), 400

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        
        # Auto-resolve profile_id from user_id
        cur.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        
        if row:
            profile_id = row["id"]
        else:
            # Create new profile if it doesn't exist
            cur.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
            conn.commit()
            profile_id = cur.lastrowid

        saved = []
        for sk in skills:
            name = sk.get("name")
            confidence = int(sk.get("confidence", 80))
            source = sk.get("source", "user")
            skill_id = ensure_skill_exists(conn, name)
            
            cur.execute("SELECT id FROM profile_skills WHERE profile_id=? AND skill_id=?", (profile_id, skill_id))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO profile_skills (profile_id, skill_id, confidence, source) VALUES (?,?,?,?)",
                    (profile_id, skill_id, confidence, source)
                )
                saved.append({"skill_id": cur.lastrowid, "name": name, "confidence": confidence})
            else:
                saved.append({"name": name, "status": "already_exists"})

        conn.commit()
        return jsonify({"status": "ok", "saved": saved})
    finally:
        conn.close()

@bp.route("/generate_learning_path", methods=["POST"])
def generate_learning_path():
    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    req = request.get_json()
    if not req:
        return jsonify({"error": "Invalid JSON body"}), 400

    target_role = req.get("target_role")
    selected_skills = req.get("selected_skills", [])
    days = int(req.get("days", 30))
    daily_hours = float(req.get("daily_hours", 1.5))
    project_type = req.get("project_type", "portfolio")
    include_youtube = req.get("include_youtube", False)
    additional_context = req.get("additional_context", "")
    provider = req.get("provider", "auto")
    profile_id = req.get("profile_id")

    # Validation
    if not target_role:
        return jsonify({"error": "target_role is required"}), 400
    if not selected_skills or not isinstance(selected_skills, list) or len(selected_skills) == 0:
        return jsonify({"error": "selected_skills must be a non-empty list"}), 400

    # Resolve profile_id from user_id if not provided
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        if not profile_id:
            cur.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                profile_id = row["id"]
            else:
                # Create profile if it doesn't exist
                cur.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
                conn.commit()
                profile_id = cur.lastrowid

        # Get user's current skills for matching score calculation
        cur.execute("""
            SELECT s.name FROM profile_skills ps
            JOIN skills s ON s.id = ps.skill_id
            WHERE ps.profile_id = ?
        """, (profile_id,))
        user_skills = [r["name"] for r in cur.fetchall()]
    finally:
        conn.close()

    # Import AI generator functions
    from app.ai_generator import generate_learning_plan, analyze_skill_gaps
    from app.youtube_search import search_youtube_videos

    # Generate learning plan using AI generator
    try:
        plan_result = generate_learning_plan(
            selected_skills=selected_skills,
            role=target_role,
            days=days,
            hours=daily_hours,
            project_type=project_type,
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
        if include_youtube:
            try:
                for skill in selected_skills:
                    video_results = search_youtube_videos(
                        f"{skill} tutorial {target_role}",
                        max_results=2,
                        allow_search=True
                    )
                    videos.extend(video_results[:2])  # Limit to 2 per skill
                # Deduplicate by URL
                seen_urls = set()
                unique_videos = []
                for vid in videos:
                    url = vid.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_videos.append({
                            "title": vid.get("title", "Untitled"),
                            "url": url
                        })
                videos = unique_videos[:5]  # Max 5 videos total
            except Exception as e:
                # YouTube search failed, continue without videos
                videos = []

        # Build response matching exact contract
        response_data = {
            "status": "ok",
            "learning_path": {
                "summary": f"{days}-day learning plan for {target_role}",
                "skills": formatted_learning_paths,
                "projects": formatted_projects,
                "videos": videos
            },
            "matching_score": matching_score,
            "source": source_used
        }

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to generate learning path", "details": str(e)}), 500