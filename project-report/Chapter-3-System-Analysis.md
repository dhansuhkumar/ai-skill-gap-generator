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

**Cost Comparison with Alternatives:**

| Component | Traditional Approach | This Project |
|-----------|---------------------|--------------|
| Skill Gap Analysis | Career counselling (₹2,000–₹10,000) | Free |
| Learning Resources | Paid courses (₹1,000–₹20,000) | Curated free resources |
| Job Search | Recruiters/consultants (₹5,000–₹50,000) | Aggregated free listings |
| Résumé Review | Professional review (₹500–₹3,000) | Free AI-powered extraction |
| **Total** | **₹8,500–₹83,000** | **Free–₹10/month** |

The economic feasibility is strongly positive, particularly for the target demographic of Indian engineering students and freshers.

### 3.2.3 Operational Feasibility

Operational feasibility examines whether the system can be effectively used by its intended audience and maintained by a development team.

**User Accessibility:** The platform is accessible through any modern web browser on desktop and mobile devices. The 6-step wizard interface is designed to be intuitive for users with basic computer literacy. The wizard format breaks a complex task (career planning) into manageable steps, reducing cognitive overload. The persistent AI chat sidebar provides contextual help at every step, addressing user confusion without requiring human support staff.

**Maintenance and Support:** The system is designed with modularity in mind. Each backend module handles a specific responsibility (résumé parsing, GitHub analysis, learning path generation, job aggregation). When an external API changes its response format or introduces breaking changes, only the relevant module needs to be updated. The caching layers reduce the system's dependency on real-time API availability, making it more resilient during API outages.

**Scalability Considerations:** The Flask backend runs as a single-threaded process by default. For small to medium user loads (up to 100 concurrent users), this is sufficient. For higher loads, the production deployment uses Gunicorn as the WSGI server, which can spawn multiple worker processes. The stateless design of the API endpoints means that load balancing across multiple server instances is straightforward. Database queries through Supabase are indexed appropriately (user_id, skill_name) to handle increasing data volumes.

**Deployment Complexity:** Docker and Docker Compose configuration files are provided, allowing the entire stack to be launched with a single command. The environment variable configuration is documented in both the README and in Appendix A. The frontend-backend communication is standard HTTPS REST with JSON payloads, which is universally understood and easy to debug.

**Training Requirements:** Users do not require any formal training to use the platform. The wizard interface guides them step-by-step, and the AI chat sidebar provides explanations for any technical terms they may not understand. For the development team, the codebase is well-structured with clear module boundaries, inline documentation, and logging at critical decision points.

---

## 3.3 Functional Requirements

The functional requirements specify the specific behaviours and features that the system must implement to satisfy user needs. The following requirements were identified through analysis of the user journey and validated against the project objectives.

**FR-01: User Registration and Authentication**
The system shall allow users to register and log in using Supabase authentication. Users shall receive a JWT token upon successful login, which must be included in the Authorization header for all protected API requests. The system shall validate the JWT token on each protected route and return a 401 Unauthorized response for invalid or expired tokens.

**FR-02: Manual Skill Entry**
The system shall allow users to add skills by typing them into a text input field. Skills shall be validated against a vocabulary of known technology terms and normalised to title case (e.g., "java script" becomes "Java Script"). Duplicate skills shall not be allowed. Users shall be able to remove skills from their list before confirming.

**FR-03: Résumé Upload and Parsing**
The system shall accept PDF file uploads up to 5MB in size. The backend shall extract text from the PDF using pdfminer.six and pass it to the Groq LLM for structured extraction. The extracted data shall include skills (as a list), education (as a list of objects with degree, institution, and year), experience (as a list of objects with company, title, start year, and end year), certifications, GitHub URL, LinkedIn URL, total experience years, and global context (fresher/experienced/neutral). If the AI extraction fails, the system shall fall back to keyword-based extraction against a vocabulary of 500+ technical terms.

**FR-04: GitHub Profile Analysis**
The system shall accept a GitHub username and return language-wise proficiency scores (0–100) based on repository analysis. The scoring shall reward quality indicators (tests, Docker, CI/CD, type-safety files) and diversity (multiple languages), starting with a base of 30 points for any repository in a language. Results shall be cached for 10 minutes per username to avoid repeated API calls.

