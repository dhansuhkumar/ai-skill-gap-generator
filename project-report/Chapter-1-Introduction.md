# CHAPTER 1

# INTRODUCTION

---

## 1.1 Background and Motivation

The technology industry is evolving at an unprecedented pace. New frameworks, programming languages, tools, and methodologies emerge almost every month. For someone looking to switch careers or level up within the tech industry, the sheer volume of skills to acquire can feel overwhelming. A fresher graduating with a Computer Science degree might know Python and some basic web development, but they often do not know exactly what specific technologies a "Full Stack Developer" or "Data Scientist" role actually requires. Even experienced professionals sometimes struggle to keep up with shifting industry demands.

Traditional learning platforms such as Coursera, Udemy, and LinkedIn Learning offer thousands of courses. However, these platforms suffer from a critical limitation: they take a one-size-fits-all approach. A learner must manually search for relevant courses, guess which technologies are in demand, and figure out the correct sequence in which to learn them. Most learners spend weeks researching before they even start learning, and many give up halfway because they do not have a clear roadmap or visible progress.

The problem becomes even more complex when we consider the Indian job market specifically. With over 50 lakh engineering graduates entering the workforce every year, the competition for entry-level tech jobs is fierce. Freshers often apply to hundreds of jobs without understanding how their existing skills match against what employers actually want. They lack a tool that can objectively compare their current abilities against job requirements and tell them precisely what they need to learn.

Beyond freshers, working professionals also face challenges. Someone working as a backend developer who wants to transition to an ML Engineer role needs to identify the exact skill gaps between their current position and the target role. They need a personalised learning plan that respects their time constraints, work schedule, and learning pace. Generic roadmaps found on blog posts do not account for the individual's existing knowledge, daily time availability, or career goals.

Another significant gap in existing solutions is the absence of real-world context. Most learning platforms generate roadmaps in isolation, without curating actual job listings or portfolio project ideas that would help the learner demonstrate their new skills to potential employers. A learning path that does not connect back to actual job market opportunities feels incomplete and demotivating.

The AI-Powered Skill Gap Generator and Personalized Learning Path Recommender was conceived to address all these issues. The platform takes a holistic view of a user's career development journey. It starts by understanding what the user already knows, identifies exactly what they need to learn for their target role, and generates a day-by-day learning roadmap with curated resources, YouTube tutorials, and portfolio project ideas. Most importantly, it surfaces real job listings that match the user's updated skill profile, creating a complete闭环 from learning to job application.

---

## 1.2 Problem Statement

The following specific problems form the core motivation for this project:

1. **Lack of Objective Skill Gap Analysis:** Most learners do not have a systematic way to compare their current skills against the requirements of their target job role. They rely on guesswork or vague advice from mentors, which often leads to learning irrelevant or outdated technologies.

2. **No Personalised Learning Roadmaps:** Existing platforms provide generic course recommendations without considering the user's existing knowledge, preferred learning pace, daily time commitment, or total duration of the learning plan.

3. **Disconnect Between Learning and Employment:** Learning platforms focus solely on content delivery. They do not help learners understand whether their learning efforts will translate into actual job opportunities or how to showcase their new skills through portfolio projects.

4. **Résumé Blind Spots:** Many freshers and early-career professionals do not know how to effectively present their skills, education, and projects on a résumé. Even when they upload a résumé to existing tools, the extraction is often incomplete or inaccurate.

5. **GitHub Profile Underutilisation:** GitHub repositories are a goldmine of evidence for a developer's coding ability, but most recruiters and learners themselves do not know how to objectively evaluate a GitHub profile. A fresher with five small projects should not be scored the same way as a professional with ten production-grade repositories.

6. **Limited Job Discovery for Freshers:** Popular job aggregation platforms do not filter jobs by experience level effectively. A fresher searching for "Software Developer" jobs in India will see hundreds of senior-level postings, making the search frustrating and demotivating.

This project directly addresses all six problem areas through a unified web platform that combines AI-powered résumé parsing, GitHub profile analysis, skill gap computation, personalised learning path generation, and real job aggregation.

---

## 1.3 Objectives

The project was designed with the following five primary objectives:

**Objective 1:** To develop a hybrid résumé parsing system that uses both AI (Groq LLM) and keyword-based extraction to identify a user's skills, education, experience, certifications, and contact information from a PDF résumé, with automatic fallback mechanisms to ensure reliability even when AI services are unavailable.

**Objective 2:** To implement a GitHub profile analyser that evaluates a user's public repositories for quality indicators such as test coverage, CI/CD implementation, type-safety files, and language diversity, generating a fresher-friendly score that rewards coding activity rather than penalising lack of experience.

**Objective 3:** To build a skill gap analysis engine that compares a user's current skills against the required skills for a self-selected target job role, using web-search-augmented AI to ensure up-to-date and accurate skill requirements, and presenting the results with a clear match score and visual gap breakdown.

