# CHAPTER 8

# CONCLUSION AND FUTURE WORK

---

## 8.1 Introduction

This chapter concludes the project report by summarising the achievements of the AI-Powered Skill Gap Generator and Personalized Learning Path Recommender. It evaluates how the implemented system meets each of the five objectives stated in Chapter 1. The chapter then proposes a set of future enhancements that would extend the system's capabilities and address the limitations identified in Chapter 7.

---

## 8.2 Project Summary

The AI-Powered Skill Gap Generator and Personalized Learning Path Recommender is a full-stack web application that helps users identify skill gaps between their current abilities and their target job roles, and generates personalised learning roadmaps to bridge those gaps. The system was designed with a specific focus on the Indian technology job market, addressing the needs of freshers and early-career professionals who face the greatest information asymmetry in their career planning journey.

The application is built using React.js with Vite and Framer Motion for the frontend, Python Flask for the backend, Supabase for database and authentication, and Groq API for AI inference. It integrates with GitHub REST API for repository analysis, Remotive, Jooble, and Adzuna APIs for job aggregation, and DuckDuckGo for live web search augmentation.

The complete user journey consists of a 6-step wizard: Skills Input, Role Selection, Gap Identification, Learning Preferences, Project Preferences, and Results. Each step builds on the data from the previous step, creating a cohesive and guided experience. The persistent AI Chat Sidebar provides contextual help throughout the journey.

---

## 8.3 Evaluation Against Objectives

This section evaluates how the implemented system meets each of the five objectives defined in Chapter 1.

### Objective 1: Hybrid Résumé Parsing System

**Objective Statement:** To develop a hybrid résumé parsing system that uses both AI (Groq LLM) and keyword-based extraction to identify a user's skills, education, experience, certifications, and contact information from a PDF résumé, with automatic fallback mechanisms.

**Achievement:** The system implements a robust 3-layer extraction pipeline. The Groq LLM (llama-3.3-70b-versatile) extracts structured data from any résumé format using carefully engineered JSON-extraction prompts. Regex patterns handle specific fields (dates, URLs, city names) independently. A vocabulary-based keyword matcher with 500+ technology terms serves as the fallback when AI is unavailable. The system achieved 80-85% skill extraction accuracy on text-based PDFs and provides a filled_percentage score to indicate extraction confidence.

**Status:** Fully met. The hybrid approach provides both the intelligence needed for non-standard formats and the reliability of fallback mechanisms.

### Objective 2: GitHub Profile Analyser

**Objective Statement:** To implement a GitHub profile analyser that evaluates a user's public repositories for quality indicators such as test coverage, CI/CD implementation, type-safety files, and language diversity, generating a fresher-friendly score.

**Achievement:** The GitHub analyser implements a scoring model that starts at 30 points for any repository in a language and adds points for quality indicators (tests: +10, DevOps: +10, type-safety: +5, stars >5: +5, additional repos: up to +20). A diversity bonus of +10 is applied when the user has repositories in 3 or more languages. The system uses ThreadPoolExecutor with 8 parallel workers for fast repository analysis, and results are cached for 10 minutes per username.

**Status:** Fully met. The fresher-friendly scoring model was validated through user acceptance testing, with participants noting that the scores felt fair and achievable.

### Objective 3: Skill Gap Analysis Engine

**Objective Statement:** To build a skill gap analysis engine that compares a user's current skills against required skills for a target role, using web-search-augmented AI for up-to-date requirements.

**Achievement:** The skill gap engine uses the Groq LLM augmented with live DuckDuckGo search results to identify the current required skills for any target role. The system returns the missing skills as a list, a match score (0-100), the count of user skills, the count of required skills, and an estimated count of matching jobs in the market. The results are displayed with a visual gap breakdown showing current vs. required skills.

**Status:** Fully met. The web-augmented approach ensures that skill requirements reflect current market demands rather than outdated taxonomies.

### Objective 4: AI-Powered Learning Path Generator

**Objective Statement:** To create an AI-powered learning path generator that produces day-by-day personalised roadmaps constrained by the user's time preferences, including curated resources and portfolio projects.

**Achievement:** The learning path generator uses Retrieval-Augmented Generation (RAG) with a background pre-fetch architecture. Web searches run in daemon threads while users fill in preferences, and the AI call fires immediately using cached results. Learning paths include specific daily tasks, curated resource links (roadmaps, tutorials, documentation), YouTube video embeds, and hands-on project suggestions. The generator achieved an average response time of 6.2 seconds (target: 8 seconds) across 10 test cases.

**Status:** Fully met. The background pre-fetch architecture reduced generation latency by approximately 85% compared to a naive sequential approach.

### Objective 5: Multi-Source Job Aggregation

**Objective Statement:** To integrate a multi-source job aggregation system that fetches real job listings from Remotive, Jooble, and Adzuna APIs in parallel, filters by experience level, scores by skill match, and ranks by location proximity.

