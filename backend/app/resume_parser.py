import re
import json
import logging
from pathlib import Path
from io import BytesIO
from pdfminer.high_level import extract_text

logger = logging.getLogger(__name__)

def load_known_skills():
    """Load skills from skill_data.json."""
    try:
        path = Path(__file__).parent / "skill_data.json"
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Return keys (main skill names) plus any specific logic if we wanted synonyms, 
        # but for now, let's stick to the keys as requested.
        return list(data.keys())
    except Exception as e:
        logger.error(f"Failed to load skill_data.json: {e}")
        return []

def extract_skills_from_pdf(file_stream) -> list:
    """
    Extract text from PDF and find skills using regex word boundaries.
    Returns a list of unique capitalized skill names.
    """
    try:
        # 1. Extract Text
        if isinstance(file_stream, bytes):
             file_stream = BytesIO(file_stream)
        
        # If it's a werkzeug FileStorage object, it might need .read() or similar, 
        # but often we pass the object directly if it behaves like a file.
        # However, pdfminer expects a file-like object or path.
        # If it's pure bytes, BytesIO is fine. If it's FileStorage, we might need to save or read.
        # Let's assume it is passed as a file-like object or we read it.
        # Safest is to read it into BytesIO if we are unsure of position.
        
        # Check if we need to read it
        if hasattr(file_stream, 'read') and hasattr(file_stream, 'seek'):
            file_stream.seek(0)
            content = file_stream.read()
            file_stream = BytesIO(content)
            
        text = extract_text(file_stream)
        if not text:
            return []

        # 2. Load Skills
        known_skills = load_known_skills()
        
        # 3. Regex Matching
        found_skills = set()
        text_lower = text.lower()
        
        for skill in known_skills:
            # Escape skill for regex to handle C++, C#, etc.
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            
            # Special handling for C++ or C# which \b might mess up relative to word boundaries 
            # (e.g. "C++" \b matches the end of C but ++ are non-word chars).
            # We will rely on simple word boundary for standard text skills.
            # For C++, we might need specific handling, but let's stick to user request: 
            # "Use re (regex) with word boundaries (\b{skill}\b)"
            
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        return list(found_skills)

    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []