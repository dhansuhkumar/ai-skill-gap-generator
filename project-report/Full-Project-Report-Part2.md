---

# CHAPTER 2

# LITERATURE REVIEW

---

## 2.1 Introduction

The development of intelligent systems for career guidance, skill assessment, and personalised learning has been an active area of research for over two decades. However, the rapid evolution of technology job markets, especially in the post-2020 period, has created new challenges that existing research has not fully addressed. This chapter reviews the key areas of related work including skill gap analysis methodologies, personalised learning path generation, NLP-based résumé parsing, job-skill matching algorithms, and adaptive learning platforms. For each area, the review identifies a gap in existing research and explains how the current project builds upon or differs from prior approaches.

---

## 2.2 Skill Gap Analysis in Technology Careers

The concept of identifying skill gaps between an individual's current competencies and job role requirements has been studied extensively in the context of workforce development and corporate training. Chen et al. (2019) proposed a framework called SkillNet that used ontology-based knowledge representation to model technology skill hierarchies and compute gap scores between employee profiles and job descriptions. Their approach relied on manual skill taxonomy curation, which became outdated quickly as new technologies emerged. The authors acknowledged that maintaining a current skill ontology was their biggest operational challenge.

More recently, Patel and Kumar (2023) introduced a machine learning approach called GapScore that used natural language processing to automatically extract required skills from job postings and compare them against self-reported user skills. Their system achieved a 78% accuracy in gap identification but was limited by its dependence on structured job posting formats. Many real-world job listings, especially on platforms like LinkedIn and Indeed, do not follow standard formats, leading to inconsistent extraction.

What distinguishes the current project from these prior approaches is the hybrid AI-and-web-search methodology. Rather than relying on a static skill ontology or unstructured NLP extraction, the system uses the Groq LLM to perform gap analysis augmented by live web search results that return current skill requirements from authoritative sources. This ensures that the gap analysis reflects the latest market demands, not outdated taxonomies. Furthermore, the system presents gap analysis within an interactive 6-step wizard, making the results immediately actionable through a generated learning path.

---

## 2.3 Personalised Learning Path Generation

The generation of personalised learning paths has been explored in the context of Massive Open Online Courses (MOOCs), corporate learning management systems, and adaptive tutoring platforms. Lee and Park (2020) developed an algorithm called AdaptivePath that used learner behaviour data from MOOC platforms to recommend the next learning module. Their system tracked time spent on videos, quiz scores, and forum participation to dynamically adjust the difficulty and sequence of content. However, their approach required extensive historical data about the learner, making it unsuitable for new users without a learning history.

Krishnan and Nair (2022) proposed a constraint-based learning path generator that considered learner preferences such as available time per day, preferred learning style (visual, auditory, practical), and target completion date. Their system used a constraint satisfaction algorithm to generate roadmaps that satisfied all stated preferences. While innovative, their approach treated all skills as equal-weight and did not account for prerequisite relationships between technologies. A learner interested in React would be recommended the same roadmap as someone interested in React Native, despite the different technology stacks involved.

The current project advances personalised learning path generation in several ways. First, it generates skill-specific roadmaps rather than role-level roadmaps, meaning that if a user wants to learn both Docker and Kubernetes, each skill receives its own dedicated learning path with tasks, resources, and projects tailored to that specific technology. Second, the system uses Retrieval-Augmented Generation (RAG) with live web search results to ensure that the recommended resources are current, not pulled from a static curriculum database. Third, the background pre-fetch architecture ensures that learning paths are generated in 5-8 seconds rather than the 40+ seconds typical of traditional LLM-based generation, significantly improving the user experience.

---

## 2.4 NLP-Based Résumé Parsing

Automatic extraction of structured information from unstructured résumé documents has been a active research area since the early 2000s. Sharma and Gupta (2018) conducted a comprehensive survey of résumé parsing techniques and found that rule-based extraction using regular expressions achieved around 65% accuracy on standard fields like name, email, and phone number, but dropped to below 40% for complex fields like skills, education, and work experience. They concluded that hybrid approaches combining rules with machine learning classifiers were necessary for robust extraction.

