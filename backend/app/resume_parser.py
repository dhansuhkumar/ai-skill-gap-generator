"""
Resume Parser with Deep AI-Powered Extraction.

Extracts comprehensive resume data using Groq AI:
- Skills (tech + soft)
- Education (degree, institution, year, GPA)
- Work experience (company, title, duration, seniority)
- Certifications
- Languages
- Total experience years
- Global context (fresher/experienced)
- GitHub/LinkedIn URLs
"""

import logging
import os
import json
import re
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, List
from pdfminer.high_level import extract_text

from .web_skill_extractor import get_tech_skills_vocab

logger = logging.getLogger(__name__)

TECH_SKILLS_VOCAB = get_tech_skills_vocab()

SENIOR_KEYWORDS = [
    "senior",
    "lead",
    "principal",
    "architect",
    "staff",
    "manager",
    "director",
    "head of",
    "team lead",
    "tech lead",
    "5+ years",
    "6+ years",
    "7+ years",
    "8+ years",
    "10+ years",
]

FRESHER_KEYWORDS = [
    "student",
    "fresher",
    "graduate",
    "intern",
    "internship",
    "bootcamp",
    "junior",
    "entry level",
    "entry-level",
    "trainee",
    "apprentice",
    "new grad",
    "recent graduate",
    "b.tech",
    "b.e.",
    "bachelor",
    "pursuing",
    "studying",
    "0-1 years",
    "0-2 years",
]

PROJECT_KEYWORDS = [
    "project",
    "built",
    "developed",
    "created",
    "implemented",
    "designed",
    "deployed",
    "github",
    "repository",
    "portfolio",
]

DEGREE_PATTERNS = [
    r"(?:b\.?tech|bachelor(?:'s)?|b\.?e\.?|b\.?sc|b\.?a\.?|b\.?com|m\.?tech|master(?:'s)?|m\.?sc|m\.?ba|ph\.?d\.?|doctorate)(?:\s+(?:of|in|Engineering|Science|Arts|Commerce|Business|Computer Applications|Computer Science|Information Technology))?",
    r"(?:computer science|data science|information technology|electronics|electrical|mechanical|civil|chemical|biotechnology|business administration)(?:\s+(?:engineering|technology|science))?",
]

COMPANY_PATTERNS = [
    r"(?:google|amazon|microsoft|meta|facebook|apple|netflix|adobe|uber|airbnb|salesforce|oracle|ibm|intel|cisco|redhat|vmware|serviceNow|servicenow)",
    r"(?:infosys|wipro|tcs|hcl|tech mahindra|accenture|cognizant|capgemini|deloitte|ey|kpmg|pwc|flipkart|paytm|oyo|swiggy|zomato|myntra)",
]

DATE_PATTERNS = [
    r"(\d{4})\s*[-–—to]+\s*(present|\d{4})",
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4})\s*[-–—to]+\s*(?:(present)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4}))",
    r"(\d{4})\s+to\s+(present|\d{4})",
]


def _extract_skills_keyword(text: str) -> List[str]:
    """Extract skills using vocabulary matching."""
    text_lower = text.lower()
    found = set()

    for primary_skill, variations in TECH_SKILLS_VOCAB.items():
        for variant in variations:
            if variant in text_lower:
                found.add(primary_skill)
                break

    return list(found)


def _detect_context(text: str) -> str:
    """Detect overall resume context."""
    text_lower = text.lower()
    has_senior = any(kw in text_lower for kw in SENIOR_KEYWORDS)
    has_fresher = any(kw in text_lower for kw in FRESHER_KEYWORDS)

    if has_senior and not has_fresher:
        return "experienced"
    elif has_fresher and not has_senior:
        return "fresher"
    return "neutral"


def _extract_years_of_experience(text: str) -> Optional[float]:
    """Extract estimated years of experience from date ranges."""
    current_year = datetime.now().year
    max_years = 0

    for pattern in DATE_PATTERNS:
        matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            try:
                start_year = None
                end_year = current_year

                for g in groups:
                    if g is None:
                        continue
                    if g.lower() == "present":
                        end_year = current_year
                    elif g.isdigit() and len(g) == 4:
                        year = int(g)
                        if 1990 <= year <= current_year + 1:
                            if start_year is None:
                                start_year = year
                            else:
                                end_year = year

                if start_year:
                    years = end_year - start_year
                    if 0 <= years <= 50:
                        max_years = max(max_years, years)
            except (ValueError, TypeError):
                continue

    return max_years if max_years > 0 else None


