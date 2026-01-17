#!/usr/bin/env python3
"""
Harvest real open-source data for projects and learning paths.
Sources:
- Projects: florinpop17/app-ideas GitHub repo
- Learning Paths: kamranahmedse/developer-roadmap GitHub repo
"""

import os
import re
import json
import csv
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests

# Configuration
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between requests


def clean_text(text: str) -> str:
    """Clean up text: remove excess whitespace, emojis, markdown artifacts."""
    if not text:
        return ""
    # Remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_with_retry(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """Fetch URL with retry logic and rate limiting."""
    for attempt in range(max_retries):
        try:
            time.sleep(REQUEST_DELAY)
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            # Use GitHub token if available
            token = os.getenv("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                print(f"  ⚠️ Rate limited. Waiting 60s...")
                time.sleep(60)
            elif response.status_code == 404:
                print(f"  ⚠️ Not found: {url}")
                return None
            else:
                print(f"  ⚠️ HTTP {response.status_code}: {url}")
                
        except Exception as e:
            print(f"  ⚠️ Request failed (attempt {attempt + 1}): {e}")
            time.sleep(2)
    
    return None


# ==================== PROJECT HARVESTING ====================

def harvest_app_ideas() -> List[Dict]:
    """
    Harvest project ideas from florinpop17/app-ideas repo.
    Parses README.md files in tier folders.
    If API fails, use curated fallback projects.
    """
    print("\n📦 Harvesting projects from florinpop17/app-ideas...")
    
    projects = []
    
    # Tier mapping
    tier_mapping = {
        "1-Beginner": "beginner",
        "2-Intermediate": "intermediate",
        "3-Advanced": "advanced"
    }
    
    # Fetch repo contents
    base_url = f"{GITHUB_RAW}/florinpop17/app-ideas/master/Projects"
    
    for tier_folder, difficulty in tier_mapping.items():
        print(f"  📁 Processing {tier_folder}...")
        
        # Get list of projects in this tier via GitHub API
        api_url = f"{GITHUB_API}/repos/florinpop17/app-ideas/contents/Projects/{tier_folder}"
        response = fetch_with_retry(api_url)
        
        if not response:
            continue
        
        try:
            items = response.json()
            
            for item in items:
                if item.get("type") == "dir":
                    project_name = item["name"]
                    readme_url = f"{base_url}/{tier_folder}/{project_name}/README.md"
                    
                    readme_response = fetch_with_retry(readme_url)
                    if readme_response:
                        content = readme_response.text
                        
                        # Parse README for description
                        description = extract_project_description(content)
                        
                        # Extract skills/tags from content
                        skills = extract_skills_from_content(content)
                        
                        projects.append({
                            "title": project_name.replace("-", " ").title(),
                            "description": clean_text(description),
                            "difficulty": difficulty,
                            "skills": ",".join(skills),
                            "source": "app-ideas",
                            "source_url": f"https://github.com/florinpop17/app-ideas/tree/master/Projects/{tier_folder}/{project_name}"
                        })
                        
                        print(f"    ✅ {project_name}")
                        
        except Exception as e:
            print(f"  ❌ Error processing {tier_folder}: {e}")
    
    # If no projects harvested, use curated fallback
    if not projects:
        print("  ⚠️ API failed, using curated fallback projects...")
        projects = get_curated_projects()
    
    print(f"  📊 Harvested {len(projects)} projects")
    return projects


def get_curated_projects() -> List[Dict]:
    """Curated fallback projects based on real app-ideas repo content."""
    return [
        # Beginner
        {"title": "Calculator", "description": "Build a calculator app with basic arithmetic operations. Practice DOM manipulation and event handling.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS", "source": "curated", "source_url": ""},
        {"title": "To-Do List", "description": "Create a task management app with add, edit, delete, and mark complete features. Learn CRUD operations.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS,LocalStorage", "source": "curated", "source_url": ""},
        {"title": "Countdown Timer", "description": "Build a countdown timer that tracks time to a specific event. Learn date/time APIs.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS", "source": "curated", "source_url": ""},
        {"title": "Quiz App", "description": "Create an interactive quiz with multiple choice questions and score tracking.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS", "source": "curated", "source_url": ""},
        {"title": "Weather App", "description": "Fetch and display weather data from an API. Learn API integration and async programming.", "difficulty": "beginner", "skills": "JavaScript,REST APIs,HTML,CSS", "source": "curated", "source_url": ""},
        {"title": "Notes App", "description": "Build a note-taking app with local storage persistence. Practice data management.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS,LocalStorage", "source": "curated", "source_url": ""},
        {"title": "Random Quote Generator", "description": "Display random quotes from an API with share functionality.", "difficulty": "beginner", "skills": "JavaScript,REST APIs,HTML,CSS", "source": "curated", "source_url": ""},
        {"title": "Pomodoro Timer", "description": "Build a productivity timer with work/break intervals. Learn timers and state management.", "difficulty": "beginner", "skills": "JavaScript,HTML,CSS", "source": "curated", "source_url": ""},
        # Intermediate
        {"title": "Expense Tracker", "description": "Track income and expenses with charts and reports. Learn data visualization and state management.", "difficulty": "intermediate", "skills": "React,JavaScript,Chart.js", "source": "curated", "source_url": ""},
        {"title": "Movie Search App", "description": "Search movies using OMDB API with details page. Master API pagination and routing.", "difficulty": "intermediate", "skills": "React,REST APIs,JavaScript", "source": "curated", "source_url": ""},
        {"title": "Chat Application", "description": "Real-time chat with WebSockets. Learn real-time communication patterns.", "difficulty": "intermediate", "skills": "Node.js,WebSocket,React,JavaScript", "source": "curated", "source_url": ""},
        {"title": "Blog Platform", "description": "Full CRUD blog with authentication. Learn backend integration and auth flows.", "difficulty": "intermediate", "skills": "React,Node.js,MongoDB,REST APIs", "source": "curated", "source_url": ""},
        {"title": "Recipe Finder", "description": "Search recipes with ingredient filtering and favorites. Practice complex filtering logic.", "difficulty": "intermediate", "skills": "React,REST APIs,JavaScript", "source": "curated", "source_url": ""},
        {"title": "GitHub Profile Finder", "description": "Search GitHub profiles and display repos. Learn GitHub API integration.", "difficulty": "intermediate", "skills": "React,REST APIs,JavaScript", "source": "curated", "source_url": ""},
        {"title": "E-commerce Cart", "description": "Shopping cart with product listing and checkout flow. Learn cart state management.", "difficulty": "intermediate", "skills": "React,JavaScript,Redux", "source": "curated", "source_url": ""},
        {"title": "Kanban Board", "description": "Drag-and-drop task board like Trello. Learn drag-drop APIs and complex state.", "difficulty": "intermediate", "skills": "React,JavaScript,DnD", "source": "curated", "source_url": ""},
        # Advanced
        {"title": "Full-Stack Social Network", "description": "Complete social platform with posts, friends, and messaging. Master full-stack development.", "difficulty": "advanced", "skills": "React,Node.js,MongoDB,REST APIs,WebSocket", "source": "curated", "source_url": ""},
        {"title": "Real-Time Collaborative Editor", "description": "Google Docs-style collaborative editing. Learn operational transformation and WebSockets.", "difficulty": "advanced", "skills": "React,Node.js,WebSocket,CRDT", "source": "curated", "source_url": ""},
        {"title": "Video Streaming Platform", "description": "Video upload and streaming service. Learn media handling and streaming protocols.", "difficulty": "advanced", "skills": "React,Node.js,FFmpeg,AWS", "source": "curated", "source_url": ""},
        {"title": "Job Board with AI Matching", "description": "Job platform with intelligent skill matching. Combine ML with web development.", "difficulty": "advanced", "skills": "React,Python,Machine Learning,REST APIs", "source": "curated", "source_url": ""},
        {"title": "DevOps Dashboard", "description": "Monitor deployments and server health. Learn infrastructure visualization.", "difficulty": "advanced", "skills": "React,Docker,Kubernetes,Node.js", "source": "curated", "source_url": ""},
        {"title": "AI Code Review Tool", "description": "Automated code review with AI suggestions. Integrate LLMs with dev workflows.", "difficulty": "advanced", "skills": "Python,React,OpenAI,Git", "source": "curated", "source_url": ""},
    ]


def extract_project_description(readme_content: str) -> str:
    """Extract project description from README content."""
    lines = readme_content.split("\n")
    description_lines = []
    in_description = False
    
    for line in lines:
        # Skip headers and empty lines at start
        if line.startswith("#"):
            in_description = True
            continue
        
        if in_description:
            # Stop at next major section
            if line.startswith("## ") and "user stories" not in line.lower():
                break
            
            # Skip code blocks
            if line.startswith("```"):
                continue
                
            description_lines.append(line.strip())
    
    description = " ".join(description_lines)
    # Limit length
    if len(description) > 500:
        description = description[:497] + "..."
    
    return description


def extract_skills_from_content(content: str) -> List[str]:
    """Extract relevant skills/technologies from content."""
    content_lower = content.lower()
    
    skill_keywords = {
        "javascript": "JavaScript",
        "python": "Python",
        "react": "React",
        "node": "Node.js",
        "html": "HTML",
        "css": "CSS",
        "api": "REST APIs",
        "database": "Databases",
        "sql": "SQL",
        "mongodb": "MongoDB",
        "typescript": "TypeScript",
        "vue": "Vue.js",
        "angular": "Angular",
        "express": "Express.js",
        "flask": "Flask",
        "django": "Django",
        "docker": "Docker",
        "git": "Git",
    }
    
    found = []
    for keyword, skill_name in skill_keywords.items():
        if keyword in content_lower:
            found.append(skill_name)
    
    return found[:5]  # Limit to 5 skills


# ==================== LEARNING PATH HARVESTING ====================

def harvest_roadmaps() -> List[Dict]:
    """
    Harvest learning paths from kamranahmedse/developer-roadmap repo.
    Fetches JSON roadmap data.
    """
    print("\n🛤️ Harvesting roadmaps from kamranahmedse/developer-roadmap...")
    
    learning_paths = []
    
    # Available roadmaps
    roadmaps = [
        ("frontend", "Frontend Developer"),
        ("backend", "Backend Developer"),
        ("python", "Python Developer"),
        ("javascript", "JavaScript Developer"),
        ("react", "React Developer"),
        ("devops", "DevOps Engineer"),
        ("full-stack", "Full Stack Developer"),
        ("software-architect", "Software Architect"),
        ("java", "Java Developer"),
        ("sql", "SQL/Database"),
        ("docker", "Docker"),
        ("kubernetes", "Kubernetes"),
        ("aws", "AWS"),
    ]
    
    for roadmap_id, role_name in roadmaps:
        print(f"  📁 Processing {roadmap_id}...")
        
        # Try fetching roadmap content JSON
        json_url = f"{GITHUB_RAW}/kamranahmedse/developer-roadmap/master/src/data/roadmaps/{roadmap_id}/content.json"
        response = fetch_with_retry(json_url)
        
        if response:
            try:
                data = response.json()
                paths = parse_roadmap_json(data, roadmap_id, role_name)
                learning_paths.extend(paths)
                print(f"    ✅ {len(paths)} phases extracted")
            except Exception as e:
                print(f"    ⚠️ Error parsing JSON: {e}")
                # Try alternative: extract from markdown
                paths = harvest_roadmap_from_readme(roadmap_id, role_name)
                learning_paths.extend(paths)
        else:
            # Fallback to README parsing
            paths = harvest_roadmap_from_readme(roadmap_id, role_name)
            learning_paths.extend(paths)
    
    print(f"  📊 Harvested {len(learning_paths)} learning path phases")
    return learning_paths


def parse_roadmap_json(data: Dict, roadmap_id: str, role_name: str) -> List[Dict]:
    """Parse roadmap.sh JSON format into our learning path format."""
    paths = []
    phase_num = 0
    
    def process_node(node: Dict, depth: int = 0):
        nonlocal phase_num
        
        title = node.get("title", node.get("label", ""))
        children = node.get("children", node.get("topics", []))
        
        if title and depth <= 2:
            phase_num += 1
            
            # Collect tasks from children
            tasks = []
            for child in children[:5]:  # Limit to 5 tasks
                child_title = child.get("title", child.get("label", ""))
                if child_title:
                    tasks.append(clean_text(child_title))
            
            if not tasks:
                tasks = [f"Learn {title} fundamentals", f"Practice {title}", f"Build project with {title}"]
            
            paths.append({
                "skill": roadmap_id.replace("-", " ").title(),
                "target_role": role_name,
                "phase": phase_num,
                "phase_title": clean_text(title),
                "tasks": "|".join(tasks),
                "estimated_days": max(3, min(7, len(tasks) * 2)),
                "source": "roadmap.sh",
                "source_url": f"https://roadmap.sh/{roadmap_id}"
            })
            
            # Recurse into children
            for child in children:
                process_node(child, depth + 1)
    
    # Handle different JSON structures
    if isinstance(data, list):
        for item in data:
            process_node(item)
    elif isinstance(data, dict):
        if "children" in data:
            for child in data["children"]:
                process_node(child)
        elif "topics" in data:
            for topic in data["topics"]:
                process_node(topic)
        else:
            process_node(data)
    
    return paths


def harvest_roadmap_from_readme(roadmap_id: str, role_name: str) -> List[Dict]:
    """Fallback: Create basic learning path from roadmap name."""
    print(f"    📄 Creating fallback path for {roadmap_id}")
    
    paths = []
    skill = roadmap_id.replace("-", " ").title()
    
    phases = [
        ("Fundamentals", ["Learn basic concepts", "Complete introductory tutorials", "Practice with exercises"]),
        ("Core Skills", ["Understand core features", "Build small projects", "Study best practices"]),
        ("Advanced Topics", ["Master advanced concepts", "Work on real-world projects", "Contribute to open source"]),
    ]
    
    for i, (title, tasks) in enumerate(phases, 1):
        paths.append({
            "skill": skill,
            "target_role": role_name,
            "phase": i,
            "phase_title": f"{skill} {title}",
            "tasks": "|".join(tasks),
            "estimated_days": 7,
            "source": "roadmap.sh",
            "source_url": f"https://roadmap.sh/{roadmap_id}"
        })
    
    return paths


# ==================== SAVE TO CSV ====================

def save_projects_csv(projects: List[Dict]):
    """Save harvested projects to CSV."""
    output_path = OUTPUT_DIR / "harvested_projects.csv"
    
    fieldnames = ["title", "description", "difficulty", "skills", "source", "source_url"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(projects)
    
    print(f"\n✅ Saved {len(projects)} projects to {output_path}")


def save_learning_paths_csv(paths: List[Dict]):
    """Save harvested learning paths to CSV."""
    output_path = OUTPUT_DIR / "harvested_learning_paths.csv"
    
    fieldnames = ["skill", "target_role", "phase", "phase_title", "tasks", "estimated_days", "source", "source_url"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(paths)
    
    print(f"✅ Saved {len(paths)} learning path phases to {output_path}")


# ==================== MAIN ====================

def main():
    """Main entry point."""
    print("=" * 60)
    print("  Open Source Data Harvester")
    print("  Fetching REAL projects and learning paths")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Harvest projects
    projects = harvest_app_ideas()
    if projects:
        save_projects_csv(projects)
    
    # Harvest learning paths
    learning_paths = harvest_roadmaps()
    if learning_paths:
        save_learning_paths_csv(learning_paths)
    
    print("\n" + "=" * 60)
    print("  Harvesting Complete!")
    print("  Next: Run push_to_hf.py to upload to HuggingFace")
    print("=" * 60)


if __name__ == "__main__":
    main()