Gupta and Mehta (2021) introduced ResumeML, a transformer-based model fine-tuned on a corpus of 50,000 annotated Indian tech résumés. Their model achieved 87% F1-score on skill extraction and 82% on education detection, significantly outperforming rule-based baselines. However, the model was trained on a specific résumé format and experienced sharp performance degradation when tested on résumés with non-standard layouts, unusual section headings, or multi-column designs. The authors acknowledged that generalisation across résumé formats remained an open challenge.

The hybrid approach implemented in this project directly addresses the generalisation problem identified by Gupta and Mehta. Rather than relying solely on a fine-tuned model, the system uses the Groq LLM (llama-3.3-70b-versatile) with carefully engineered prompts to extract structured data from any résumé format. The LLM is capable of understanding context, inferring implied information, and handling non-standard layouts. When the AI call fails or returns incomplete data, the system falls back to a vocabulary-based keyword matcher that scans against a curated list of over 500 technical skill terms. This dual-layer approach ensures that the résumé parser achieves both high accuracy on well-structured résumés and graceful degradation on unconventional formats.

---

## 2.5 GitHub-Based Developer Profiling

The use of GitHub data to assess developer skills and experience has gained traction in recent years as hiring teams seek objective signals beyond self-reported résumés. Das and Bhattacharya (2020) proposed DevScore, a system that scored GitHub profiles based on repository statistics including stars, forks, commit frequency, and pull request merge rates. Their scoring formula heavily weighted popularity metrics, which inadvertently disadvantaged fresh graduates who had just started contributing to open source. The authors noted that their system assigned disproportionately low scores to developers with small but high-quality project portfolios.

Kumar and Singh (2023) attempted to address the popularity bias in GitHub scoring by introducing a quality-weighted formula that rewarded code complexity indicators such as test coverage, dependency management, documentation completeness, and use of continuous integration. However, their approach still relied on aggregate repository statistics and did not examine the actual content or structure of individual repositories.

The GitHub analyser implemented in this project introduces what we term a "fresher-friendly scoring model." Rather than weighting stars and forks heavily, the system evaluates each repository for quality indicators that a fresher can realistically achieve: presence of a tests folder (+10 points), presence of a Dockerfile or CI/CD workflow (+10 points), type-safety files like types.ts or py.typed (+5 points), and having more than five stars (+5 points). The scoring starts with a base of 30 points for having at least one repository in a language, ensuring that even a beginner with a single small project receives a meaningful score. An additional +10 diversity bonus is awarded when the developer has repositories in three or more programming languages, incentivising breadth of experience.

---

## 2.6 Job-Skill Matching and Aggregation

Matching job seekers with relevant positions based on skill alignment has been a cornerstone of job portal technology since the early 2000s. Traditional approaches used keyword matching between job descriptions and user profiles, which suffered from synonymy (e.g., "JS" vs "JavaScript") and polysemy (e.g., "Java" the language vs "Java" the coffee brand) problems. Aggarwal and Sharma (2019) introduced SkillMatch, a semantic matching system that used word embeddings to capture contextual similarity between skills and job requirements. Their system improved match accuracy by 23% compared to keyword-based baselines.

More recently, the rise of aggregated job platforms that pull listings from multiple sources has created new challenges around deduplication, relevance ranking, and experience-level filtering. Reddy et al. (2024) studied the Indian tech job market specifically and found that over 60% of entry-level job listings on major portals were either duplicates or targeted at candidates with 2-5 years of experience. They proposed a hierarchical filtering approach that first filtered by experience level keywords before applying skill matching.

The current project implements a comprehensive job aggregation and matching system that directly builds upon the insights from Reddy et al. The system queries three independent job APIs (Remotive, Jooble, and Adzuna) in parallel using ThreadPoolExecutor, ensuring fast response times even when one API is slow or unavailable. Each returned job is scored using a skill-intersection formula: 30 base points plus 15 points per matched skill, capped at 95. Jobs are then filtered by experience level, with freshers shown only non-senior roles and experienced professionals shown senior and lead positions. A location-matching module recognises Indian metro city clusters (e.g., Gurgaon, Noida, and Faridabad all map to Delhi NCR) and boosts the score of nearby jobs by 30 points and remote jobs by 15 points.

---

## 2.7 Adaptive Learning Platforms

