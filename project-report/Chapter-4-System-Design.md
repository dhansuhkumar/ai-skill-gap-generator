# CHAPTER 4

# SYSTEM DESIGN

---

## 4.1 Introduction

System design translates the requirements identified in Chapter 3 into a concrete blueprint for implementation. This chapter begins with the overall system architecture, describing how the frontend, backend, and external services interact. It then details each backend module with its responsibilities and key functions. The database design section presents the Entity-Relationship diagram and table structures. The API design section documents all key endpoints with their request and response formats. Finally, the frontend component hierarchy illustrates how the React components are organised and how data flows between them.

---

## 4.2 System Architecture

The application follows a three-tier client-server architecture with clear separation of concerns between the presentation layer, business logic layer, and data layer. This architecture ensures maintainability, testability, and the ability to scale individual components independently.

```
+------------------------------------------------------------------------------------+
|                              USER'S BROWSER                                        |
|   +------------------------------------------------------------------+             |
|   |                    React.js Frontend (Vite)                       |             |
|   |  +----------+  +----------+  +----------+  +---------------+   |             |
|   |  |Dashboard |  |StepWizard|  |AI Chat   |  |Visualizations|   |             |
|   |  | (6 Steps)|  | (States) |  |Sidebar   |  | (Charts/TL)  |   |             |
|   |  +----------+  +----------+  +----------+  +---------------+   |             |
|   +------------------------------------------------------------------+             |
|                              | HTTPS REST (JSON)                                  |
+------------------------------|----------------------------------------------------+
                               |
                    +-----------v------------+
                    |   Flask Backend API    |
                    |   (Python 3.11+)       |
                    |                        |
                    |  +------------------+  |
                    |  | Auth Middleware  |  |
                    |  | (JWT Validation) |  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  | resume_parser.py |  |
                    |  | (PDF + Groq AI)  |  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  |github_analyzer.py|  |
                    |  | (GitHub REST API)|  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  |learning_path_ai.py| |
                    |  |(Groq RAG + Web)  |  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  | job_api_client.py |  |
                    |  |(3 Parallel APIs) |  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  |  ai/router.py   |  |
                    |  |(Groq → Gemini)  |  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  | web_search.py    |  |
                    |  | (DuckDuckGo DDGS)|  |
                    |  +------------------+  |
                    |                        |
                    |  +------------------+  |
                    |  |  dashboard_routes |  |
                    |  |  + routes.py     |  |
                    |  +------------------+  |
                    +-----------------------|----------------------------------------+
                                             |
                    +-----------------------v----------------------------------------+
                    |                    Supabase                                      |
                    |  +---------------+  +------------------+  +-----------------+  |
                    |  | PostgreSQL DB |  | Auth (JWT + RLS) |  | File Storage    |  |
                    |  | learning_paths|  |                  |  | (avatars, PDFs) |  |
                    |  | learning_prog |  |                  |  |                 |  |
                    |  | profiles     |  |                  |  |                 |  |
                    |  +---------------+  +------------------+  +-----------------+  |
                    +----------------------------------------------------------------+
                                             |
                    +-----------------------v----------------------------------------+
                    |               EXTERNAL SERVICES                                  |
                    |  +-----------+  +----------+  +-------+  +--------+  +------+ |
                    |  | Groq API  |  | GitHub   |  |Remotive|  | Jooble |  |Adzuna| |
                    |  |(LLM Inf.) |  | REST API|  |(Jobs)  |  |(Jobs) |  |(Jobs)| |
                    |  +-----------+  +----------+  +--------+  +--------+  +------+ |
                    +----------------------------------------------------------------+
```

### 4.2.1 Three-Tier Architecture Description

**Presentation Layer (Frontend):** The React.js frontend runs entirely in the user's browser and communicates with the backend exclusively through HTTPS REST API calls. The frontend manages the wizard state, renders the UI components, handles user input validation, and displays the AI chat sidebar. It does not perform any skill gap calculations or data processing—all computation happens on the backend.

**Business Logic Layer (Backend):** The Flask Python backend exposes REST API endpoints that correspond to the user's actions in the wizard. Each endpoint invokes one or more service modules to perform the actual work. The backend is stateless, meaning each request is independent and contains all information needed for processing (including the JWT token for authentication).