**Achievement:** The job aggregation system uses ThreadPoolExecutor(max_workers=3) to query all three APIs simultaneously. Each job is scored using the formula: 30 base + 15 per matched skill, capped at 95. Jobs are filtered by experience level (fresher/experienced/neutral) and ranked with location boosts (+30 for nearby, +15 for remote). The system deduplicates results by URL and caches them for 1 hour. Job aggregation achieved an average response time of 3.2 seconds (target: 4 seconds).

**Status:** Fully met. The parallel querying and multi-factor ranking provide users with relevant, actionable job listings.

---

## 8.4 Overall Project Outcome

The project successfully delivered a functional, deployed, and documented web application that addresses the identified problem of skill gap identification and personalised learning path generation. The system passed 94.1% of all test cases during the testing phase, including unit tests, integration tests, performance tests, and user acceptance tests.

The project demonstrated several best practices in software engineering: modular architecture with clear separation of concerns, caching at multiple layers for performance and resilience, graceful degradation through fallback mechanisms, parallel execution for I/O-bound operations, and comprehensive documentation throughout the codebase.

From a user impact perspective, the system provides freshers and early-career professionals with objective, AI-driven insights that were previously available only through expensive career counselling or self-directed research. The integration of real job listings creates a tangible connection between learning effort and career outcome, which is a significant motivational factor for sustained learning.

---

## 8.5 Future Enhancements

The following enhancements are proposed for future development based on user feedback, observed limitations, and potential market opportunities:

### 8.5.1 Resume Scoring and Ranking Against Job Descriptions

**Description:** Extend the system to allow users to upload a specific job description (from a job posting) and receive a score indicating how well their résumé matches the role requirements. The system would highlight which skills from the job description are present or missing in the user's profile, suggest specific résumé improvements, and prioritise the learning path to focus on the highest-impact missing skills.

**Technical Approach:** Use NLP similarity matching between the user's parsed résumé and the job description text. Calculate a match percentage based on weighted skill overlap, experience level alignment, and education requirements. Generate specific improvement suggestions using the Groq LLM with the job description as context.

**Priority:** High — directly addresses the most common user request during UAT.

### 8.5.2 LinkedIn API Integration

**Description:** Integrate LinkedIn OAuth to allow users to import their professional profile directly from LinkedIn. The integration would pull skills, education, work experience, certifications, and recommendations automatically, eliminating the need for manual entry or PDF upload. LinkedIn's "Open to Work" feature could also be used to suggest target roles based on the user's displayed career interests.

**Technical Approach:** Implement LinkedIn OAuth 2.0 flow using the LinkedIn API (requires LinkedIn Developer account and API approval). Parse the LinkedIn profile JSON to extract structured data matching the same schema used by the PDF parser. Use Supabase storage for caching imported profile data with user consent.

**Priority:** Medium — high user demand but LinkedIn API approval process can be lengthy.

### 8.5.3 Mobile Application (React Native)

**Description:** Develop a React Native mobile application that mirrors the web platform's functionality in a mobile-optimised interface. The mobile app would support push notifications for daily learning reminders, offline access to saved learning paths, and a simplified progress tracking interface. The AI chat could be reimagined as a voice assistant for hands-free guidance.

**Technical Approach:** Use React Native with Expo for cross-platform development. Share the existing Flask backend API with the mobile client. Implement local storage (AsyncStorage) for offline learning path access. Use a push notification service (Firebase Cloud Messaging or Expo Notifications) for daily reminders.

**Priority:** Medium — addresses the mobile UX limitations identified in UAT.

### 8.5.4 Fine-Tuned Domain-Specific LLM

**Description:** Fine-tune a smaller language model (such as Llama 3 8B or Mistral 7B) on a curated dataset of Indian technology résumés, job descriptions, and learning resources. The fine-tuned model would provide more accurate skill extraction for Indian résumé formats, more relevant learning path recommendations, and more contextual AI chat responses tailored to the Indian job market.

**Technical Approach:** Curate a training dataset of 5,000-10,000 Indian technology résumés with annotated skill tags, education fields, and experience levels. Use parameter-efficient fine-tuning (LoRA or QLoRA) to adapt the base model on a single GPU. Deploy the fine-tuned model on Groq or a dedicated inference endpoint for cost-effective serving.

**Priority:** Low-Medium — significant improvement in AI quality but requires substantial data collection and training effort.

### 8.5.5 Peer Learning Community Features

**Description:** Build a community layer on top of the learning platform where users pursuing the same learning path can connect, share resources, ask questions, and collaborate on projects. Features would include: discussion forums per skill topic, peer code review requests, study group formation based on similar learning paths, and a leaderboard tracking consistent daily learners.

**Technical Approach:** Add Supabase tables for community data (posts, comments, study_groups, peer_reviews). Implement real-time features using Supabase Realtime subscriptions for live chat and notifications. Add a "streak" system that tracks consecutive days of completed learning tasks, with badges and leaderboard rankings stored in the gamification tables.