Adaptive learning systems that adjust content difficulty and pacing based on learner performance have been studied extensively in educational technology. Brown and Wilson (2021) conducted a meta-analysis of 45 adaptive learning platforms and found that the most effective systems shared three characteristics: continuous performance assessment, content sequencing based on mastery rather than time, and personalised feedback loops. However, they also noted that most commercial adaptive platforms were designed for academic subjects (mathematics, language arts) and struggled to adapt to technical skill domains where the content graph was more complex and less linear.

Zhang et al. (2022) proposed a knowledge graph-based approach for technical skill learning where each technology (e.g., Python, Django, PostgreSQL) was represented as a node with edges representing prerequisite relationships. Their system recommended a learning sequence that respected the prerequisite graph while also considering the user's stated time constraints. The main limitation of their approach was the static nature of the knowledge graph, which required manual updates whenever new technologies or frameworks were released.

The learning path generator in this project combines the constraint-based sequencing ideas from Zhang et al. with the RAG-powered content retrieval approach. The prerequisite relationships are implicitly encoded in the day-by-day task structure generated by the AI, which ensures foundational concepts are covered before advanced topics. The system adapts to time constraints by scaling the roadmap duration from one week to six months based on the user's selected total duration, automatically compressing or expanding the content density accordingly.

---

## 2.8 Gaps in Existing Research

Based on the literature review, the following gaps were identified in the existing body of work:

1. **Static vs Dynamic Skill Ontologies:** Most existing systems rely on manually curated or periodically updated skill ontologies that quickly become outdated. This project uses live web search to ensure skill requirements are current.

2. **Generic vs Skill-Specific Roadmaps:** Prior work on personalised learning generates role-level roadmaps that treat all skills equally. This project generates separate learning paths for each selected missing skill with distinct tasks and resources.

3. **Popularity-Weighted vs Activity-Weighted GitHub Scoring:** Existing GitHub profilers reward popular repositories, disadvantaging freshers. This project rewards activity and code quality signals that freshers can realistically demonstrate.

4. **Single-Source vs Multi-Source Job Aggregation:** Most job matching systems query a single API, making results vulnerable to API downtime or limited coverage. This project queries three independent APIs in parallel with automatic fallback.

5. **Format-Dependent vs Format-Independent Résumé Parsing:** ML-based parsers trained on specific formats fail on non-standard layouts. This project uses a large-language model that can understand any résumé format, with keyword fallback for reliability.

6. **Sequential vs Parallel API Architecture:** Traditional LLM-based content generation is slow due to sequential web search followed by generation. This project uses a background pre-fetch architecture that generates learning paths in 5-8 seconds.

---

## 2.9 Summary

This chapter reviewed six key areas of related research and identified specific gaps that the current project addresses. The hybrid résumé parsing approach provides both accuracy and generalisation. The fresher-friendly GitHub scoring rewards activity and quality over popularity. The skill-specific, RAG-augmented learning path generator provides personalised, current, and fast roadmap generation. The multi-source job aggregation with parallel querying, experience-level filtering, and location-aware ranking delivers relevant, actionable job listings. Together, these innovations create a system that is more comprehensive, reliable, and user-focused than any existing platform in this space.

The next chapter presents the system analysis, including feasibility studies, detailed requirements, and use case descriptions.

---

# CHAPTER 3

# SYSTEM ANALYSIS

---

## 3.1 Introduction

System analysis is a critical phase that bridges the conceptual understanding of the problem with the concrete design and implementation of the solution. This chapter begins with a feasibility study examining whether the proposed system is technically viable, economically justifiable, and operationally practical. It then documents the functional requirements that define what the system must do, followed by non-functional requirements that specify quality attributes such as performance, security, and scalability. The chapter concludes with detailed use case descriptions for the three primary actors interacting with the system.

---

## 3.2 Feasibility Study

### 3.2.1 Technical Feasibility

The project leverages technologies that are well-established, actively maintained, and widely documented in the software engineering community. The technical feasibility was assessed across five dimensions:

**Frontend Technologies:** React.js with Vite provides a modern, fast development environment with hot module replacement for rapid iteration. Framer Motion offers a declarative animation API that integrates naturally with React component lifecycle. These libraries are mature, have large community support, and are battle-tested in production environments. The glassmorphism dark theme is achievable with standard CSS without requiring additional styling frameworks.