**Data Layer (Supabase):** Supabase serves as the data layer, providing PostgreSQL for structured data storage and JWT-based authentication. The learning_paths table stores the generated roadmaps, the learning_progress table tracks which steps the user has completed, and the profiles table stores user skill profiles. All database operations go through the Supabase client library, which handles connection pooling, query building, and authentication.

---

## 4.3 Backend Module Descriptions

The backend is organised into eight primary modules, each handling a distinct responsibility. The modules communicate through well-defined function interfaces and do not share global state (except for intentionally cached data).

### 4.3.1 Module 1: resume_parser.py

**Purpose:** Extract structured data from uploaded PDF résumés using a hybrid AI + keyword matching approach.

**Key Functions:**

`extract_resume_deep(file_stream) → dict`: The primary entry point. Accepts a file stream, extracts text using pdfminer.six, and returns a comprehensive dictionary with skills, education, experience, certifications, languages, total_experience_years, global_context, GitHub URL, LinkedIn URL, location (city, state, country), and a filled_percentage score indicating how many of the 7 data categories were successfully populated.

`_extract_deep_with_ai(text) → dict`: Sends the résumé text to the Groq LLM via the AI router with a structured JSON-extraction prompt. The prompt specifies the exact JSON schema expected, including nested objects for education and experience entries. Returns a dictionary parsed from the LLM's JSON response.

`_extract_skills_keyword(text) → List[str]`: Falls back to vocabulary-based extraction when AI is unavailable. Iterates through a TECH_SKILLS_VOCAB dictionary containing 500+ technology terms with their common variations (e.g., "python": ["python", "python3", "py"]). Returns a deduplicated list of matched skills.

`_detect_context(text) → str`: Classifies the résumé as "fresher", "experienced", or "neutral" by scanning for keywords like "intern", "fresher", "junior" (fresher indicators) or "senior", "lead", "5+ years" (experienced indicators).

`_extract_location_from_resume(text) → dict`: Searches the text for Indian city names using a curated list of 120+ cities. Returns the matched city, its state, and "India" as the country.

`_extract_urls(text) → dict`: Uses regex patterns to find GitHub and LinkedIn URLs in the text.

`_extract_years_of_experience(text) → Optional[float]`: Parses date ranges using regex patterns to estimate the total years of professional experience.

**Error Handling:** If PDF text extraction fails (corrupted file, image-only PDF), the function returns an empty deep result with filled_percentage=0. If the AI call fails, the function continues with keyword-based fallbacks. Logging is used throughout to aid debugging.

---

### 4.3.2 Module 2: github_analyzer.py

**Purpose:** Analyse a GitHub user's public repositories to generate fresher-friendly language proficiency scores.

**Key Classes:**

`GitHubAnalyzer`: The main analyser class. Initialised with an optional GitHub personal access token for higher rate limits. Uses a `requests.Session` for connection reuse.

`GitHubAnalysisResult`: A dataclass holding the complete analysis result: username, languages (dict of LanguageScore objects), total_repos, diversity_bonus, and error.

`RepoAnalysis`: A dataclass for per-repository analysis: name, language, stars, has_tests, has_devops, has_types, bonus_points.

**Key Functions:**

`analyze_profile(username) → GitHubAnalysisResult`: The main entry point. Fetches all public repositories using the GitHub API, then launches a ThreadPoolExecutor with 8 workers to analyse each repository's root directory contents in parallel. Each worker checks for tests/, Dockerfile, .github/, types.ts, and py.typed. Results are aggregated per language and scored.

`_calculate_language_score(lang_data: LanguageScore) → int`: Implements the fresher-friendly scoring formula:
- Base: 30 points (for having ≥1 repo)
- +5 per additional repo (max +20)
- +10 for tests folder
- +10 for Dockerfile or GitHub workflows
- +5 for type-safety files (types.ts, py.typed)
- +5 for repositories with >5 stars
- Diversity bonus: +10 to all languages if 3+ languages are present
- Final score clamped to [0, 100]

`analyze_github_profile(username, github_token) → dict`: The module-level convenience function that wraps GitHubAnalyzer, implements the 10-minute TTL cache using a module-level `_ANALYSIS_CACHE` dictionary, and returns a serialisable dictionary.

**Caching Strategy:** The cache uses a simple dictionary keyed by username. Each entry stores a tuple of (result_dict, timestamp). The TTL is 600 seconds (10 minutes). Only successful results are cached; errors cause a cache miss so the next attempt can try again.

