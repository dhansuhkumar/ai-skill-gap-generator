# Changelog

## End-to-End Skill Gap Flow Implementation

### Overview
This update implements a complete end-to-end flow for the AI Skill Gap Generator with Supabase authentication, single prompt-box UI, and deterministic JSON API responses.

### Key Changes

#### Authentication
- **Supabase Integration**: Frontend now supports Supabase authentication with fallback to local auth
- **JWT Token Storage**: Changed from `token` to `jwtToken` in localStorage
- **Backend JWT Verification**: Updated to support both Supabase tokens and local JWT tokens

#### API Endpoints
- **Resume Upload** (`/api/upload_resume`): Now returns structured JSON with `parsed.skills`, `parsed.summary`, `parsed.experience`
- **Confirm Skills** (`/api/confirm_skills`): Accepts skills as objects with `name`, `confidence`, `source`; auto-resolves `profile_id`
- **Generate Learning Path** (`/api/generate_learning_path`): 
  - Returns strict JSON structure matching contract
  - Includes `videos` array when `include_youtube=true`
  - Computes and returns `matching_score` (0-100)
  - Tracks and returns `source` (provider used: gemini/openai/heuristic)
  - Supports provider selection (auto/gemini/openai/local)

#### Frontend Flow
- **3-Step Prompt Box Sequence**:
  1. Missing skills selection (comma-separated)
  2. Project preferences (type, days, hours/day)
  3. Additional context (optional)
- **Provider Selector**: Integrated into AnalysisConfiguration with Auto/Gemini/OpenAI/Local options
- **YouTube Toggle**: Toggle to include/exclude YouTube video recommendations
- **Optimistic UI**: Skills confirmation shows immediate feedback

#### Error Handling
- **401 Unauthorized**: Automatically redirects to login
- **429 Rate Limit**: Shows user-friendly message about fallback
- **400 Validation Errors**: Displays specific error messages
- **General Errors**: Graceful error handling with user feedback

### Environment Variables

Required in `.env`:
- `JWT_SECRET_KEY` (required)
- `SUPABASE_URL` (optional - for Supabase auth)
- `SUPABASE_KEY` (optional - for Supabase auth)
- `CORS_ALLOWED_ORIGINS` (optional - defaults to localhost ports)
- `GEMINI_API_KEY` (optional - for AI generation)
- `OPENAI_API_KEY` (optional - for AI generation)
- `YOUTUBE_API_KEY` (optional - for video recommendations)

### Frontend Dependencies
- Added `@supabase/supabase-js` for Supabase authentication

### Backend Dependencies
- `supabase` already in requirements-prod.txt

### Migration Notes
- Existing users: JWT tokens stored as `token` will need to re-authenticate
- Supabase users: Configure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in frontend `.env`
- Database: No schema changes required; `profiles` table auto-created if missing

### Testing
- Test full flow: Skills → Role → Analysis Configuration → Results
- Test Supabase auth (if configured) and local auth fallback
- Test provider selection and YouTube toggle
- Test error scenarios (401, 429, 400)

