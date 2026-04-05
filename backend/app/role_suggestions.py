# backend/app/role_suggestions.py
"""
Alternative Role Suggestions - Find roles user has high chance to become.
Uses web search instead of HuggingFace datasets.
OPTIMIZED: Parallel skill lookups for faster alternative role discovery.
"""

from typing import List, Dict
from .web_skill_extractor import search_role_skills, get_tech_skills_vocab, _SKILL_CACHE
from .skill_cleaner import clean_and_deduplicate_skills
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

COMMON_ROLES = [
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Software Engineer",
    "Data Scientist",
    "Data Engineer",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Mobile Developer",
    "QA Engineer",
    "Security Engineer",
    "Product Manager",
    "Web Developer",
    "UI/UX Designer",
]

ROLE_REQUIRED_SKILLS = {
    "Frontend Developer": [
        "JavaScript",
        "React",
        "HTML",
        "CSS",
        "TypeScript",
        "Git",
        "REST API",
        "Responsive Design",
    ],
    "Backend Developer": [
        "Python",
        "Java",
        "Node.js",
        "SQL",
        "REST API",
        "Git",
        "Linux",
        "Docker",
    ],
    "Full Stack Developer": [
        "JavaScript",
        "React",
        "Python",
        "SQL",
        "REST API",
        "Git",
        "Docker",
        "HTML",
        "CSS",
    ],
    "Software Engineer": [
        "Python",
        "Java",
        "SQL",
        "Git",
        "Docker",
        "REST API",
        "Data Structures",
        "Algorithms",
    ],
    "Data Scientist": [
        "Python",
        "Data Science",
        "Machine Learning",
        "SQL",
        "Statistics",
        "Pandas",
        "Visualization",
    ],
    "Data Engineer": [
        "Python",
        "SQL",
        "Spark",
        "Airflow",
        "Kafka",
        "AWS",
        "Data Engineering",
        "ETL",
    ],
    "Machine Learning Engineer": [
        "Python",
        "Machine Learning",
        "TensorFlow",
        "PyTorch",
        "SQL",
        "Deep Learning",
        "MLOps",
    ],
    "DevOps Engineer": [
        "Docker",
        "Kubernetes",
        "AWS",
        "Linux",
        "CI/CD",
        "Terraform",
        "Git",
        "Ansible",
    ],
    "Cloud Engineer": [
        "AWS",
        "Azure",
        "Docker",
        "Kubernetes",
        "Linux",
        "Terraform",
        "CI/CD",
        "Python",
    ],
    "Mobile Developer": [
        "React Native",
        "Flutter",
        "iOS",
        "Android",
        "JavaScript",
        "API",
        "Git",
    ],
    "QA Engineer": [
        "Testing",
        "Selenium",
        "Python",
        "Automation",
        "Jest",
        "Cypress",
        "Git",
        "Agile",
    ],
    "Security Engineer": [
        "Security",
        "Cybersecurity",
        "Python",
        "Network Security",
        "Penetration Testing",
        "AWS",
    ],
    "Product Manager": [
        "Agile",
        "Communication",
        "Data Analysis",
        "Project Management",
        "SQL",
        "Strategy",
    ],
    "Web Developer": [
        "JavaScript",
        "React",
        "HTML",
        "CSS",
        "Python",
        "SQL",
        "Git",
        "REST API",
    ],
    "UI/UX Designer": [
        "Figma",
        "HTML",
        "CSS",
        "User Research",
        "Prototyping",
        "Design Systems",
        "Wireframing",
    ],
}


def get_alternative_roles(user_skills: List[str], limit: int = 5) -> List[Dict]:
    """
    Find alternative roles user has high chance to become based on their current skills.
    OPTIMIZED: Uses pre-defined skills map to avoid slow web searches.

    Args:
        user_skills: List of skills the user already has
        limit: Number of alternative roles to return

    Returns:
        List of dicts with role, match_score, etc.
    """
    print(f"🔍 Finding alternative roles for {len(user_skills)} user skills")

    if not user_skills:
        return []

    user_skills_lower = {s.lower().strip() for s in user_skills}
    role_matches = []

    for role, required_skills in ROLE_REQUIRED_SKILLS.items():
        required_lower = {s.lower().strip() for s in required_skills}
        matched = user_skills_lower.intersection(required_lower)

        if required_lower:
            match_score = int((len(matched) / len(required_lower)) * 100)
        else:
            match_score = 0

        if match_score >= 15:
            role_matches.append(
                {
                    "role": role,
                    "match_score": match_score,
                    "user_skills_count": len(matched),
                    "required_skills_count": len(required_lower),
                    "missing_skills_count": len(required_lower) - len(matched),
                }
            )

    role_matches.sort(key=lambda x: x["match_score"], reverse=True)
    print(f"✅ Found {len(role_matches)} alternative roles")

    return role_matches[:limit]