---

### 4.3.3 Module 3: learning_path_ai.py

**Purpose:** Generate personalised day-by-day learning roadmaps using Groq LLM with RAG (Retrieval-Augmented Generation).

**Key Innovations:**

The module implements a "fast generation" architecture where the AI call is fired immediately using whatever web search results are already cached, while a background thread simultaneously fetches fresh web results for future use. This reduces perceived generation time from 40+ seconds to 5-8 seconds.

**Key Functions:**

`generate_ai_learning_path(skill, role, days, hours, pace, context, include_youtube) → dict`: The primary entry point. Checks the MD5 cache first. If cached, returns immediately. Otherwise, loads any pre-fetched web results from `_WEB_RESULTS`, builds the RAG prompt, calls the Groq LLM, parses the JSON response, and caches the result.

`_build_roadmap_prompt(skill, role, days, hours, pace, roadmap_results, web_results, youtube_results) → str`: Constructs the full prompt for the LLM. Includes the skill name, target role, time constraints, up to 4 roadmap links, up to 3 web resource links, and up to 2 YouTube embeds. Specifies the exact JSON structure expected in the response.

`_background_web_search(skill, role)`: A daemon thread function that searches DuckDuckGo for roadmaps, learning resources, and YouTube embeds for a given skill and role. Results are stored in the `_WEB_RESULTS` cache for use in the next learning path generation. This runs asynchronously and does not block the main thread.

`_generate_fallback_learning_path(skill, role, days) → dict`: A structured fallback when AI generation fails. Divides the timeline into 3 phases (Foundation, Intermediate, Advanced) with roughly equal day ranges. Each phase includes tasks, resources from DEFAULT_ROADMAPS, and a project suggestion.

`generate_ai_projects(skills, role, project_type, context) → List[dict]`: Generates portfolio project recommendations using the Groq LLM. Returns a list of project objects with title, description, and associated skills.

`prefetch_web_searches(skills, role)`: Called after learning path generation to warm the web search cache for the next set of skills, reducing future generation latency.

**MD5 Caching:** The cache key is generated by hashing the concatenation of skill, role, days, hours, and pace using MD5. This ensures that the same input parameters always produce the same cached output, regardless of when the request is made.

---

### 4.3.4 Module 4: job_api_client.py

**Purpose:** Aggregate real job listings from three independent APIs (Remotive, Jooble, Adzuna) with parallel querying, skill matching, experience filtering, and location-aware ranking.

**Key Functions:**

`search_jobs(skills, role, experience_level, location, max_results, user_location) → dict`: The primary entry point. Checks the 1-hour cache first. If cache miss, spawns three parallel threads using ThreadPoolExecutor(max_workers=3) and waits for all to complete. Merges results, deduplicates by URL, applies location boosting, and returns the ranked list.

`_search_remotive(skills, role, experience_level, max_results) → List[dict]`: Queries the Remotive API (free, no key required). Builds search queries from the user's top 2 skills and role. For freshers, adds "junior" and "entry" keywords. Calculates skill match score for each job, filters by experience level, sorts by score, and returns up to max_results.

`_search_jooble(skills, role, experience_level, location, max_results) → List[dict]`: Queries the Jooble API (requires free API key). Similar flow to Remotive but uses POST requests with JSON body.

`_search_adzuna(skills, role, experience_level, country, max_results) → List[dict]`: Queries the Adzuna API (requires free app_id and app_key). Optimised for the Indian job market (country="in"). Adds "fresher" or "senior" modifiers to queries based on experience level.

`_calculate_match_score(job_description, user_skills) → int`: Calculates 0-100 match score: 30 base + 15 per matched skill, capped at 95. Uses `_extract_skills_from_text` which scans the job description against the TECH_SKILLS vocabulary.

`_filter_experience_level(jobs, experience_level, user_skills) → List[dict]`: Filters jobs based on title and description keywords. Fresher filter excludes jobs with "senior", "lead", "5+ years", "manager". Experienced filter prefers jobs with those terms.

`_is_job_nearby(job_location, user_location) → bool`: Checks if a job's location is near the user's city using a city cluster mapping. For example, Gurgaon, Gurugram, Noida, Faridabad, and Ghaziabad all map to "Delhi NCR" and are considered near each other.