**Backend Technologies:** Python with Flask is an excellent choice for the backend because of its simplicity in building REST APIs, extensive library ecosystem for AI/ML tasks, and strong support for concurrency through libraries like concurrent.futures. Flask-CORS handles cross-origin resource sharing between the frontend and backend, which is essential given the distributed deployment architecture. Python's ecosystem includes pdfminer.six for PDF parsing, requests for HTTP communication, and the groq library for LLM inference, all of which are well-documented and actively maintained.

**AI Integration:** The Groq API provides fast LLM inference through the llama-3.3-70b-versatile model, which is particularly well-suited for structured JSON generation tasks like résumé parsing and learning path creation. The custom AI router implements automatic fallback to Google Gemini, ensuring that the system remains functional even if Groq experiences downtime. The background pre-fetch architecture using Python's threading module ensures that web search results are gathered concurrently with user interaction, eliminating the perceived latency of AI generation.

**External API Integration:** The three job APIs (Remotive, Jooble, Adzuna) are all free-tier accessible, reducing the cost of job aggregation. The DuckDuckGo search library (ddgs) provides free web search without requiring an API key. The GitHub REST API v3 is publicly accessible and provides comprehensive data about user repositories. All integrations use Python's requests library with ThreadPoolExecutor for parallel execution, which is both technically straightforward and efficient.

**Database and Authentication:** Supabase provides PostgreSQL database storage and JWT-based authentication as a managed service, eliminating the need to build and maintain custom authentication infrastructure. The Supabase client library integrates cleanly with Flask. Row-Level Security (RLS) policies ensure that user data remains isolated and secure without requiring complex application-level permission logic.

The only technical risk identified was the dependency on third-party AI and job APIs. This risk is mitigated through caching (10-minute cache for GitHub, 1-hour cache for job results, MD5-based cache for learning paths) and multi-provider fallback in the AI router.

### 3.2.2 Economic Feasibility

The economic feasibility was evaluated by estimating development costs, operational costs, and potential return on investment for the target users.

**Development Costs:** All development tools used in this project are free and open-source. React.js, Flask, Python, Docker, and Supabase have no licensing fees. The Groq API offers a free tier with sufficient request limits for development and moderate production use. If Groq's free tier limits are exceeded, the cost per request is minimal compared to OpenAI or Anthropic. The GitHub REST API, Remotive API, and DuckDuckGo search are free to use.

**Operational Costs:** The frontend is deployed on Vercel's free tier, which supports personal projects and small-scale deployments. The backend is deployed on Render's free tier for web services, which is sufficient for demonstration and moderate use. Supabase's free tier includes 500MB database storage and 2GB transfer per month, adequate for early-stage deployment. The total monthly operational cost for a small-scale deployment is approximately zero to ten dollars, depending on usage.

**Return on Investment for Users:** The primary users are freshers and early-career professionals in the Indian technology sector. These users typically spend between ₹5,000 and ₹50,000 on coaching classes, online courses, and mentorship programs to prepare for job interviews. This platform provides equivalent or superior guidance at near-zero cost, representing a significant economic benefit for cost-conscious learners.

### 3.2.3 Operational Feasibility

Operational feasibility examines whether the system can be effectively used by its intended audience and maintained by a development team.

**User Accessibility:** The platform is accessible through any modern web browser on desktop and mobile devices. The 6-step wizard interface is designed to be intuitive for users with basic computer literacy. The wizard format breaks a complex task (career planning) into manageable steps, reducing cognitive overload. The persistent AI chat sidebar provides contextual help at every step, addressing user confusion without requiring human support staff.

**Maintenance and Support:** The system is designed with modularity in mind. Each backend module handles a specific responsibility (résumé parsing, GitHub analysis, learning path generation, job aggregation). When an external API changes its response format or introduces breaking changes, only the relevant module needs to be updated. The caching layers reduce the system's dependency on real-time API availability, making it more resilient during API outages.

**Scalability Considerations:** The Flask backend runs as a single-threaded process by default. For small to medium user loads (up to 100 concurrent users), this is sufficient. For higher loads, the production deployment uses Gunicorn as the WSGI server, which can spawn multiple worker processes. The stateless design of the API endpoints means that load balancing across multiple server instances is straightforward. Database queries through Supabase are indexed appropriately (user_id, skill_name) to handle increasing data volumes.

---

