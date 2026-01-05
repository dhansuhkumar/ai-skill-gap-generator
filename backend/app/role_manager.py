import json
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class RoleManager:
    def __init__(self):
        self.role_data = self._load_role_data()

    def _load_role_data(self) -> Dict:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, 'role_data.json')
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load role_data.json: {e}")
            return {"roles": {}, "default_skills": []}

    def _normalize(self, skill: str) -> str:
        """Normalize skill string for comparison (lowercase, stripped)."""
        return skill.lower().strip()

    def get_role_requirements(self, role_name: str) -> List[str]:
        """Get required skills for a role. Returns default list if role not found."""
        # Try exact match
        roles = self.role_data.get("roles", {})
        if role_name in roles:
            return roles[role_name]
        
        # Try case-insensitive match
        role_lower = role_name.lower()
        for r_name, skills in roles.items():
            if r_name.lower() == role_lower:
                return skills
                
        # Fallback: Check if it partially matches any key
        for r_name, skills in roles.items():
            if role_lower in r_name.lower() or r_name.lower() in role_lower:
                return skills
                
        # Final Fallback: Return generous defaults + maybe role name itself if it's a tech stack
        return self.role_data.get("default_skills", [])

    def compute_missing_skills(self, user_skills: List[str], target_role: str) -> List[str]:
        """
        Compute missing skills deterministically.
        missing = required - user_skills
        """
        required = self.get_role_requirements(target_role)
        
        user_norm = {self._normalize(s) for s in user_skills}
        missing = []
        
        for req in required:
            if self._normalize(req) not in user_norm:
                missing.append(req)
                
        return missing

role_manager = RoleManager()