def _has_project_mentions(text: str) -> bool:
    """Check if resume mentions projects."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PROJECT_KEYWORDS)


def _extract_urls(text: str) -> Dict[str, str]:
    """Extract GitHub and LinkedIn URLs."""
    urls = {"github_url": "", "linkedin_url": ""}

    github_pattern = r"(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]*|github\.com/[a-zA-Z0-9_-]+)"
    linkedin_pattern = r"(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)"

    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        urls["github_url"] = github_match.group(0)
        if not urls["github_url"].startswith("http"):
            urls["github_url"] = "https://" + urls["github_url"]

    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        urls["linkedin_url"] = linkedin_match.group(0)
        if not urls["linkedin_url"].startswith("http"):
            urls["linkedin_url"] = "https://" + urls["linkedin_url"]

    return urls


def _extract_deep_with_ai(text: str) -> Dict:
    """
    Use Groq AI to extract comprehensive resume data.
    Returns structured JSON with all resume fields.
    """
    prompt = f"""You are an expert resume parser. Extract structured information from this resume text.

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
    "skills": ["Python", "React", "AWS", ...],
    "education": [
        {{
            "degree": "B.Tech Computer Science",
            "institution": "MIT",
            "graduation_year": 2024,
            "gpa": "8.5/10"
        }}
    ],
    "experience": [
        {{
            "company": "Google",
            "title": "Software Engineer",
            "start_year": 2022,
            "end_year": 2024,
            "is_current": false
        }}
    ],
    "certifications": ["AWS Solutions Architect", "Google Data Analytics"],
    "total_experience_years": 2.5,
    "languages": ["English", "Hindi"],
    "has_projects": true,
    "github_url": "https://github.com/username",
    "linkedin_url": "https://linkedin.com/in/username"
}}

Resume Text:
{text[:4000]}