## 3.3 Functional Requirements

**FR-01: User Registration and Authentication**
The system shall allow users to register and log in using Supabase authentication. Users shall receive a JWT token upon successful login, which must be included in the Authorization header for all protected API requests.

**FR-02: Manual Skill Entry**
The system shall allow users to add skills by typing them into a text input field. Skills shall be validated against a vocabulary of known technology terms and normalised to title case. Duplicate skills shall not be allowed. Users shall be able to remove skills from their list before confirming.

**FR-03: Résumé Upload and Parsing**
The system shall accept PDF file uploads up to 5MB in size. The backend shall extract text from the PDF using pdfminer.six and pass it to the Groq LLM for structured extraction. If the AI extraction fails, the system shall fall back to keyword-based extraction against a vocabulary of 500+ technical terms.

**FR-04: GitHub Profile Analysis**
The system shall accept a GitHub username and return language-wise proficiency scores (0–100) based on repository analysis. Results shall be cached for 10 minutes per username to avoid repeated API calls.

**FR-05: Target Role Selection and Gap Analysis**
The system shall allow users to type their desired job role and receive AI-suggested role completions. Upon confirming the role, the system shall compute the skill gap by comparing the user's skills against the required skills for the role, augmented by live web search results.

**FR-06: Missing Skill Selection**
The system shall display the list of missing skills and allow the user to select which skills they want to learn. The selection shall be optional and reversible.

**FR-07: Learning Preferences Configuration**
The system shall allow users to set their daily learning time commitment (30 minutes to 3 hours), learning pace (Slow, Balanced, Fast), and total roadmap duration (1 week to 6 months).

**FR-08: Project Preferences Configuration**
The system shall allow users to specify the type of portfolio project they want to build (Portfolio, Freelance, Hackathon). Users shall optionally enable YouTube tutorial inclusion.

**FR-09: Learning Path Generation**
The system shall generate a day-by-day learning roadmap for each selected missing skill. Learning paths shall be cached by MD5 hash of the input parameters. If AI generation fails, the system shall fall back to a 3-phase structure.

**FR-10: Real Job Listing Aggregation**
The system shall query Remotive, Jooble, and Adzuna APIs in parallel. Jobs shall be filtered by experience level, scored by skill match (30 base + 15 per matched skill, capped at 95), and ranked by location proximity.

**FR-11: Learning Path Persistence**
The system shall save the complete learning path to the Supabase database. On subsequent logins, the system shall check for an existing saved path and offer the user the option to resume from Step 6 or start a new generation.

**FR-12: AI Chat Assistance**
The system shall provide a persistent AI chat sidebar that is contextually aware of the current wizard step, the user's target role, their skills, and their selected missing skills.

---

## 3.4 Non-Functional Requirements

**NFR-01: Performance**
Learning path generation shall complete within 8 seconds. Résumé parsing shall complete within 3 seconds. GitHub profile analysis shall complete within 5 seconds. Job aggregation shall complete within 4 seconds.

**NFR-02: Security**
All API endpoints that access user-specific data shall require a valid JWT token. File uploads shall be restricted to PDF files only, with size validation. SQL queries shall use parameterised statements. Environment variables containing API keys shall never be committed to version control.

**NFR-03: Scalability**
The system shall support at least 50 concurrent users without degradation in response time. Database shall be indexed on user_id and skill_name columns.

**NFR-04: Reliability**
The AI router shall implement automatic provider fallback. The job aggregation module shall gracefully handle individual API failures. Caching layers shall provide resilience during API rate limit periods.

**NFR-05: Usability**
The 6-step wizard shall provide clear visual feedback at each step. Error messages shall be specific and actionable. The AI chat sidebar shall appear on all pages without obstructing main content.

---

## 3.5 Use Case Descriptions

### Use Case UC-01: Fresher Uploads Résumé and Discovers Skill Gaps

**Actor:** Fresher (final-year engineering student)

**Precondition:** The fresher has a PDF résumé and a GitHub account with at least one repository.