**Objective 4:** To create an AI-powered learning path generator that produces a day-by-day personalised roadmap for each selected missing skill, including curated resources from authoritative sources, YouTube tutorial embeds, and portfolio project recommendations, all constrained by the user's time commitment, learning pace, and total duration preferences.

**Objective 5:** To integrate a multi-source job aggregation system that fetches real job listings from Remotive, Jooble, and Adzuna APIs in parallel, filters them by experience level, scores them by skill match, and ranks them by location proximity to the user's city, delivering actionable job application links alongside the learning path.

---

## 1.4 Scope of the Project

The project encompasses a full-stack web application with the following scope:

**Frontend Scope:**
The React.js frontend implements a six-step interactive wizard that guides users from skill input through to viewing their complete learning path and job matches. The interface uses a glassmorphism dark theme with Framer Motion animations for smooth transitions between wizard steps. A persistent AI chat sidebar provides contextual help at every stage. The dashboard displays skill comparison charts, a learning timeline with step-by-step progress tracking, and gamification elements to maintain learner motivation.

**Backend Scope:**
The Python Flask backend exposes a REST API that handles résumé upload and parsing, GitHub profile analysis, role-based gap analysis, learning path generation, and job search aggregation. The backend uses Supabase for persistent storage of user profiles, learning paths, and progress tracking. JWT-based authentication ensures that user data remains private and secure. All external API calls (Groq, GitHub, Remotive, Jooble, Adzuna, DuckDuckGo) are managed through dedicated service modules with proper error handling, retry logic, and caching.

**Integration Scope:**
The system integrates with five external services: Groq API for AI inference, GitHub REST API for repository analysis, Remotive API for remote job listings, Jooble API for location-based jobs, and Adzuna API for the Indian job market. DuckDuckGo is used for web search augmentation to ensure learning resources are current and relevant.

**Deployment Scope:**
The frontend is deployed on Vercel and the backend on Render, both connected to the same GitHub repository. Docker and Docker Compose configuration files are provided for containerised local development and potential production deployment.

**Out of Scope:**
The project does not include a native mobile application, LinkedIn API integration, real-time collaboration features, payment processing, or job application tracking. These features are identified as future enhancements in Chapter 8.

---

## 1.5 Organisation of the Report

The report is structured into eight chapters, each building upon the previous one to provide a complete understanding of the project:

**Chapter 1: Introduction** establishes the motivation, defines the problem, lists the objectives, and describes the scope. This chapter sets the context for the entire project.

**Chapter 2: Literature Review** examines related work in the areas of skill gap analysis, personalised learning systems, NLP-based résumé parsing, job-skill matching algorithms, and adaptive learning platforms. It identifies gaps in existing research that this project addresses.

**Chapter 3: System Analysis** covers the feasibility study from technical, economic, and operational perspectives. It documents the functional and non-functional requirements and provides detailed use case descriptions for the three primary actors: Fresher, Experienced Professional, and the System.

**Chapter 4: System Design** presents the system architecture, module descriptions for all backend components, database design with an Entity-Relationship diagram, API endpoint specifications with request and response formats, and the frontend component hierarchy.

**Chapter 5: Implementation** details the development environment, key algorithms including the hybrid résumé extraction, GitHub fresher-friendly scoring, fast learning path generation with RAG, and location-aware job matching. It also documents the challenges faced during development and the solutions implemented.

**Chapter 6: Testing** describes the testing strategy including unit tests for critical backend modules, integration tests for end-to-end flows, performance benchmarks for learning path generation latency, and user acceptance test cases with expected and actual results.

**Chapter 7: Results and Discussion** presents screenshots and descriptions of the running application, performance measurement results, limitations encountered, and a comparative analysis against existing commercial platforms.

**Chapter 8: Conclusion and Future Work** summarises the achievements, evaluates how the project meets its stated objectives, and proposes future enhancements including mobile app development, LinkedIn integration, fine-tuned domain-specific LLMs, and peer learning community features.

The report also includes appendices containing the database schema SQL, environment variable reference, API documentation, and installation instructions.

---

## 1.6 Summary

This chapter introduced the AI-Powered Skill Gap Generator and Personalized Learning Path Recommender by establishing its relevance in today's rapidly changing technology job market. The problem statement identified six critical gaps in the learning-to-employment journey that existing platforms fail to address. The five objectives provide a clear blueprint for what the system must accomplish, ranging from intelligent résumé parsing to multi-source job aggregation. The scope defines the boundaries of what was built, and the report organisation gives the reader a roadmap for the remaining chapters.

The next chapter reviews the existing literature and research in skill gap analysis, personalised learning, NLP-based résumé parsing, and job-skill matching to establish the theoretical and practical foundation upon which this project was built.

---
