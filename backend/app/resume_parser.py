"""
Resume Parser with Context Analysis

Extracts skills from PDF resumes with contextual information:
- Seniority detection (Senior, Lead, Architect -> "experienced")
- Fresher detection (Student, Intern, Bootcamp, Graduate -> "fresher")
- Date range extraction for duration estimation
- Project mention detection

This enables the Fusion Engine to weight skills appropriately.
"""

import logging
import os
import json
import re
from io import BytesIO
from datetime import datetime
from typing import Optional
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)

# Seniority keywords (indicates experienced professional)
SENIOR_KEYWORDS = [
    "senior", "lead", "principal", "architect", "staff", 
    "manager", "director", "head of", "team lead", "tech lead",
    "5+ years", "6+ years", "7+ years", "8+ years", "10+ years"
]

# Fresher keywords (indicates entry-level/student)
FRESHER_KEYWORDS = [
    "student", "fresher", "graduate", "intern", "internship",
    "bootcamp", "junior", "entry level", "entry-level", "trainee",
    "apprentice", "new grad", "recent graduate", "b.tech", "b.e.",
    "bachelor", "pursuing", "studying", "0-1 years", "0-2 years"
]

# Date patterns for duration extraction
DATE_PATTERNS = [
    # "2021 - Present", "2021 - 2023"
    r'(\d{4})\s*[-–—to]+\s*(present|\d{4})',
    # "Jan 2021 - Dec 2023", "January 2021 - Present"
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4})\s*[-–—to]+\s*(?:(present)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4}))',
    # "2021 to present"
    r'(\d{4})\s+to\s+(present|\d{4})',
]

# Project indicators
PROJECT_KEYWORDS = [
    "project", "built", "developed", "created", "implemented",
    "designed", "deployed", "github", "repository", "portfolio"
]


# Load skill keywords for deterministic extraction
def _load_skill_keywords():
    """Load skill database and build a mapping."""
    mapping = {}
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'skill_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            for skill, info in data.items():
                mapping[skill.lower()] = skill
                for syn in info.get("synonyms", []):
                    mapping[syn.lower()] = skill
    except Exception as e:
        logger.error(f"Failed to load skill_data.json: {e}")
    return mapping


SKILL_MAPPING = _load_skill_keywords()


def _extract_skills_deterministic(text: str) -> list:
    """Extract skills using keyword matching from skill_data.json."""
    if not SKILL_MAPPING or not text:
        return []
    
    text_lower = text.lower()
    found = set()
    # Sort by length desc to match longest first
    sorted_keys = sorted(SKILL_MAPPING.keys(), key=len, reverse=True)
    
    for token in sorted_keys:
        escaped = re.escape(token)
        if re.search(r'(?:^|[^a-z0-9])' + escaped + r'(?:$|[^a-z0-9])', text_lower):
            found.add(SKILL_MAPPING[token])
    
    return list(found)


def _detect_context(text: str) -> str:
    """
    Detect overall resume context: 'experienced', 'fresher', or 'neutral'.
    
    Returns:
        'experienced' - if senior/lead keywords found
        'fresher' - if student/intern/bootcamp keywords found
        'neutral' - if neither or both found
    """
    text_lower = text.lower()
    
    has_senior = any(kw in text_lower for kw in SENIOR_KEYWORDS)
    has_fresher = any(kw in text_lower for kw in FRESHER_KEYWORDS)
    
    if has_senior and not has_fresher:
        return "experienced"
    elif has_fresher and not has_senior:
        return "fresher"
    else:
        return "neutral"


def _extract_years_of_experience(text: str) -> Optional[int]:
    """
    Extract estimated years of experience from date ranges.
    
    Returns the maximum duration found, or None if no dates detected.
    """
    text_lower = text.lower()
    current_year = datetime.now().year
    max_years = 0
    
    for pattern in DATE_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            
            try:
                # Extract start year (always first numeric group)
                start_year = None
                end_year = current_year  # Default to present
                
                for g in groups:
                    if g is None:
                        continue
                    if g.lower() == 'present':
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
                    if 0 <= years <= 50:  # Sanity check
                        max_years = max(max_years, years)
            except (ValueError, TypeError):
                continue
    
    return max_years if max_years > 0 else None