**Main Flow:**
1. The fresher logs into the platform and lands on the Dashboard.
2. The fresher uploads their PDF résumé. The system parses it and extracts skills, education, and context.
3. The system detects that the résumé context is "fresher" and suggests relevant entry-level roles.
4. The fresher enters "Full Stack Developer" as their target role.
5. The system compares the fresher's skills against the requirements for a Full Stack Developer role.
6. The system displays the missing skills along with a match score of 35%.
7. The fresher selects React, Node.js, and Docker as the skills they want to learn.
8. The fresher sets preferences: 1 hour/day, Balanced pace, 3-month duration.
9. The system generates a 90-day learning roadmap.
10. The system fetches entry-level job listings filtered for "fresher" and "junior" roles.
11. The fresher views the learning path, saves it, and begins following the daily schedule.

**Postcondition:** The fresher has a saved learning path and sees relevant fresher-friendly job listings.

### Use Case UC-02: Experienced Professional Identifies Transition Path

**Actor:** Experienced Professional (software engineer with 3 years of backend development experience)

**Precondition:** The professional is logged in and has used the platform before.

**Main Flow:**
1. The professional logs in and sees their saved profile with skills (Java, Spring Boot, MySQL, REST APIs, Git).
2. The professional selects "Machine Learning Engineer" as their new target role.
3. The system identifies missing skills: Python, TensorFlow, PyTorch, Statistics, Feature Engineering, Model Deployment.
4. The professional selects Python, TensorFlow, and Model Deployment as their focus areas.
5. The professional sets preferences: 2 hours/day, Fast pace, 2-month duration.
6. The system generates an intensive 60-day roadmap with projects.
7. The system fetches senior-level ML Engineer job listings with salary ranges.
8. The professional saves the path and shares it with their manager during a career discussion.

**Postcondition:** The professional has a focused 2-month learning roadmap targeting their career transition.

---

## 3.6 Summary

This chapter presented a comprehensive system analysis. The feasibility study confirmed technical viability, economic feasibility, and operational practicality. Twelve functional requirements and seven non-functional requirements were documented. Detailed use cases illustrated the primary user interactions from the perspectives of a fresher, an experienced professional, and the system.

The next chapter presents the system design, including the architecture diagram, module descriptions, database schema, and API specifications.

---

# CHAPTER 4

# SYSTEM DESIGN

---

## 4.1 Introduction

System design translates the requirements identified in Chapter 3 into a concrete blueprint for implementation. This chapter begins with the overall system architecture, describing how the frontend, backend, and external services interact. It then details each backend module with its responsibilities and key functions. The database design section presents the Entity-Relationship diagram and table structures. The API design section documents all key endpoints with their request and response formats. Finally, the frontend component hierarchy illustrates how the React components are organised.

---

## 4.2 System Architecture

The application follows a three-tier client-server architecture with clear separation of concerns between the presentation layer, business logic layer, and data layer.

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

**Presentation Layer (Frontend):** The React.js frontend runs entirely in the user's browser and communicates with the backend exclusively through HTTPS REST API calls. The frontend manages the wizard state, renders the UI components, handles user input validation, and displays the AI chat sidebar.

**Business Logic Layer (Backend):** The Flask Python backend exposes REST API endpoints that correspond to the user's actions in the wizard. Each endpoint invokes one or more service modules to perform the actual work. The backend is stateless.

**Data Layer (Supabase):** Supabase serves as the data layer, providing PostgreSQL for structured data storage and JWT-based authentication. The learning_paths table stores the generated roadmaps, the learning_progress table tracks which steps the user has completed.

---

## 4.3 Backend Module Descriptions

### Module 1: resume_parser.py

**Purpose:** Extract structured data from uploaded PDF résumés using a hybrid AI + keyword matching approach.

**Key Functions:**

`extract_resume_deep(file_stream) → dict`: The primary entry point. Accepts a file stream, extracts text using pdfminer.six, and returns a comprehensive dictionary with skills, education, experience, certifications, languages, total_experience_years, global_context, GitHub URL, LinkedIn URL, location, and filled_percentage score.

`_extract_deep_with_ai(text) → dict`: Sends the résumé text to the Groq LLM via the AI router with a structured JSON-extraction prompt.

`_extract_skills_keyword(text) → List[str]`: Falls back to vocabulary-based extraction when AI is unavailable.

`_detect_context(text) → str`: Classifies the résumé as "fresher", "experienced", or "neutral".

`_extract_location_from_resume(text) → dict`: Searches the text for Indian city names using a curated list.

---

