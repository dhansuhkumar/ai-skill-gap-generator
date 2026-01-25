"""
Data Fusion Service

Combines data from multiple sources (GitHub, skill analysis, learning paths)
into a unified structure for frontend visualization components.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def create_skill_comparison_data(
    user_skills: List[str],
    github_data: Optional[Dict],
    role_required_skills: List[str]
) -> Dict[str, Any]:
    """
    Create data structure for radar/spider chart comparing current vs required skills.
    
    Args:
        user_skills: List of user's current skills
        github_data: GitHub analysis result with language proficiency scores
        role_required_skills: Skills required for target role
    
    Returns:
        {
            "skills": [
                {
                    "name": "Python",
                    "current_proficiency": 75,  # From GitHub
                    "required_proficiency": 90,
                    "gap": 15,
                    "source": "github"
                },
                ...
            ],
            "average_current": 65,
            "average_required": 80,
            "overall_gap": 15
        }
    """
    skill_comparison = []
    github_languages = github_data.get("languages", {}) if github_data else {}
    
    # Combine all unique skills
    all_skills = set(user_skills + role_required_skills)
    
    for skill in all_skills:
        # Get current proficiency from GitHub if available
        current_prof = 0
        source = "manual"
        
        if skill in github_languages:
            current_prof = github_languages[skill].get("score", 0)
            source = "github"
        elif skill.lower() in user_skills:
            # Manual skill, assign default proficiency
            current_prof = 60
        
        # Required proficiency (default 80 for all required skills)
        required_prof = 80 if skill in role_required_skills else 0
        
        if required_prof > 0 or current_prof > 0:
            skill_comparison.append({
                "name": skill,
                "current_proficiency": current_prof,
                "required_proficiency": required_prof,
                "gap": max(0, required_prof - current_prof),
                "source": source,
                "has_gap": current_prof < required_prof
            })
    
    # Sort by gap (highest first)
    skill_comparison.sort(key=lambda x: x["gap"], reverse=True)
    
    # Calculate averages
    if skill_comparison:
        avg_current = sum(s["current_proficiency"] for s in skill_comparison) / len(skill_comparison)
        avg_required = sum(s["required_proficiency"] for s in skill_comparison) / len(skill_comparison)
    else:
        avg_current = 0
        avg_required = 0
    
    return {
        "skills": skill_comparison[:10],  # Top 10 for visualization
        "average_current": round(avg_current, 1),
        "average_required": round(avg_required, 1),
        "overall_gap": round(avg_required - avg_current, 1)
    }


def create_learning_timeline_data(
    learning_paths: Dict[str, Any],
    progress_data: Optional[List[Dict]] = None
) -> List[Dict[str, Any]]:
    """
    Create timeline data for learning path visualization.
    
    Args:
        learning_paths: Learning paths from AI generator
        progress_data: User's progress on learning steps
    
    Returns:
        [
            {
                "skill": "Python",
                "milestones": [
                    {
                        "day_from": 1,
                        "day_to": 5,
                        "title": "Python Basics",
                        "tasks": [...],
                        "completed": false,
                        "step_index": 0
                    },
                    ...
                ]
            },
            ...
        ]
    """
    timeline_data = []
    
    # Create progress lookup
    progress_lookup = {}
    if progress_data:
        for prog in progress_data:
            key = f"{prog['skill_name']}_{prog['step_index']}"
            progress_lookup[key] = prog.get("completed", False)
    
    for skill_name, skill_data in learning_paths.items():
        steps = skill_data.get("steps", [])
        milestones = []
        
        for idx, step in enumerate(steps):
            key = f"{skill_name}_{idx}"
            milestones.append({
                "day_from": step.get("day_from", idx * 5 + 1),
                "day_to": step.get("day_to", (idx + 1) * 5),
                "title": step.get("title", f"Step {idx + 1}"),
                "tasks": step.get("tasks", []),
                "project": step.get("project"),
                "completed": progress_lookup.get(key, False),
                "step_index": idx
            })
        
        timeline_data.append({
            "skill": skill_name,
            "summary": skill_data.get("summary", ""),
            "milestones": milestones,
            "total_steps": len(milestones),
            "completed_steps": sum(1 for m in milestones if m["completed"]),
            "progress_percentage": round(
                sum(1 for m in milestones if m["completed"]) / len(milestones) * 100, 1
            ) if milestones else 0
        })
    
    return timeline_data


def create_github_insights_data(github_data: Optional[Dict]) -> Dict[str, Any]:
    """
    Extract GitHub insights for visualization.
    
    Args:
        github_data: Full GitHub analysis result
    
    Returns:
        {
            "username": "user123",
            "total_repos": 15,
            "languages": [...],
            "diversity_score": 10,
            "commit_timeline": [...]  # For heatmap
        }
    """
    if not github_data:
        return {
            "username": None,
            "total_repos": 0,
            "languages": [],
            "diversity_score": 0,
            "commit_timeline": [],
            "available": False
        }
    
    languages = []
    for lang, data in github_data.get("languages", {}).items():
        languages.append({
            "name": lang,
            "score": data.get("score", 0),
            "repos": data.get("repos", 0),
            "has_tests": data.get("has_tests", False),
            "has_devops": data.get("has_devops", False),
            "starred_repos": data.get("starred_repos", 0)
        })
    
    # Sort by score
    languages.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "username": github_data.get("username"),
        "total_repos": github_data.get("total_repos", 0),
        "languages": languages[:10],  # Top 10
        "diversity_score": github_data.get("diversity_bonus", 0),
        "language_count": github_data.get("language_count", 0),
        "commit_timeline": github_data.get("commit_timeline", []),
        "available": True
    }


def create_skill_network_data(
    skills: List[str],
    projects: List[Dict],
    videos: List[Dict],
    learning_paths: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create network graph data showing relationships between skills, projects, and resources.
    
    Args:
        skills: List of skill names
        projects: Portfolio projects
        videos: Learning videos
        learning_paths: Learning path data
    
    Returns:
        {
            "nodes": [
                {"id": "skill_python", "type": "skill", "label": "Python", "proficiency": 75},
                {"id": "project_1", "type": "project", "label": "Todo App"},
                {"id": "video_1", "type": "video", "label": "Python Tutorial"},
                ...
            ],
            "edges": [
                {"source": "skill_python", "target": "project_1", "type": "required_for"},
                {"source": "video_1", "target": "skill_python", "type": "teaches"},
                ...
            ]
        }
    """
    nodes = []
    edges = []
    
    # Add skill nodes
    for skill in skills:
        skill_id = f"skill_{skill.lower().replace(' ', '_')}"
        nodes.append({
            "id": skill_id,
            "type": "skill",
            "label": skill,
            "proficiency": learning_paths.get(skill, {}).get("current_proficiency", 50),
            "category": "skill"
        })
    
    # Add project nodes and edges
    for idx, project in enumerate(projects):
        project_id = f"project_{idx}"
        nodes.append({
            "id": project_id,
            "type": "project",
            "label": project.get("title", f"Project {idx + 1}"),
            "description": project.get("description", ""),
            "category": "project"
        })
        
        # Connect project to its required skills
        for skill in project.get("skills", []):
            skill_id = f"skill_{skill.lower().replace(' ', '_')}"
            edges.append({
                "source": skill_id,
                "target": project_id,
                "type": "required_for",
                "label": "required for"
            })
    
    # Add video nodes and edges (limit to 10 most relevant)
    for idx, video in enumerate(videos[:10]):
        video_id = f"video_{idx}"
        nodes.append({
            "id": video_id,
            "type": "video",
            "label": video.get("title", f"Video {idx + 1}"),
            "url": video.get("url", ""),
            "channel": video.get("channel", ""),
            "category": "resource"
        })
        
        # Try to connect video to relevant skills (based on title matching)
        video_title_lower = video.get("title", "").lower()
        for skill in skills:
            if skill.lower() in video_title_lower:
                skill_id = f"skill_{skill.lower().replace(' ', '_')}"
                edges.append({
                    "source": video_id,
                    "target": skill_id,
                    "type": "teaches",
                    "label": "teaches"
                })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


