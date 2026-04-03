"""
HuggingFace Data Loader - DISABLED.

This module has been neutered to prevent 60-second cold-start downloads.
All functionality now uses web search via web_skill_extractor.py instead.

Keeping the module for backward compatibility with existing imports.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HFDataLoader:
    """
    Disabled HuggingFace data loader.

    All methods now return empty data to prevent any HF network calls.
    Role-to-skills functionality is handled by web_skill_extractor.py.
    """

    _instance = None
    _initialized = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_loaded(self):
        """No-op: HuggingFace datasets disabled for performance."""
        pass

    def _ensure_projects_loaded(self):
        """No-op: Projects now come from web search."""
        pass

    def _ensure_learning_paths_loaded(self):
        """No-op: Learning paths now generated via AI."""
        pass

    def get_all_job_titles(self) -> List[str]:
        """Return empty list - use web search for job titles."""
        return []

    def find_matching_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        """Return empty list - use web search for jobs."""
        return []

    def get_job_links_for_titles(self, job_titles: List[str]) -> List[str]:
        """Return empty list."""
        return []

    def get_skills_for_job_links(self, job_links: List[str]) -> Dict[str, List[str]]:
        """Return empty dict - skills now come from web search."""
        return {}

    def get_projects_for_skills(self, skills: List[str], limit: int = 5) -> List[Dict]:
        """Return empty list - projects now generated via AI."""
        return []

    def get_learning_path_for_skill(self, skill: str, days: int = 7) -> Dict:
        """Return empty dict - paths now generated via AI."""
        return {}

    def get_required_skills(self, query: str, limit_jobs: int = 20) -> List[str]:
        """Return empty list - use web_skill_extractor.search_role_skills instead."""
        return []

    def get_similar_job_titles(self, query: str, limit: int = 10) -> List[str]:
        """Return empty list - use web search for autocomplete."""
        return []


hf_loader = HFDataLoader()


def get_all_job_titles():
    return hf_loader.get_all_job_titles()


def find_matching_jobs(query: str, limit: int = 10):
    return hf_loader.find_matching_jobs(query, limit)


def get_required_skills(query: str, limit_jobs: int = 20):
    return hf_loader.get_required_skills(query, limit_jobs)


def get_similar_job_titles(query: str, limit: int = 10):
    return hf_loader.get_similar_job_titles(query, limit)


def get_projects_for_skills(skills: List[str], limit: int = 5):
    return hf_loader.get_projects_for_skills(skills, limit)


def get_learning_path_for_skill(skill: str, days: int = 7):
    return hf_loader.get_learning_path_for_skill(skill, days)


logger.info("HuggingFace data loader DISABLED - using web search instead")
