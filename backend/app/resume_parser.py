import logging
import os
import json
import re
from io import BytesIO
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)

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


def extract_skills_from_pdf(file_stream) -> list:
    """
    Extract text from PDF and identify skills using keyword matching.
    Returns a list of skill strings (no AI used).
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
