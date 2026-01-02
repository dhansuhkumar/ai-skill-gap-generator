import logging
from io import BytesIO
from pdfminer.high_level import extract_text
from app.ai_generator import extract_skills_with_ai

logger = logging.getLogger(__name__)

def extract_skills_from_pdf(file_stream) -> list:
    """
    Extract text from PDF and use AI to identify skills.
    Returns a list of skill strings.
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

        # 2. Use AI Extraction
        # Limit text length to avoid huge context usage
        truncated_text = text[:8000] 
        skills = extract_skills_with_ai(truncated_text)
        
        return skills

    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return []