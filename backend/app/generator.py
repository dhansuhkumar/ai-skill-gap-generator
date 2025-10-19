import os
from pathlib import Path
import zipfile



BASE_DIR = Path(__file__).parent / "projects"

# Create projects folder if it doesn't exist
BASE_DIR.mkdir(exist_ok=True)

def create_project(skill):
    """Creates a small starter project folder with a README"""
    skill_dir = BASE_DIR / skill.replace(" ", "_")
    skill_dir.mkdir(exist_ok=True)
    
    # Create README file with instructions
    readme_path = skill_dir / "README.txt"
    with open(readme_path, "w") as f:
        f.write(f"Starter project for skill: {skill}\n")
        f.write("Instructions: Try to implement a small project using this skill.\n")
    
    return skill_dir

def create_zip(skill):
    """Generate a zip file of the starter project"""
    skill_dir = create_project(skill)
    zip_path = BASE_DIR / f"{skill.replace(' ', '_')}.zip"
    
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in skill_dir.rglob("*"):
            zipf.write(file, arcname=file.relative_to(BASE_DIR))
    
    return zip_path