**Deduplication and Ranking:** All three API result sets are merged into a single list. The system tracks seen URLs in a set and only keeps the first occurrence of each URL. After deduplication, jobs are sorted by: (skill_match_score) + 30 (if nearby) + 15 (if remote).

---

### 4.3.5 Module 5: ai/router.py

**Purpose:** Provide a unified interface for AI inference across multiple providers with automatic fallback.

**Key Functions:**

`get_ai_response(prompt, requested_provider, is_json) → str`: The primary entry point. Tries providers in sequence: Groq (primary, llama-3.3-70b-versatile) → Google Gemini (gemini-1.5-flash) → Local fallback JSON. Each provider is wrapped in a try-except block so failures trigger automatic fallback.

**Provider Details:**
- **Groq:** Uses the groq library with the llama-3.3-70b-versatile model. Fast inference (~100 tokens/second). System prompt is set to "career development AI assistant." Temperature 0.7, max_tokens 2000.
- **Gemini:** Uses google.generativeai library with gemini-1.5-flash. Slightly slower but reliable. Same system prompt.
- **Local Fallback:** Returns a standardised JSON structure with empty arrays for skills, projects, and job matches. Ensures the frontend always receives a valid response structure.

**Retry Logic:** The current implementation does a single attempt per provider with immediate fallback. The error is logged but no exponential backoff is implemented at this layer (the caching layers provide the primary resilience mechanism).

---

### 4.3.6 Module 6: web_search.py

**Purpose:** Perform live web searches using DuckDuckGo to find current roadmaps, learning resources, and YouTube video embeds for skills and roles.

**Key Functions:**

`search_roadmaps(skill, max_results) → List[dict]`: Searches DuckDuckGo for authoritative learning roadmaps. Uses queries targeting roadmap.sh, GitHub awesome lists, and official documentation. Filters results to high-quality domains (github.com, roadmap.sh, freecodecamp.org, official documentation sites). Assigns authority scores and sorts by authority.

`search_learning_resources(skill, role, max_results) → List[dict]`: Searches for tutorials, courses, and articles for a specific skill-role combination. Results include title, URL, and snippet.

`search_youtube_embeds(skill, role, max_results) → List[dict]`: Uses DuckDuckGo's video search to find YouTube tutorials. Extracts video IDs from URLs (supports both youtube.com/watch?v= and youtu.be/ formats), constructs embed URLs, and returns thumbnail URLs for display.

`_is_high_quality_source(url) → bool`: Checks if a URL belongs to a trusted domain. Used to filter out low-quality or paywalled content from search results.

`_build_job_queries(role, experience_level, skills) → List[str]`: Constructs targeted search queries for job listings. Fresher searches include "entry level", "junior", "fresher" and exclude "senior", "lead". Experienced searches do the reverse.

**Caching:** All search functions use a module-level `_SEARCH_CACHE` dictionary with the query as the key. This prevents redundant searches during a single server session.

---

### 4.3.7 Module 7: dashboard_routes.py

**Purpose:** Handle Flask Blueprint routes for dashboard-specific operations including learning path persistence, progress tracking, GitHub analysis, and AI chat.

**Key Routes:**

`POST /api/get_dashboard_data`: Combines role analysis and learning path data to produce formatted dashboard data including skill comparison items, learning timeline with completion status, and summary statistics.

`POST /api/save_learning_progress`: Saves completed step indices for a skill. Uses Supabase if available, falls back to in-memory storage. Updates an existing record or inserts a new one depending on whether the user has prior progress for that skill.

`POST /api/save_learning_path`: Saves the complete learning path (target role, selected skills, full roadmap JSON) to Supabase or in-memory storage. Performs an upsert operation (update if exists, insert if not).

`GET /api/get_saved_learning_path`: Checks if a saved learning path exists for the authenticated user. Returns the full path data if found, or a has_saved_path=False flag if not.

`POST /api/analyze-github`: Receives a GitHub username, calls the github_analyzer module, and returns the complete analysis result with language scores, diversity bonus, and error status.

`POST /api/role-chat`: Receives a role name, conversation messages, and provider preference. Calls the Groq LLM with conversation history and role context to generate contextual AI chat responses.

---

### 4.3.8 Module 8: routes.py

**Purpose:** Handle the primary Flask Blueprint routes for the core wizard flow: résumé upload, skill gap analysis, job matching, and profile management.