def create_unified_dashboard_data(
    user_skills: List[str],
    role_analysis: Dict[str, Any],
    github_data: Optional[Dict],
    learning_path: Dict[str, Any],
    progress_data: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Main fusion function: combines all data sources into unified dashboard structure.
    
    Args:
        user_skills: User's current skills
        role_analysis: Role gap analysis result
        github_data: GitHub analysis result
        learning_path: Generated learning path
        progress_data: User's learning progress
    
    Returns:
        Complete dashboard data with all visualizations
    """
    learning_paths = learning_path.get("skills", {})
    projects = learning_path.get("projects", [])
    videos = learning_path.get("videos", [])
    required_skills = role_analysis.get("required_skills", [])
    
    return {
        "skill_comparison": create_skill_comparison_data(
            user_skills, github_data, required_skills
        ),
        "learning_timeline": create_learning_timeline_data(
            learning_paths, progress_data
        ),
        "github_insights": create_github_insights_data(github_data),
        "skill_network": create_skill_network_data(
            list(learning_paths.keys()), projects, videos, learning_paths
        ),
        "summary": {
            "total_skills": len(user_skills),
            "skills_to_learn": len(learning_paths),
            "projects": len(projects),
            "videos": len(videos),
            "github_available": github_data is not None,
            "matching_score": learning_path.get("matching_score", 0)
        }
    }