**FR-05: Target Role Selection and Gap Analysis**
The system shall allow users to type their desired job role and receive AI-suggested role completions. Upon confirming the role, the system shall compute the skill gap by comparing the user's skills against the required skills for the role, augmented by live web search results. The system shall return the missing skills as a list, a match score (0–100), the count of user skills, and the count of required skills.

**FR-06: Missing Skill Selection**
The system shall display the list of missing skills identified in FR-05 and allow the user to select which skills they want to learn. The selection shall be optional (users can skip any skill) and reversible (users can change selections before proceeding). The selected skills shall be passed forward to the learning path generation step.

**FR-07: Learning Preferences Configuration**
The system shall allow users to set their daily learning time commitment (30 minutes, 1 hour, 2 hours, 3 hours), learning pace (Slow, Balanced, Fast), and total roadmap duration (1 week, 2 weeks, 1 month, 3 months, 6 months). These preferences shall constrain the generated learning path to fit within the stated time boundaries.

**FR-08: Project Preferences Configuration**
The system shall allow users to specify the type of portfolio project they want to build (Portfolio, Freelance, Hackathon). Users shall optionally enable YouTube tutorial inclusion in their learning path. Users may also provide additional context as free-form text that will be included in the learning path generation prompt.

**FR-09: Learning Path Generation**
The system shall generate a day-by-day learning roadmap for each selected missing skill, constrained by the user's time preferences. Each day or phase shall include specific tasks, curated resource links (articles, documentation, tutorials), and at least one hands-on project. Learning paths shall be cached by MD5 hash of the input parameters to avoid regenerating identical paths. If AI generation fails, the system shall fall back to a 3-phase structure (Foundation, Intermediate, Advanced).

**FR-10: Real Job Listing Aggregation**
The system shall query Remotive, Jooble, and Adzuna APIs in parallel and merge the results. Each job listing shall include the job title, company name, job location, description snippet, salary range (if available), and a direct application link. Jobs shall be filtered by experience level, scored by skill match (30 base + 15 per matched skill, capped at 95), and ranked by a combination of skill score, location proximity, and remote-work status.

**FR-11: Learning Path Persistence**
The system shall save the complete learning path (target role, selected skills, generated roadmap, job listings) to the Supabase database. On subsequent logins, the system shall check for an existing saved path and offer the user the option to resume from Step 6 or start a new generation.

**FR-12: AI Chat Assistance**
The system shall provide a persistent AI chat sidebar that is contextually aware of the current wizard step, the user's target role, their skills, and their selected missing skills. The chat shall be powered by the Groq LLM through the AI router and shall handle conversational queries about technology concepts, learning strategies, and career advice.

---

## 3.4 Non-Functional Requirements

Non-functional requirements define the quality attributes of the system that determine how well it performs its functions, rather than what specific functions it performs.

**NFR-01: Performance**
Learning path generation shall complete within 8 seconds under normal API conditions. Résumé parsing shall complete within 3 seconds for files up to 5 pages. GitHub profile analysis shall complete within 5 seconds for profiles with up to 50 repositories. Job aggregation shall complete within 4 seconds, assuming all three APIs respond within their typical latency. The frontend shall render the initial page within 2 seconds on a standard broadband connection.

**NFR-02: Security**
All API endpoints that access user-specific data shall require a valid JWT token in the Authorization header. The JWT token shall be validated on the server side before processing any request. File uploads shall be restricted to PDF files only, with size validation on both client and server. SQL queries shall use parameterised statements to prevent injection attacks. Environment variables containing API keys shall never be committed to the version control repository. CORS shall be configured to whitelist only the frontend domain in production.

**NFR-03: Scalability**
The system shall support at least 50 concurrent users without degradation in response time. The database shall be indexed on user_id and skill_name columns to ensure fast lookups as the user base grows. The job search and GitHub analysis caching layers shall reduce the load on external APIs during peak usage.

**NFR-04: Reliability and Availability**
The AI router shall implement automatic provider fallback (Groq → Gemini → Local fallback) to ensure that the system remains functional even when a primary provider is down. The job aggregation module shall gracefully handle individual API failures by continuing with results from available sources. The 10-minute GitHub cache and 1-hour job cache shall provide resilience during API rate limit periods.