**Key Routes:**

`POST /api/upload_resume`: Accepts a PDF file (multipart/form-data), validates file type and size, calls extract_resume_deep, and returns the parsed data including skills, education, experience, context, location, and filled_percentage.

`POST /api/analyze_gaps`: Protected route (requires JWT). Receives user skills and target role, calls the skill_analyzer module, and returns missing skills, required skills, match score, and job count.

`POST /api/job_matches`: Receives user skills, role, experience level, and location. Calls the job_api_client module and returns ranked job listings with match scores and source information.

`GET /api/profile`: Protected route. Returns the user's saved profile including role, skills, recommendations, experience level, and estimated years.

`POST /api/save_profile`: Protected route. Upserts the user's profile data to Supabase.

`GET /api/job_titles`: Returns job title suggestions based on a query parameter for autocomplete functionality.

---

## 4.4 Database Design

The database design uses Supabase (PostgreSQL) with Row-Level Security (RLS) policies to ensure data isolation between users. The schema consists of three primary tables and three supporting tables created through the Supabase SQL migration.

### 4.4.1 Entity-Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│     users       │         │  learning_paths  │         │ learning_progress│
│   (Supabase     │         │                  │         │                 │
│   Auth Table)   │         │                  │         │                 │
│                 │         │                  │         │                 │
│ id: UUID (PK)  │1───────N│ user_id: UUID(FK)│1───────N│ user_id: UUID   │
│ email: TEXT    │         │ id: UUID (PK)    │         │ skill_name: TEXT│
│ created_at: TST │         │ target_role: TEXT│         │ completed_steps │
│                 │         │ selected_skills │         │                 │
└─────────────────┘         │ learning_path   │         │ path_id: TEXT   │
                             │ created_at: TST │         │ week_number     │
                             │ updated_at: TST │         │ day_number      │
                             └─────────────────┘         │ completed_tasks │
                                                         └─────────────────┘

         ┌──────────────────┐
         │   user_profiles   │
         │                  │
         │ id: UUID (PK)    │
         │ user_id: UUID(FK)│
         │ skills: JSONB    │
         │ role: TEXT       │
         │ github_username  │
         │ experience_level │
         │ estimated_years  │
         └──────────────────┘
```

### 4.4.2 Table Definitions

**Table: learning_paths**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique path identifier |
| user_id | UUID | REFERENCES auth.users(id) ON DELETE CASCADE, NOT NULL | Owner's user ID |
| target_role | TEXT | NOT NULL | The job role the path targets |
| selected_skills | TEXT[] | DEFAULT '{}' | Array of skill names to learn |
| learning_path | JSONB | DEFAULT '{}' | Full learning path JSON with steps, resources, projects |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**RLS Policies:**
- SELECT: Users can only view their own paths (auth.uid() = user_id)
- INSERT: Users can only insert paths for themselves
- UPDATE: Users can only update their own paths
- DELETE: Users can only delete their own paths

**Table: learning_progress**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique progress identifier |
| user_id | UUID | REFERENCES auth.users(id) ON DELETE CASCADE | Owner's user ID |
| skill_name | TEXT | | Name of the skill being learned |
| completed_steps | INTEGER[] | DEFAULT '{}' | Array of completed step indices |
| path_id | TEXT | | Reference to the learning path |
| week_number | INTEGER | | Week number in the roadmap |
| day_number | INTEGER | | Day number within the week |
| completed_tasks | INTEGER[] | DEFAULT '{}' | Array of completed task indices |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Unique Constraint:** UNIQUE(user_id, skill_name) ensures only one progress record per skill per user.

**Indexes:**
- idx_learning_paths_user_id ON learning_paths(user_id)
- idx_learning_progress_user_id ON learning_progress(user_id)
- idx_learning_progress_skill ON learning_progress(skill_name)

---

## 4.5 API Design

The backend exposes a RESTful API with JSON request and response bodies. All endpoints that access user-specific data require a Bearer token in the Authorization header.

### 4.5.1 API Endpoint Specifications

**Endpoint 1: POST /api/upload-resume**

```
Description: Upload and parse a PDF résumé
Authentication: Not required (public endpoint)
Content-Type: multipart/form-data

Request:
  - file: PDF file (max 5MB)

