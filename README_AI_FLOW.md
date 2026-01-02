# AI Skill Gap Generator - End-to-End Flow

This implementation provides a complete end-to-end flow with Supabase authentication, single prompt-box UI, and deterministic JSON API responses.

## Setup Instructions

### Backend
1.  Ensure virtual environment is active:
    ```bash
    cd backend
    # Activate venv (e.g., source venv/bin/activate on Linux/Mac, or venv\Scripts\activate on Windows)
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements-prod.txt
    ```

3.  **Environment Variables**: Create a `.env` file in the backend directory with:
    ```env
    # Required
    JWT_SECRET_KEY=your_secure_random_jwt_secret_key_here
    
    # Optional - Supabase Authentication
    SUPABASE_URL=your_supabase_project_url
    SUPABASE_KEY=your_supabase_anon_key
    
    # Optional - CORS Configuration
    CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
    
    # Optional - AI Provider API Keys
    GEMINI_API_KEY=your_gemini_api_key
    OPENAI_API_KEY=your_openai_api_key
    
    # Optional - YouTube API Key (for video recommendations)
    YOUTUBE_API_KEY=your_youtube_api_key
    ```

4.  **Database**: The app will auto-create SQLite database and tables if they don't exist.

5.  Run the backend:
    ```bash
    python backend/run.py
    # Or
    python backend/main.py
    ```

### Frontend
1.  Install dependencies:
    ```bash
    cd frontend
    npm install
    ```

2.  **Environment Variables**: Create a `.env` file in the frontend directory (optional for Supabase):
    ```env
    VITE_SUPABASE_URL=your_supabase_project_url
    VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
    ```
    If not configured, the app will fall back to local authentication.

3.  Run dev server:
    ```bash
    npm run dev
    ```

## Usage Flow

1.  **Login/Register**: 
    - If Supabase is configured, use email/password
    - Otherwise, use local authentication with username/password

2.  **Step 1 - Skills**: 
    - Add skills manually using the tag input
    - OR upload a PDF resume to auto-extract skills
    - Click "Next" to confirm and save skills

3.  **Step 2 - Target Role**: 
    - Select a predefined role or enter a custom role
    - Click "Next" to analyze skill gaps

4.  **Step 3 - Analysis Configuration**:
    - **Missing Skills**: Agent shows missing skills. Type which ones you want to learn (comma-separated)
    - **Project Preferences**: Enter project type and timeline (e.g., "portfolio, 30 days, 1.5 hours/day")
    - **Additional Context**: Optional text area for extra information
    - **AI Provider**: Select Auto/Gemini/OpenAI/Local
    - **YouTube Videos**: Toggle to include/exclude video recommendations
    - Click "Start Analysis"

5.  **Step 4 - Results**: 
    - View personalized learning path with:
      - Per-skill learning steps with day ranges
      - Recommended projects
      - YouTube video tutorials (if enabled)
      - Matching score and provider used

## API Contract

### POST `/api/confirm_skills`
**Request:**
```json
{
  "skills": [
    {"name": "React", "confidence": 80, "source": "user"}
  ]
}
```

**Response:**
```json
{
  "status": "ok",
  "saved": [...]
}
```

### POST `/api/generate_learning_path`
**Request:**
```json
{
  "profile_id": 1,
  "target_role": "Full Stack Developer",
  "selected_skills": ["React", "SQL"],
  "days": 30,
  "daily_hours": 1.5,
  "project_type": "portfolio",
  "include_youtube": true,
  "additional_context": "I want to focus on backend too",
  "provider": "auto"
}
```

**Response:**
```json
{
  "status": "ok",
  "learning_path": {
    "summary": "30-day plan",
    "skills": {
      "React": {
        "summary": "...",
        "steps": [
          {
            "day_from": 1,
            "day_to": 5,
            "title": "...",
            "tasks": ["..."],
            "project": "...",
            "resources": ["..."]
          }
        ]
      }
    },
    "projects": [
      {"title": "...", "description": "...", "skills": ["..."]}
    ],
    "videos": [
      {"title": "...", "url": "https://youtu.be/..."}
    ]
  },
  "matching_score": 72,
  "source": "gemini"
}
```

## Troubleshooting

*   **CORS Errors**: Ensure `CORS_ALLOWED_ORIGINS` in backend `.env` includes your frontend URL
*   **401 Unauthorized**: Check that JWT token is stored as `jwtToken` in localStorage. Re-login if needed.
*   **JSON Errors**: Check backend logs. The AI is instructed to return strict JSON, but occasionally models hallucinate. The fallback logic will handle most cases.
*   **Rate Limits (429)**: If Gemini/OpenAI returns 429, the system temporarily locks it out for 5 minutes and tries the next provider or heuristic fallback.
*   **Supabase Auth Issues**: Ensure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set in frontend `.env`. If not configured, the app falls back to local auth.
*   **Profile Not Found**: The backend auto-creates profiles. If you see this error, ensure the user_id from JWT matches the profile's user_id.

## Architecture

- **Frontend**: React with Vite, uses Supabase client for auth
- **Backend**: Flask with SQLite, supports Supabase JWT verification
- **AI Providers**: Gemini (priority) → OpenAI → Heuristic fallback
- **Database**: SQLite with `profiles`, `skills`, `profile_skills` tables