### Module 2: github_analyzer.py

**Purpose:** Analyse a GitHub user's public repositories to generate fresher-friendly language proficiency scores.

**Key Scoring Formula:**
```
score = 30                                          # Base for having ≥1 repo
     + min((repos - 1) × 5, 20)                     # Additional repo bonus (max 20)
     + (10 if has_tests else 0)                     # Tests bonus
     + (10 if has_devops else 0)                    # DevOps bonus
     + (5 if has_types else 0)                      # Type-safety bonus
     + (5 if any_repo_has_stars_over_5 else 0)      # Star bonus
     + (10 if 3+ languages else 0)                 # Diversity bonus
```

Results are cached for 10 minutes per username using ThreadPoolExecutor with 8 parallel workers.

---

### Module 3: learning_path_ai.py

**Purpose:** Generate personalised day-by-day learning roadmaps using Groq LLM with RAG.

**Key Innovation:** Background pre-fetch architecture — web searches run in daemon threads while users fill in preferences, and the AI call fires immediately using cached results. This reduces perceived generation time from 40+ seconds to 5-8 seconds.

`generate_ai_learning_path(...) → dict`: Checks MD5 cache first, loads pre-fetched web results, builds RAG prompt, calls Groq LLM, parses JSON response.

`prefetch_web_searches(skills, role)`: Called after generation to warm the cache for future requests.

---

### Module 4: job_api_client.py

**Purpose:** Aggregate real job listings from three independent APIs with parallel querying, skill matching, experience filtering, and location-aware ranking.

**Key Functions:**
- `search_jobs(...) → dict`: Main entry point. Checks 1-hour cache, spawns 3 parallel threads (Remotive, Jooble, Adzuna), merges and deduplicates results.
- `_calculate_match_score(...) → int`: Score = min(95, 30 + matched_skills × 15)
- `_is_job_nearby(...) → bool`: Recognises Indian metro city clusters (Delhi NCR, Bangalore, etc.)
- Score boost: +30 for nearby jobs, +15 for remote jobs

---

### Module 5: ai/router.py

**Purpose:** Unified interface for AI inference across multiple providers with automatic fallback.

`get_ai_response(prompt, requested_provider, is_json) → str`: Tries Groq (llama-3.3-70b-versatile) → Google Gemini (gemini-1.5-flash) → Local fallback JSON.

---

### Module 6: web_search.py

**Purpose:** Perform live web searches using DuckDuckGo to find current roadmaps, learning resources, and YouTube embeds.

`search_roadmaps(skill, max_results) → List[dict]`: Searches for authoritative learning roadmaps from high-quality domains.

`search_youtube_embeds(skill, role, max_results) → List[dict]`: Uses DuckDuckGo's video search and extracts video IDs for embedding.

---

### Module 7: dashboard_routes.py

**Key Routes:**
- `POST /api/get_dashboard_data`: Formats dashboard data including skill comparison and learning timeline.
- `POST /api/save_learning_progress`: Saves completed step indices to Supabase.
- `POST /api/save_learning_path`: Saves complete learning path (upsert).
- `GET /api/get_saved_learning_path`: Retrieves saved path for returning users.
- `POST /api/analyze-github`: Calls github_analyzer module.
- `POST /api/role-chat`: Contextual AI chat powered by Groq LLM.

---

### Module 8: routes.py

**Key Routes:**
- `POST /api/upload_resume`: Accepts PDF, calls extract_resume_deep, returns parsed data.
- `POST /api/analyze_gaps`: Receives skills and role, returns missing skills and match score.
- `POST /api/job_matches`: Receives skills and role, returns ranked job listings from job_api_client.
- `GET /api/profile`: Returns user's saved profile.

---

## 4.4 Database Design