Response 200:
  {
    "status": "ok",
    "parsed": {
      "skills": ["Python", "React", "SQL"],
      "education": [{"degree": "B.Tech", "institution": "IIT Delhi", "graduation_year": 2024}],
      "experience": [{"company": "Google", "title": "SDE Intern", "start_year": 2023, "end_year": 2024}],
      "certifications": ["AWS Solutions Architect"],
      "global_context": "fresher",
      "estimated_years": 0.5,
      "github_url": "https://github.com/johndoe",
      "linkedin_url": "https://linkedin.com/in/johndoe",
      "location": {"city": "Bangalore", "state": "Karnataka", "country": "India"},
      "filled_percentage": 71
    }
  }

Response 400:
  {"error": "Only PDF files are supported"}
Response 413:
  {"error": "File size exceeds 5MB limit"}
```

**Endpoint 2: POST /api/confirm-skills**

```
Description: Save user skills profile
Authentication: Required (Bearer token)
Content-Type: application/json

Request:
  {
    "skills": [{"name": "Python", "confidence": 85, "source": "resume"}],
    "role": "Full Stack Developer",
    "experience_level": "fresher",
    "estimated_years": 0
  }

Response 200:
  {"status": "ok", "profile_id": "uuid-string"}
```

**Endpoint 3: POST /api/analyze-role**

```
Description: Analyse skill gaps for a target role
Authentication: Required
Content-Type: application/json

Request:
  {
    "skills": ["Python", "JavaScript", "HTML", "CSS"],
    "target_role": "Full Stack Developer"
  }

Response 200:
  {
    "status": "ok",
    "missing_skills": ["React", "Node.js", "PostgreSQL", "Docker", "Git"],
    "required_skills": ["React", "Node.js", "PostgreSQL", "Docker", "Git", "Python", "JavaScript"],
    "match_score": 29,
    "user_skills_count": 4,
    "required_skills_count": 8,
    "matched_jobs_count": 1247
  }
```

**Endpoint 4: POST /api/generate-learning-path**

```
Description: Generate a complete learning path with resources, projects, and job listings
Authentication: Required
Content-Type: application/json

Request:
  {
    "target_role": "Full Stack Developer",
    "selected_skills": ["React", "Node.js", "Docker"],
    "time_commitment": "1 hour",
    "learning_pace": "Balanced",
    "duration": "3 months",
    "project_type": "portfolio",
    "include_youtube": true,
    "additional_context": "I prefer project-based learning"
  }

Response 200:
  {
    "status": "ok",
    "learning_path": {
      "summary": "Master Full Stack Development in 90 days",
      "skills": {
        "React": {
          "summary": "...",
          "steps": [{"day_from": 1, "day_to": 7, "title": "React Foundations", "tasks": [...], "resources": [...]}],
          "youtube_videos": [{"title": "...", "video_id": "...", "embed_url": "..."}]
        }
      },
      "projects": [{"title": "...", "description": "...", "skills": ["React", "Node.js"]}]
    },
    "jobs": {
      "jobs": [...],
      "total_found": 20,
      "sources": ["remotive", "adzuna"]
    }
  }
```

**Endpoint 5: GET /api/saved-path**

```
Description: Retrieve previously saved learning path
Authentication: Required

Response 200:
  {
    "status": "ok",
    "has_saved_path": true,
    "data": {
      "target_role": "Full Stack Developer",
      "selected_skills": ["React", "Node.js"],
      "learning_path": {...},
      "updated_at": "2025-03-15T10:30:00Z"
    }
  }

Response 200 (no saved path):
  {"status": "ok", "has_saved_path": false}
```

**Endpoint 6: POST /api/analyze-github**

```
Description: Analyse GitHub profile for fresher-friendly skill scores
Authentication: Required
Content-Type: application/json

Request:
  {"github_username": "johndoe"}

Response 200:
  {
    "status": "ok",
    "available": true,
    "username": "johndoe",
    "languages": {
      "Python": {"repos": 3, "score": 65, "has_tests": true, "has_devops": false, "has_types": false},
      "JavaScript": {"repos": 2, "score": 50, "has_tests": false, "has_devops": true, "has_types": false}
    },
    "total_repos": 5,
    "diversity_bonus": 10,
    "language_count": 2
  }
```

**Endpoint 7: POST /api/job-matches**

```
Description: Get ranked job listings from multiple APIs
Authentication: Not required (public endpoint)
Content-Type: application/json

