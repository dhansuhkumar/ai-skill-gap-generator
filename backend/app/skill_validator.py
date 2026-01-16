# backend/app/skill_validator.py
"""
Skill Validator - Fast validation using curated skill database.
Loads valid skills from JSON for instant validation.
UPDATED: Less strict validation to accept CSV variations.
"""

import json
import os
from typing import Set, Dict, List

# Global cache for valid skills
_VALID_SKILLS_CACHE: Set[str] = None
_SKILL_CATEGORIES_CACHE: Dict[str, List[str]] = None


def load_valid_skills() -> Set[str]:
    """
    Load valid skills from JSON file.
    Returns a set of lowercase skill names for fast lookup.
    """
    global _VALID_SKILLS_CACHE
    
    if _VALID_SKILLS_CACHE is not None:
        return _VALID_SKILLS_CACHE
    
    try:
        # Load from JSON file
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'valid_skills.json'
        )
        
        with open(data_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        
        # Flatten all skills into a single set
        valid_skills = set()
        for category_skills in categories.values():
            for skill in category_skills:
                # Add original and lowercase versions
                valid_skills.add(skill.lower())
                # Add common variations
                valid_skills.add(skill.lower().replace('.', ''))
                valid_skills.add(skill.lower().replace(' ', ''))
        
        # Add common abbreviations
        abbreviations = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'cpp': 'c++',
            'cs': 'c#',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'k8s': 'kubernetes',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'cv': 'computer vision',
        }
        
        for abbr in abbreviations:
            valid_skills.add(abbr)
        
        _VALID_SKILLS_CACHE = valid_skills
        print(f"✅ Loaded {len(valid_skills)} valid skills for validation")
        
        return valid_skills
        
    except Exception as e:
        print(f"⚠️ Failed to load valid_skills.json: {e}")
        # Return empty set as fallback
        return set()


def is_valid_skill_fast(skill: str) -> bool:
    """
    Fast skill validation - LESS STRICT VERSION.
    Accepts partial matches and variations to work with CSV data.
    
    Args:
        skill: Skill name to validate
    
    Returns:
        True if skill is valid, False otherwise
    """
    if not skill or not skill.strip():
        return False
    
    skill_lower = skill.lower().strip()
    
    # Skip obvious garbage
    if len(skill_lower) < 2 or len(skill_lower) > 50:
        return False
    
    if not any(c.isalpha() for c in skill_lower):
        return False
    
    valid_skills = load_valid_skills()
    
    # If no valid skills loaded, accept anything reasonable
    if not valid_skills:
        return True
    
    # Direct match
    if skill_lower in valid_skills:
        return True
    
    # Remove common suffixes and try again
    skill_clean = skill_lower.replace('.js', '').replace('.py', '').replace(' ', '')
    if skill_clean in valid_skills:
        return True
    
    # Partial match for compound skills (e.g., "python programming" contains "python")
    for valid_skill in valid_skills:
        # Check if valid skill is in the input
        if valid_skill in skill_lower:
            if len(valid_skill) >= 2:  # Avoid single letter matches
                return True
        # Check if input is in valid skill
        if skill_lower in valid_skill:
            if len(skill_lower) >= 2:
                return True
    
    # FALLBACK: If it looks like a skill, accept it (LESS STRICT)
    # This allows CSV skills that aren't in our curated list
    if 2 <= len(skill_lower) <= 50 and any(c.isalpha() for c in skill_lower):
        # Check if it's not pure garbage
        alpha_ratio = sum(c.isalpha() for c in skill_lower) / len(skill_lower)
        if alpha_ratio > 0.3:  # At least 30% letters
            return True
    
    return False


def load_skill_categories() -> Dict[str, List[str]]:
    """
    Load skill categories from JSON file.
    Returns dict of {category: [skills]}.
    """
    global _SKILL_CATEGORIES_CACHE
    
    if _SKILL_CATEGORIES_CACHE is not None:
        return _SKILL_CATEGORIES_CACHE
    
    try:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'valid_skills.json'
        )
        
        with open(data_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        
        _SKILL_CATEGORIES_CACHE = categories
        return categories
        
    except Exception as e:
        print(f"⚠️ Failed to load skill categories: {e}")
        return {}


def get_skill_category(skill: str) -> str:
    """
    Get the category for a skill.
    
    Args:
        skill: Skill name
    
    Returns:
        Category name or 'other'
    """
    categories = load_skill_categories()
    skill_lower = skill.lower().strip()
    
    for category, skills in categories.items():
        for valid_skill in skills:
            if skill_lower == valid_skill.lower() or skill_lower in valid_skill.lower():
                return category
    
    return 'other'


# Pre-load skills at module import for faster first access
load_valid_skills()
