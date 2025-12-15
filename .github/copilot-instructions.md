# Copilot instructions for AI coding agents

Purpose
- Help AI coding agents quickly become productive in this repository by summarizing architecture, workflows, and project-specific conventions.

Big picture (high level)
- This is a small web service + static frontend: the backend is a Flask app under `backend/` and the static SPA lives in `frontend/`.
- App factory: `backend/app/__init__.py` exposes `create_app()`; routes are registered in `backend/app/routes.py` and `backend/run.py` wires the app for production (used by Gunicorn).
- AI features live under `backend/app/*` (`ai_skill_analyzer.py`, `ai_generator.py`, `recommender.py`). These modules try to use cloud LLMs but provide deterministic fallbacks when APIs or libs are missing.

Key files and responsibilities
- `backend/run.py`: application entry used by the Docker image (`backend.run:app` for Gunicorn). Also contains convenient direct-run endpoints when executed.
- `backend/app/__init__.py`: app factory, CORS, JWT config and an `/api/embed` helper for local embeddings.
- `backend/app/routes.py`: primary API blueprint mounted at `/api` — endpoints: `/recommend`, `/recommend/projects`, `/api/role-chat`, `/upload_resume`, profile endpoints, and starter ZIP serving.
- `backend/app/recommender.py`: deterministic skill DB lookup (`skill_db.json`, `skill_data.json`) and the `generate_micro_projects()` function (controls YouTube search usage via `include_videos` flag).
- `backend/app/ai_skill_analyzer.py`: AI prompt + model selection. Requires `GEMINI_API_KEY` and `google.generativeai` to enable; otherwise callers should fall back.
- `backend/database.py`: initializes an on-disk SQLite DB `users.db` and required tables—called from `backend/run.py` during startup.
- `frontend/script.js`: frontend expects backend at `http://127.0.0.1:8080` by default; it POSTs to `/recommend` and uses `/api/save_profile` when logged in.

Important conventions & patterns
- Defensive imports: many AI modules import vendor libraries inside try/except and raise or return safe defaults. When editing AI modules, preserve the fallback behavior so the API remains reachable offline.
- Flag propagation: frontend sends `include_youtube` and `max_video_results`; recommender honors these via `generate_micro_projects(missing, include_videos=True, max_results=3)`.
- Normalization: skill matching uses lightweight normalization functions (`_normalize_skill_name`) instead of a giant canonical DB — follow that pattern when adding new match logic.
- JWT identity: auth routes store the username as the JWT identity; profile endpoints expect the username as identity (see `backend/app/auth.py`).

Developer workflows (how to run & test)
- Local quick run (dev): create & activate venv, install requirements, then run the app directly (debug server on port 8080):

  Windows PowerShell
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements-prod.txt
  python backend/run.py
  ```

- Docker (production-like): the Dockerfile runs Gunicorn binding `backend.run:app` on port 5000. Compose maps host 5000→container 5000. Note: the frontend expects 8080 by default, so update `BASE_URL` or run the container port accordingly.

  Docker Compose
  ```bash
  docker compose -f docker-compose.yml up -d --build
  ```

- Tests: run tests from repo root. Pytest config sets `pythonpath = backend` in `backend/tests/pytest.ini`.

  ```bash
  pytest -q
  ```

Environment variables the agent should know
- `JWT_SECRET_KEY` — required for login/profile JWTs (read in `backend/app/__init__.py`).
- `GEMINI_API_KEY` — enables the AI skill analyzer (`backend/app/ai_skill_analyzer.py`). If missing, the AI path raises and code falls back to deterministic lookups.
- `.env` at repo root is respected by `backend/run.py` and `backend/app/__init__.py` via `python-dotenv`.

Testing & debug tips
- To test the recommend flow use the test client or the frontend payload shape: POST JSON to `/api/recommend` with `{"role": "Web Developer", "skills": ["js","html"]}`.
- When modifying AI prompts, assert that the returned content is strict JSON; callers expect JSON extraction (search for the brace `{`/`}` in `ai_skill_analyzer.py`).
- When adding heavy ML imports, prefer lazy imports inside functions to avoid increasing startup memory and breaking simple unit tests.

Where to look for examples
- Example endpoint and fallback patterns: [backend/app/routes.py](backend/app/routes.py)
- Production run config and Gunicorn binding: [Dockerfile](Dockerfile)
- Frontend expectations for host/port and keys: [frontend/script.js](frontend/script.js)
- Deterministic recommender & DB files: [backend/app/recommender.py](backend/app/recommender.py), [backend/app/skill_db.json](backend/app/skill_db.json)

If anything is unclear
- Ask for the specific area (API shape, env vars, AI prompt behavior, or frontend/backend integration) and I'll update this file with concrete examples or expanded snippets.