Request:
  {
    "skills": ["Python", "React", "SQL"],
    "role": "Full Stack Developer",
    "experience_level": "fresher",
    "location": {"city": "Bangalore", "state": "Karnataka", "country": "India"}
  }

Response 200:
  {
    "jobs": [
      {
        "job_link": "https://remotive.com/remote-jobs/view/12345",
        "job_title": "Junior Full Stack Developer",
        "company": "TechCorp",
        "job_location": "Remote",
        "description": "We are looking for...",
        "salary": "₹6,00,000 - ₹8,00,000",
        "source": "remotive",
        "success_rate": 75,
        "required_skills": ["React", "Node.js", "PostgreSQL"],
        "location_match": false
      }
    ],
    "total_found": 20,
    "nearby_count": 8,
    "sources": ["remotive", "adzuna"]
  }
```

---

## 4.6 Frontend Component Hierarchy

The React frontend is structured as a component tree with clear parent-child relationships and data flow patterns. The main application entry point is App.jsx, which sets up routing and authentication context.

```
App.jsx
├── Navbar.jsx (navigation bar, auth status)
│
├── pages/
│   ├── ChatPage.jsx (AI chat interface)
│   ├── Profile.jsx (user profile management)
│   └── Dashboard.jsx (main 6-step wizard)
│       │
│       ├── StepProgressIndicator.jsx (5-step visual progress bar)
│       │
│       ├── StepSkills.jsx (skill input + résumé upload)
│       │   ├── SkillInput.jsx (text input with validation)
│       │   └── ResumeUpload.jsx (PDF upload component)
│       │
│       ├── StepRole.jsx (role selection with AI suggestions)
│       │
│       ├── StepMissingSkills.jsx (gap analysis results display)
│       │   └── SkillRadar.jsx (radar chart for skill comparison)
│       │
│       ├── StepLearningQuestions.jsx (time/pace/duration pickers)
│       │
│       ├── StepProjectPreferences.jsx (project type + YouTube toggle)
│       │
│       └── StepResults.jsx (learning path + jobs display)
│           ├── LearningTimeline.jsx (day-by-day task list)
│           ├── JobMatches.jsx (job listing cards)
│           └── SkillComparisonChart.jsx (bar chart: current vs required)
│
├── components/
│   ├── ui/
│   │   ├── AIChatSidebar.jsx (persistent contextual AI chat)
│   │   ├── AIChatInput.jsx (chat message input)
│   │   ├── CircularProgress.jsx (progress ring indicator)
│   │   └── Timeline.jsx (vertical timeline component)
│   │
│   ├── visualizations/
│   │   ├── DynamicDashboard.jsx (combined chart dashboard)
│   │   ├── SkillComparisonChart.jsx (reusable bar chart)
│   │   └── LearningTimeline.jsx (reusable timeline)
│   │
│   └── gamification/
│       ├── GamificationPanel.jsx (badges, streaks, points)
│       └── EnhancedLearningCard.jsx (animated progress card)
│
└── services/
    ├── api.js (Axios-based API client with interceptors)
    └── auth.js (Supabase auth wrapper)
```

**State Management:** The Dashboard component uses React useState hooks to manage all wizard state. No external state management library (Redux, Zustand) was needed because the state is localised to the Dashboard and its immediate children. Props are passed down through the component tree, and callback functions are passed up for state updates.

**Animation:** Framer Motion's AnimatePresence component wraps the step components to provide smooth fade-and-slide transitions when the wizard step changes. The motion.div component is used for individual element animations (staggered list items, progress indicators).

**API Communication:** All API calls go through the api.js service module, which wraps Axios with default configurations (base URL, timeout, headers). The auth.js service provides login/logout/registration functions using the Supabase client.

---

## 4.7 Summary

This chapter presented the complete system design for the AI-Powered Skill Gap Generator. The three-tier architecture was described with a detailed component diagram showing the frontend, backend, Supabase data layer, and external service integrations. Eight backend modules were documented with their key functions, responsibilities, and data flows. The database design included an ER diagram, table definitions, column types, constraints, RLS policies, and indexes. Seven API endpoints were documented with complete request and response schemas. The frontend component hierarchy illustrated how React components are organised and how data flows between them.

With the system design established, Chapter 5 moves to implementation, detailing the development environment, key algorithms, and the specific challenges encountered during the building of this system.

---