**Priority:** Low — enhances engagement and retention but requires significant additional development and moderation effort.

### 8.5.6 Interview Preparation Module

**Description:** Add an interview preparation module that generates personalised interview questions based on the skills in the user's learning path. The module would include: technical questions for each skill (with difficulty levels), mock interview sessions with timed responses, feedback on response quality using the Groq LLM, and a list of companies known to ask specific technology questions.

**Technical Approach:** Use the Groq LLM to generate interview questions conditioned on the user's target role, selected skills, and experience level. Implement a timed mock interview interface with audio/video recording capability (using WebRTC). Use the LLM to evaluate response quality and provide constructive feedback. Store interview history and improvement metrics in Supabase.

**Priority:** Medium — natural extension of the learning-to-employment pipeline.

---

## 8.6 Concluding Remarks

The AI-Powered Skill Gap Generator and Personalized Learning Path Recommender represents a significant step forward in democratising career guidance for the Indian technology workforce. By combining the intelligence of large language models with the reliability of traditional extraction techniques, the system provides actionable, personalised guidance at a fraction of the cost of traditional career counselling.

The project demonstrated that a well-architected hybrid system—using AI where it adds the most value (understanding context, generating creative content) and structured code where it adds the most reliability (validation, scoring, caching)—can deliver a user experience that exceeds what either approach could achieve alone.

The modular architecture ensures that each component can be independently improved over time. The GitHub analyser can adopt new scoring criteria as industry practices evolve. The learning path generator can incorporate new resource types or delivery formats. The job aggregation system can add new APIs as they become available. This adaptability is essential for a system that operates in a domain as dynamic as technology careers.

The journey from identifying the problem to deploying a working solution has been both challenging and rewarding. The technical decisions made—background pre-fetching, parallel API aggregation, fresher-friendly scoring, RAG-based generation—were driven by specific user experience goals and validated through testing. The result is a system that not only meets its functional requirements but does so in a way that is fast, reliable, and accessible to its target users.

---

## APPENDIX A: ENVIRONMENT VARIABLE REFERENCE

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| FLASK_ENV | Environment context | development / production |
| FLASK_PORT | Port for Flask server | 5000 |
| SUPABASE_URL | Supabase project URL | https://xxxx.supabase.co |
| SUPABASE_KEY | Supabase anon/service key | eyJhbGc... |
| GROQ_API_KEY | Groq API key for LLM inference | gsk_xxxx |
| GEMINI_API_KEY | Google Gemini API key (fallback) | AIza... |
| GITHUB_TOKEN | GitHub personal access token | ghp_xxxx |
| JOOBLE_API_KEY | Jooble API key (free tier) | xxxxxxxx-xxxx-xxxx |
| ADZUNA_APP_ID | Adzuna application ID | xxxxxxxx |
| ADZUNA_APP_KEY | Adzuna application key | xxxxxxxx |
| CORS_ORIGINS | Allowed CORS origins (comma-separated) | http://localhost:5173,https://xxx.vercel.app |

### Frontend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| VITE_API_BASE_URL | Backend API URL | http://localhost:5000 / https://api.xxx.onrender.com |
| VITE_SUPABASE_URL | Supabase project URL | https://xxxx.supabase.co |
| VITE_SUPABASE_ANON_KEY | Supabase anonymous key | eyJhbGc... |

---

## APPENDIX B: DATABASE SCHEMA (Supabase SQL)

```sql
-- Learning Paths Table
CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    target_role TEXT NOT NULL,
    selected_skills TEXT[] DEFAULT '{}',
    learning_path JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning Progress Table
CREATE TABLE IF NOT EXISTS learning_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_name TEXT,
    completed_steps INTEGER[] DEFAULT '{}',
    path_id TEXT,
    week_number INTEGER,
    day_number INTEGER,
    completed_tasks INTEGER[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, skill_name)
);

-- Enable RLS
ALTER TABLE learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;

-- RLS Policies for learning_paths
CREATE POLICY "Users can view own learning paths" ON learning_paths
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own learning paths" ON learning_paths
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own learning paths" ON learning_paths
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own learning paths" ON learning_paths
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for learning_progress
CREATE POLICY "Users can view own progress" ON learning_progress
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own progress" ON learning_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own progress" ON learning_progress
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own progress" ON learning_progress
    FOR DELETE USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_id ON learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_skill ON learning_progress(skill_name);
```

---

## APPENDIX C: INSTALLATION AND SETUP INSTRUCTIONS

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git
- Supabase account (free tier)
- Groq API account (free tier)
- GitHub account (for GitHub token)
- (Optional) Jooble and Adzuna API keys (free tiers available)

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements-prod.txt
cp .env.example .env
# Edit .env with your API keys
python run.py
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your Supabase URL and key
npm run dev
```

### Docker Setup

```bash
docker-compose up --build
```

---

*End of Report*

---