Return ONLY the JSON object:"""

    try:
        from .ai.router import get_ai_response

        response = get_ai_response(prompt, requested_provider="groq")

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            logger.info(
                f"Groq extracted: {len(data.get('skills', []))} skills, {len(data.get('experience', []))} exp entries"
            )
            return data
    except Exception as e:
        logger.error(f"Groq extraction failed: {e}")

    return {}


def extract_skills_from_pdf(file_stream) -> list:
    """Extract skills from PDF using keyword matching (legacy function)."""
    try:
        if isinstance(file_stream, bytes):
            file_stream = BytesIO(file_stream)

        if hasattr(file_stream, "read") and hasattr(file_stream, "seek"):
            file_stream.seek(0)
            content = file_stream.read()
            file_stream = BytesIO(content)

        text = extract_text(file_stream)
        if not text:
            return []

        skills = _extract_skills_keyword(text)
        if not skills:
            common_skills = [
                "python",
                "java",
                "javascript",
                "react",
                "node",
                "sql",
                "aws",
                "docker",
                "git",
            ]
            text_lower = text.lower()
            skills = [s.title() for s in common_skills if s in text_lower]

        return skills
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []


def extract_skills_with_context(file_stream) -> dict:
    """Extract skills from PDF with contextual information (legacy function)."""
    try:
        if isinstance(file_stream, bytes):
            file_stream = BytesIO(file_stream)

        if hasattr(file_stream, "read") and hasattr(file_stream, "seek"):
            file_stream.seek(0)
            content = file_stream.read()
            file_stream = BytesIO(content)

        text = extract_text(file_stream)
        if not text:
            return {
                "skills": [],
                "global_context": "neutral",
                "estimated_years": None,
                "has_projects": False,
                "raw_skills": [],
            }

        raw_skills = _extract_skills_keyword(text)
        if not raw_skills:
            text_lower = text.lower()
            common_skills = [
                "python",
                "java",
                "javascript",
                "react",
                "node",
                "sql",
                "aws",
                "docker",
                "git",
            ]
            raw_skills = [s.title() for s in common_skills if s in text_lower]

        global_context = _detect_context(text)
        estimated_years = _extract_years_of_experience(text)
        has_projects = _has_project_mentions(text)

        skills_with_context = [
            {"skill": skill, "context": global_context, "has_projects": has_projects}
            for skill in raw_skills
        ]

        return {
            "skills": skills_with_context,
            "global_context": global_context,
            "estimated_years": estimated_years,
            "has_projects": has_projects,
            "raw_skills": raw_skills,
        }
    except Exception as e:
        logger.error(f"Error extracting skills with context: {e}")
        return {
            "skills": [],
            "global_context": "neutral",
            "estimated_years": None,
            "has_projects": False,
            "raw_skills": [],
        }


def extract_resume_deep(file_stream) -> dict:
    """
    Deep resume extraction using Groq AI.

    Returns comprehensive resume data including:
    - skills: List of tech skills
    - education: Education history
    - experience: Work experience
    - certifications: Certifications
    - total_experience_years: Years of experience
    - global_context: fresher/experienced/neutral
    - estimated_years: Estimated years from dates
    - has_projects: Whether projects mentioned
    - languages: Languages spoken
    - github_url: GitHub profile URL
    - linkedin_url: LinkedIn profile URL
    - filled_boxes: Count of filled data categories
    """
    try:
        if isinstance(file_stream, bytes):
            file_stream = BytesIO(file_stream)

        if hasattr(file_stream, "read") and hasattr(file_stream, "seek"):
            file_stream.seek(0)
            content = file_stream.read()
            file_stream = BytesIO(content)

        text = extract_text(file_stream)
        if not text:
            return _empty_deep_result()

        logger.info("Starting Groq AI resume extraction...")
        ai_result = _extract_deep_with_ai(text)

        skills = ai_result.get("skills", []) or _extract_skills_keyword(text)
        if not skills:
            skills = [
                s.title()
                for s in [
                    "python",
                    "java",
                    "javascript",
                    "react",
                    "sql",
                    "aws",
                    "docker",
                    "git",
                ]
                if s in text.lower()
            ]

        education = ai_result.get("education", [])
        experience = ai_result.get("experience", [])
        certifications = ai_result.get("certifications", [])
        languages = ai_result.get("languages", [])

        global_context = _detect_context(text)
        estimated_years = ai_result.get(
            "total_experience_years"
        ) or _extract_years_of_experience(text)
        has_projects = ai_result.get("has_projects") or _has_project_mentions(text)

        urls = _extract_urls(text)
        github_url = ai_result.get("github_url") or urls.get("github_url", "")
        linkedin_url = ai_result.get("linkedin_url") or urls.get("linkedin_url", "")

        filled_boxes = sum(
            [
                len(skills) > 0,
                len(education) > 0,
                len(experience) > 0,
                len(certifications) > 0,
                len(languages) > 0,
                bool(github_url),
                bool(linkedin_url),
            ]
        )

        result = {
            "skills": skills,
            "education": education,
            "experience": experience,
            "certifications": certifications,
            "languages": languages,
            "total_experience_years": estimated_years,
            "global_context": global_context,
            "estimated_years": estimated_years,
            "has_projects": has_projects,
            "github_url": github_url,
            "linkedin_url": linkedin_url,
            "filled_boxes": filled_boxes,
            "total_boxes": 7,
            "filled_percentage": round((filled_boxes / 7) * 100),
        }

        logger.info(f"Deep extraction complete: {filled_boxes}/7 boxes filled")
        return result

    except Exception as e:
        logger.error(f"Deep resume extraction failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return _empty_deep_result()


def _empty_deep_result() -> dict:
    """Return empty deep extraction result."""
    return {
        "skills": [],
        "education": [],
        "experience": [],
        "certifications": [],
        "languages": [],
        "total_experience_years": None,
        "global_context": "neutral",
        "estimated_years": None,
        "has_projects": False,
        "github_url": "",
        "linkedin_url": "",
        "filled_boxes": 0,
        "total_boxes": 7,
        "filled_percentage": 0,
    }
