# routes_phase2.py
import os
import sqlite3
import json
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
import openai
from datetime import datetime
import asyncio

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

bp = Blueprint("phase2", __name__)

DB_PATH = os.getenv("DB_PATH", "users.db")  # point to your users.db

# ---------------------------
# Helper DB functions
# ---------------------------
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

# ---------------------------
# JWT helper (replace with your implementation)
# ---------------------------
def verify_jwt_token(authorization_header):
    """
    Verify JWT token and return user_id if valid, else None.
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return None
    try:
        from flask_jwt_extended import decode_token
        token = authorization_header.split()[1]
        decoded = decode_token(token)
        return decoded.get("sub")  # Assuming 'sub' is the user_id
    except Exception:
        return None

# ---------------------------
# Endpoint: save confirmed skills for a profile
# POST /confirm_skills
# Body: { "profile_id": 1, "skills": [{"name":"React","confidence":80,"source":"user"}] }
# Header: Authorization: Bearer <jwt>
# ---------------------------
@bp.route("/confirm_skills", methods=["POST"])
def confirm_skills():
    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    profile_id = data.get("profile_id")
    skills = data.get("skills", [])  # list of {name, confidence, source}

    if not profile_id or not isinstance(skills, list):
        return jsonify({"error": "profile_id and skills[] required"}), 400

    conn = get_db_conn()
    try:
        # optional: verify profile belongs to user
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM profiles WHERE id = ?", (profile_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Profile not found"}), 404
        # if row["user_id"] != user_id: return 403 (optional)

        saved = []
        for sk in skills:
            name = sk.get("name")
            confidence = int(sk.get("confidence", 80))
            source = sk.get("source", "user")
            skill_id = ensure_skill_exists(conn, name)
            cur.execute(
                "INSERT INTO profile_skills (profile_id, skill_id, confidence, source) VALUES (?,?,?,?)",
                (profile_id, skill_id, confidence, source)
            )
            saved.append({"skill_id": cur.lastrowid, "name": name, "confidence": confidence})

        conn.commit()
        return jsonify({"status": "ok", "saved": saved})
    finally:
        conn.close()

# ---------------------------
# Endpoint: generate learning path using OpenAI
# POST /generate_learning_path
# Body: { "profile_id": 1, "target_role":"Frontend Developer", "days":30 }
# Header: Authorization: Bearer <jwt>
# ---------------------------
@bp.route("/generate_learning_path", methods=["POST"])
async def generate_learning_path():
    user_id = verify_jwt_token(request.headers.get("Authorization"))
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    req = request.get_json()
    profile_id = req.get("profile_id")
    target_role = req.get("target_role")
    days = int(req.get("days", 30))

    if not profile_id or not target_role:
        return jsonify({"error": "profile_id and target_role required"}), 400

    # 1) load profile + skills from DB
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        profile_row = cur.fetchone()
        if not profile_row:
            return jsonify({"error": "Profile not found"}), 404

        # profile_parsed_json may be stored as text; parse if present
        parsed_json = {}
        if profile_row["resume_parsed_json"]:
            try:
                parsed_json = json.loads(profile_row["resume_parsed_json"])
            except Exception:
                parsed_json = {}

        # get skills
        cur.execute("""
            SELECT s.name, ps.confidence
            FROM profile_skills ps
            JOIN skills s ON s.id = ps.skill_id
            WHERE ps.profile_id = ?
            ORDER BY ps.confidence DESC
        """, (profile_id,))
        skills_rows = cur.fetchall()
        skill_list = [{"name":r["name"], "confidence": r["confidence"]} for r in skills_rows]

    finally:
        conn.close()

    # 2) Build a compact profile summary for the model
    profile_summary = {
        "display_name": profile_row["display_name"],
        "skills": skill_list,
        "resume_summary": parsed_json.get("summary", "") if isinstance(parsed_json, dict) else ""
    }

    # 3) Prompt OpenAI to generate a structured learning path JSON
    system_prompt = (
        "You are an expert career coach. "
        "Generate a clear, practical learning path to help this user reach the target role. "
        "Return JSON only with keys: summary (1-line), steps (array). "
        "Each step object: {day_from:int, day_to:int, title:string, tasks:[strings], project:string, outcome:string, resources:[strings]}."
    )

    user_prompt = {
        "profile": profile_summary,
        "target_role": target_role,
        "time_horizon_days": days,
        "instructions": "Keep steps realistic for daily study (assume 1.5-2 hours/day). Provide 6-12 steps spanning the period."
    }

    # Call OpenAI Chat API (Chat completion)
    try:
        # Use ChatCompletion with gpt-4o-mini or gpt-4 if available; adjust model name per your access
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",  # change if not available. Use "gpt-4o-mini" or "gpt-4" per your account
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)}
            ],
            max_tokens=1000,
            temperature=0.2
        )

        # model text
        text_out = response.choices[0].message["content"].strip()

        # try to parse JSON from model
        try:
            path_json = json.loads(text_out)
        except Exception:
            # If model returns extra commentary, attempt to extract json substring
            start = text_out.find("{")
            end = text_out.rfind("}")
            if start != -1 and end != -1:
                try:
                    path_json = json.loads(text_out[start:end+1])
                except Exception as e:
                    return jsonify({"error": "Failed to parse model output as JSON", "raw": text_out}), 500
            else:
                return jsonify({"error": "Model did not return JSON", "raw": text_out}), 500

        # store the generated path optionally (you can add a table learning_paths)
        return jsonify({"status":"ok", "learning_path": path_json})
    except Exception as e:
        return jsonify({"error": "OpenAI call failed", "details": str(e)}), 500
