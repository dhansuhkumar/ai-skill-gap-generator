# backend/app/skill_cleaner.py
"""
Skill Data Cleaner - Remove duplicates, garbage, and normalize skill names.
UPDATED: Minimal validation to accept CSV skills.
"""

import re
from typing import List, Set

# Common garbage patterns to filter out
GARBAGE_PATTERNS = [
    r'^\d+$',  # Pure numbers
    r'^[^a-zA-Z]+$',  # No letters at all
    r'.{50,}',  # Too long (> 50 chars)
    r'^.$',  # Single character
    r'^\s*$',  # Empty or whitespace only
]


def is_garbage_skill(skill: str) -> bool:
    """Check if a skill name is garbage/invalid."""
    if not skill or not skill.strip():
        return True
    
    skill = skill.strip()
    
    # Check against garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if re.match(pattern, skill, re.IGNORECASE):
            return True
    
    return False


def is_valid_skill(skill: str) -> bool:
    """
    Check if a skill is valid - MINIMAL VALIDATION.
    Accept almost everything from CSV.
    """
    if is_garbage_skill(skill):
        return False
    
    # ACCEPT EVERYTHING ELSE - no strict validation
    # Just check it has some letters and reasonable length
    if 2 <= len(skill) <= 50 and any(c.isalpha() for c in skill):
        return True
    
    return False


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for deduplication."""
    if not skill:
        return ""
    
    # Convert to lowercase
    skill = skill.lower().strip()
    
    # Remove extra whitespace
    skill = re.sub(r'\s+', ' ', skill)
    
    # Remove common variations
    skill = skill.replace('.js', '')
    skill = skill.replace('.py', '')
    
    # Normalize common abbreviations
    replacements = {
        'javascript': 'javascript',
        'js': 'javascript',
        'typescript': 'typescript',
        'ts': 'typescript',
        'python': 'python',
        'py': 'python',
        'c++': 'c++',
        'cpp': 'c++',
        'c#': 'c#',
        'csharp': 'c#',
        'postgresql': 'postgresql',
        'postgres': 'postgresql',
        'mongodb': 'mongodb',
        'mongo': 'mongodb',
    }
    
    return replacements.get(skill, skill)


def clean_and_deduplicate_skills(skills: List[str], max_skills: int = None) -> List[str]:
    """
    Clean skill list: remove garbage, deduplicate, normalize.
    
    Args:
        skills: Raw list of skills
        max_skills: Maximum number of skills to return (None = all)
    
    Returns:
        Cleaned and deduplicated list of skills
    """
    if not skills:
        return []
    
    seen_normalized = set()
    cleaned_skills = []
    
    for skill in skills:
        if not skill:
            continue
        
        skill = skill.strip()
        
        # Skip garbage
        if is_garbage_skill(skill):
            continue
        
        # Validate skill (minimal validation now)
        if not is_valid_skill(skill):
            continue
        
        # Normalize for deduplication
        normalized = normalize_skill_name(skill)
        
        # Skip if already seen
        if normalized in seen_normalized:
            continue
        
        seen_normalized.add(normalized)
        cleaned_skills.append(skill)  # Keep original casing
        
        # Stop if we've reached max
        if max_skills and len(cleaned_skills) >= max_skills:
            break
    
    return cleaned_skills


def rank_skills_by_frequency(skill_counts: dict, top_n: int = 10) -> List[str]:
    """
    Rank skills by frequency and return top N.
    
    Args:
        skill_counts: Dict of {skill: count}
        top_n: Number of top skills to return
    
    Returns:
        List of top N skills sorted by frequency
    """
    # Sort by count descending
    sorted_skills = sorted(
        skill_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Get top N
    top_skills = [skill for skill, count in sorted_skills[:top_n]]
    
    # Clean and deduplicate
    return clean_and_deduplicate_skills(top_skills, max_skills=top_n)