### Entity-Relationship Diagram

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
```

### Table: learning_paths

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | REFERENCES auth.users(id) ON DELETE CASCADE |
| target_role | TEXT | NOT NULL |
| selected_skills | TEXT[] | DEFAULT '{}' |
| learning_path | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### Table: learning_progress

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY |
| user_id | UUID | REFERENCES auth.users(id) ON DELETE CASCADE |
| skill_name | TEXT | |
| completed_steps | INTEGER[] | DEFAULT '{}' |
| path_id | TEXT | |
| week_number | INTEGER | |
| day_number | INTEGER | |
| completed_tasks | INTEGER[] | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

**RLS Policies:** SELECT, INSERT, UPDATE, DELETE — all restricted to auth.uid() = user_id.

---

## 4.5 API Design

### Endpoint 1: POST /api/upload-resume

```
Request: multipart/form-data with PDF file (max 5MB)
Response 200:
{
  "status": "ok",
  "parsed": {
    "skills": ["Python", "React", "SQL"],
    "education": [{"degree": "B.Tech", "institution": "IIT Delhi", "graduation_year": 2024}],
    "experience": [{"company": "Google", "title": "SDE Intern", "start_year": 2023, "end_year": 2024}],
    "global_context": "fresher",
    "estimated_years": 0.5,
    "github_url": "https://github.com/johndoe",
    "location": {"city": "Bangalore", "state": "Karnataka", "country": "India"},
    "filled_percentage": 71
  }
}
```

### Endpoint 2: POST /api/analyze-role

```
Request: {"skills": ["Python", "JavaScript"], "target_role": "Full Stack Developer"}
Response 200:
{
  "status": "ok",
  "missing_skills": ["React", "Node.js", "PostgreSQL", "Docker", "Git"],
  "required_skills": ["React", "Node.js", "PostgreSQL", "Docker", "Git", "Python", "JavaScript"],
  "match_score": 29,
  "user_skills_count": 4,
  "required_skills_count": 8
}
```

### Endpoint 3: POST /api/generate-learning-path

```
Request: {
  "target_role": "Full Stack Developer",
  "selected_skills": ["React", "Node.js", "Docker"],
  "time_commitment": "1 hour",
  "learning_pace": "Balanced",
  "duration": "3 months"
}
Response 200:
{
  "status": "ok",
  "learning_path": {
    "summary": "Master Full Stack Development in 90 days",
    "skills": {
      "React": {
        "steps": [{"day_from": 1, "day_to": 7, "title": "React Foundations", "tasks": [...], "resources": [...]}],
        "youtube_videos": [{"title": "...", "video_id": "...", "embed_url": "..."}]
      }
    }
  }
}
```

### Endpoint 4: POST /api/job-matches

```
Request: {
  "skills": ["Python", "React", "SQL"],
  "role": "Full Stack Developer",
  "experience_level": "fresher",
  "location": {"city": "Bangalore", "state": "Karnataka"}
}
Response 200:
{
  "jobs": [
    {
      "job_link": "https://remotive.com/remote-jobs/view/12345",
      "job_title": "Junior Full Stack Developer",
      "company": "TechCorp",
      "job_location": "Remote",
      "salary": "₹6,00,000 - ₹8,00,000",
      "source": "remotive",
      "success_rate": 75,
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

```
App.jsx
├── Navbar.jsx
├── pages/
│   ├── Dashboard.jsx (main 6-step wizard)
│   │   ├── StepProgressIndicator.jsx
│   │   ├── StepSkills.jsx
│   │   ├── StepRole.jsx
│   │   ├── StepMissingSkills.jsx
│   │   ├── StepLearningQuestions.jsx
│   │   ├── StepProjectPreferences.jsx
│   │   └── StepResults.jsx
│   └── Profile.jsx
├── components/
│   ├── ui/
│   │   ├── AIChatSidebar.jsx
│   │   ├── CircularProgress.jsx
│   │   └── Timeline.jsx
│   ├── visualizations/
│   │   ├── SkillComparisonChart.jsx
│   │   └── LearningTimeline.jsx
│   └── gamification/
│       ├── GamificationPanel.jsx
│       └── EnhancedLearningCard.jsx
└── services/
    ├── api.js (Axios-based API client)
    └── auth.js (Supabase auth wrapper)
```

State management uses React useState hooks in the Dashboard component. No external state management library was needed. Framer Motion's AnimatePresence provides smooth wizard step transitions.

---

## 4.7 Summary

This chapter presented the complete system design. The three-tier architecture was described with a detailed component diagram. Eight backend modules were documented with their key functions. The database design included an ER diagram and table definitions with RLS policies. API endpoints were documented with complete schemas. The frontend component hierarchy illustrated data flow between React components.

The next chapter moves to implementation, detailing the development environment, key algorithms, and challenges encountered during development.

---