def _has_project_mentions(text: str) -> bool:
    """Check if resume mentions projects (indicates hands-on experience)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PROJECT_KEYWORDS)


def _get_skill_context_window(text: str, skill: str, window_size: int = 200) -> str:
    """
    Get the text surrounding a skill mention for context analysis.
    
    Args:
        text: Full resume text
        skill: Skill to find context for
        window_size: Characters to include before/after skill mention
        
    Returns:
        Substring containing the skill and surrounding context
    """
    text_lower = text.lower()
    skill_lower = skill.lower()
    
    idx = text_lower.find(skill_lower)
    if idx == -1:
        return ""
    
    start = max(0, idx - window_size)
    end = min(len(text), idx + len(skill) + window_size)
    
    return text[start:end]


def extract_skills_from_pdf(file_stream) -> list:
    """
    Extract text from PDF and identify skills using keyword matching.
    Returns a list of skill strings (no AI used).
    
    This is the legacy function for backward compatibility.
    """
    try:
        # 1. Extract Text
        if isinstance(file_stream, bytes):
            file_stream = BytesIO(file_stream)
        
        if hasattr(file_stream, 'read') and hasattr(file_stream, 'seek'):
            file_stream.seek(0)
            content = file_stream.read()
            file_stream = BytesIO(content)
            
        text = extract_text(file_stream)
        if not text:
            return []

        # 2. Deterministic Skill Extraction (no AI)
        skills = _extract_skills_deterministic(text)
        
        if skills:
            logger.info(f"Deterministic parser found {len(skills)} skills")
        else:
            # Fallback: check for common skills manually
            fallback_skills = []
            text_lower = text.lower()
            common_skills = ["python", "java", "javascript", "react", "node", "sql", "aws", "docker", "git"]
            for skill in common_skills:
                if skill in text_lower:
                    fallback_skills.append(skill.title())
            skills = fallback_skills
        
        return skills

    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []


def extract_skills_with_context(file_stream) -> dict:
    """
    Extract skills from PDF with contextual information.
    
    Returns:
        {
            "skills": [
                {
                    "skill": "Python",
                    "context": "experienced" | "fresher" | "neutral",
                    "has_projects": True | False
                },
                ...
            ],
            "global_context": "experienced" | "fresher" | "neutral",
            "estimated_years": 3 | None,
            "has_projects": True | False,
            "raw_skills": ["Python", "React", ...]  # For backward compatibility
        }
    """
    try:
        # 1. Extract Text
        if isinstance(file_stream, bytes):
            file_stream = BytesIO(file_stream)
        
        if hasattr(file_stream, 'read') and hasattr(file_stream, 'seek'):
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
                "raw_skills": []
            }

        # 2. Extract skills
        raw_skills = _extract_skills_deterministic(text)
        
        if not raw_skills:
            # Fallback
            text_lower = text.lower()
            common_skills = ["python", "java", "javascript", "react", "node", "sql", "aws", "docker", "git"]
            raw_skills = [s.title() for s in common_skills if s in text_lower]

        # 3. Analyze global context
        global_context = _detect_context(text)
        estimated_years = _extract_years_of_experience(text)
        has_projects = _has_project_mentions(text)

        # 4. Analyze per-skill context (using context window)
        skills_with_context = []
        for skill in raw_skills:
            context_window = _get_skill_context_window(text, skill)
            skill_context = _detect_context(context_window) if context_window else global_context
            
            # Check if skill is mentioned near project descriptions
            skill_has_projects = any(
                kw in context_window.lower() 
                for kw in PROJECT_KEYWORDS
            ) if context_window else has_projects
            
            skills_with_context.append({
                "skill": skill,
                "context": skill_context,
                "has_projects": skill_has_projects
            })

        logger.info(f"Extracted {len(skills_with_context)} skills with context: {global_context}")
        
        return {
            "skills": skills_with_context,
            "global_context": global_context,
            "estimated_years": estimated_years,
            "has_projects": has_projects,
            "raw_skills": raw_skills
        }

    except Exception as e:
        logger.error(f"Error extracting skills with context: {e}")
        return {
            "skills": [],
            "global_context": "neutral",
            "estimated_years": None,
            "has_projects": False,
            "raw_skills": []
        }