**NFR-05: Usability**
The 6-step wizard shall provide clear visual feedback at each step, indicating the current step, completed steps, and remaining steps. Error messages shall be specific and actionable (e.g., "Please enter at least one skill" rather than "Validation failed"). The AI chat sidebar shall appear on all pages and shall not obstruct the main content area.

**NFR-06: Maintainability**
The codebase shall follow a modular architecture with clear separation of concerns. Each backend module shall have a single, well-defined responsibility. The code shall include docstrings for all public functions and logging statements at critical decision points. The frontend components shall be organised by feature (Dashboard, UI components, Visualizations, Gamification).

**NFR-07: Compatibility**
The frontend shall support the latest two major versions of Google Chrome, Mozilla Firefox, Microsoft Edge, and Apple Safari. The system shall function on desktop browsers with screen widths of 1024px and above. Mobile responsiveness shall be considered in the CSS layout but is not a primary requirement for the current version.

---

## 3.5 Use Case Descriptions

The following use case descriptions model the interactions between the system and its three primary actors: the Fresher, the Experienced Professional, and the System Administrator (represented by automated processes).

### Use Case UC-01: Fresher Uploads Résumé and Discovers Skill Gaps

**Actor:** Fresher (final-year engineering student with no full-time work experience)

**Precondition:** The fresher has a PDF résumé and a GitHub account with at least one repository.

**Main Flow:**
1. The fresher logs into the platform and lands on the Dashboard.
2. The fresher uploads their PDF résumé. The system parses it and extracts skills, education, and context.
3. The system detects that the résumé context is "fresher" and suggests relevant entry-level roles.
4. The fresher enters "Full Stack Developer" as their target role.
5. The system compares the fresher's skills (Python, HTML, CSS, basic JavaScript) against the requirements for a Full Stack Developer role.
6. The system displays the missing skills (React, Node.js, PostgreSQL, Docker, Git) along with a match score of 35%.
7. The fresher selects React, Node.js, and Docker as the skills they want to learn.
8. The fresher sets preferences: 1 hour/day, Balanced pace, 3-month duration.
9. The system generates a 90-day learning roadmap with daily tasks for React, Node.js, and Docker.
10. The system fetches entry-level job listings from Remotive and Adzuna filtered for "fresher" and "junior" roles.
11. The fresher views the learning path, saves it, and begins following the daily schedule.

**Alternate Flow A (GitHub Analysis):**
At Step 2, the fresher also provides their GitHub username. The system analyses their repositories, finds a Python project with a tests folder and a Dockerfile, and awards them a Python score of 65/100. This GitHub score is used to supplement the skill profile.

**Alternate Flow B (Resume AI Failure):**
At Step 2, the Groq API is unavailable. The system falls back to keyword extraction and returns a partial result with 4 skills detected. The fresher manually adds the remaining skills.

**Postcondition:** The fresher has a saved learning path and sees relevant fresher-friendly job listings.

---

### Use Case UC-02: Experienced Professional Identifies Transition Path

**Actor:** Experienced Professional (software engineer with 3 years of backend development experience)

**Precondition:** The professional is logged in and has used the platform before, so their skills profile is saved.

**Main Flow:**
1. The professional logs in and sees their saved profile with skills (Java, Spring Boot, MySQL, REST APIs, Git).
2. The professional selects "Machine Learning Engineer" as their new target role.
3. The system identifies missing skills: Python, TensorFlow, PyTorch, Statistics, Feature Engineering, Model Deployment.
4. The professional selects Python, TensorFlow, and Model Deployment as their focus areas.
5. The professional sets preferences: 2 hours/day, Fast pace, 2-month duration (targeting an immediate job switch).
6. The system generates an intensive 60-day roadmap with projects like building an image classifier and deploying it as a REST API.
7. The system fetches senior-level ML Engineer job listings with salary ranges above ₹15 LPA.
8. The professional saves the path and shares it with their manager during a career discussion.

**Alternate Flow (Skill Override):**
At Step 4, the system shows that the professional already knows Java, which is useful for Spark-based ML. The professional chooses to include Java in their project recommendations. The system generates a project that uses Java with Apache Spark for distributed ML processing.

