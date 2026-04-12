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