**Postcondition:** The professional has a focused 2-month learning roadmap targeting their career transition and sees senior ML Engineer positions.

---

### Use Case UC-03: System Processes Job Aggregation

**Actor:** System (automated background process triggered by user request)

**Precondition:** A user has completed the skill gap analysis and selected their missing skills.

**Main Flow:**
1. The system receives a job search request with the user's skills, target role, experience level (fresher/experienced/neutral), and location.
2. The system checks the 1-hour job cache for a matching query. If found, return cached results immediately.
3. If no cache hit, the system spawns three parallel threads: Thread A queries Remotive, Thread B queries Jooble (if API key is present), Thread C queries Adzuna (if API keys are present).
4. Each thread collects job listings, calculates a skill match score for each listing, and filters by experience level.
5. The threads complete and return their results. The system merges all listings, deduplicates by URL, and removes any entries missing application links.
6. The system applies location matching: jobs within the user's city cluster receive a +30 score boost, and remote jobs receive a +15 boost.
7. The merged and ranked results are cached for 1 hour and returned to the user.

**Alternate Flow (API Failure):**
If Jooble and Adzuna APIs fail (rate limit, invalid keys), the system continues with Remotive results alone. The response indicates which sources were used, and the user is informed that results may be incomplete.

**Postcondition:** The user receives a list of 20 ranked job listings with direct application links.

---

### Use Case UC-04: User Resumes from Saved Learning Path

**Actor:** Returning User (previously generated a learning path)

**Precondition:** The user has a saved learning path in the database from a previous session.

**Main Flow:**
1. The user logs into the platform.
2. The Dashboard component checks for an existing saved learning path via the GET /api/get-saved-learning-path endpoint.
3. The system finds a saved path for the user with target_role="Data Scientist" and selected_skills=["Python", "SQL", "Machine Learning"].
4. The Dashboard displays a welcome back message with a "Resume where you left off" button and a "Start New Generation" button.
5. The user clicks "Resume." The Dashboard jumps directly to Step 6 and renders the saved learning path with completed step indicators.
6. The user continues marking daily tasks as complete. The system updates the progress in the database.

**Alternate Flow (Progress Reset):**
At Step 5, the user clicks "Start New Generation" instead. The system clears the saved state and resets all wizard state variables. The user begins a fresh 6-step journey.

**Postcondition:** The user sees their previously generated learning path with updated progress indicators, or they start a new generation from scratch.

---

### Use Case UC-05: AI Chat Provides Contextual Help

**Actor:** User with AI Chat Sidebar

**Precondition:** The user is on any step of the wizard.

**Main Flow:**
1. The user types a question in the AI Chat sidebar: "What is Docker and why do I need it for a Full Stack Developer role?"
2. The frontend sends the question along with the current context (wizard step=3, role="Full Stack Developer", skills=["Python", "React"]) to the /api/role-chat endpoint.
3. The backend constructs a prompt for the Groq LLM that includes the user's question and the current context.
4. The LLM generates a helpful response explaining Docker in the context of Full Stack development.
5. The response is displayed in the chat sidebar.
6. The user asks a follow-up: "Should I learn Docker before or after React?" The same flow repeats with updated conversation history.

**Postcondition:** The user receives a contextually relevant answer to their technical question without leaving the wizard interface.

---

## 3.6 Summary

This chapter presented a comprehensive system analysis for the AI-Powered Skill Gap Generator and Personalized Learning Path Recommender. The feasibility study confirmed that the project is technically viable (mature, well-documented technologies), economically feasible (minimal to zero operational cost), and operationally practical (maintainable, scalable, user-friendly). Twelve functional requirements were documented, covering authentication, résumé parsing, GitHub analysis, gap analysis, learning path generation, job aggregation, persistence, and AI chat. Seven non-functional requirements addressed performance, security, scalability, reliability, usability, maintainability, and compatibility. Five detailed use cases illustrated the primary user interactions from the perspectives of a fresher, an experienced professional, and the system.

The next chapter presents the system design, including the architecture diagram, module descriptions, database schema, and API specifications.

---
