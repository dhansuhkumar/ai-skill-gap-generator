"""
HuggingFace Data Loader - Loads job/skill data from HuggingFace Datasets.
Uses Arrow/Parquet format with local caching for fast retrieval.
"""

import os
from typing import List, Dict, Optional
from collections import Counter

# HuggingFace dataset configuration
HF_USERNAME = os.getenv("HF_USERNAME", "dhansuhkumar")
HF_JOBS_DATASET = os.getenv("HF_JOBS_DATASET", f"{HF_USERNAME}/skill-gap-jobs")
HF_SKILLS_DATASET = os.getenv("HF_SKILLS_DATASET", f"{HF_USERNAME}/skill-gap-skills")
HF_PROJECTS_DATASET = os.getenv("HF_PROJECTS_DATASET", f"{HF_USERNAME}/skill-gap-projects")
HF_LEARNING_PATHS_DATASET = os.getenv("HF_LEARNING_PATHS_DATASET", f"{HF_USERNAME}/skill-gap-learning-paths")


class HFDataLoader:
    """Load and query job/skill data from HuggingFace Datasets with local caching."""
    
    _instance = None
    _jobs_df = None
    _skills_df = None
    _projects_df = None
    _learning_paths_df = None
    _initialized = False
    _projects_initialized = False
    _paths_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _ensure_loaded(self):
        """Lazy load datasets on first access."""
        if self._initialized:
            return
        
        try:
            from datasets import load_dataset
            import pandas as pd
            
            print(f"📥 Loading datasets from HuggingFace Hub...")
            print(f"   Jobs: {HF_JOBS_DATASET}")
            print(f"   Skills: {HF_SKILLS_DATASET}")
            
            # Load datasets - HuggingFace caches locally in Arrow format
            jobs_ds = load_dataset(HF_JOBS_DATASET, split="train")
            skills_ds = load_dataset(HF_SKILLS_DATASET, split="train")
            
            # Convert to pandas for fast in-memory operations
            self._jobs_df = jobs_ds.to_pandas()
            self._skills_df = skills_ds.to_pandas()
            
            print(f"✅ Loaded {len(self._jobs_df):,} jobs and {len(self._skills_df):,} skill mappings")
            self._initialized = True
            
        except Exception as e:
            print(f"❌ Failed to load HuggingFace datasets: {e}")
            import pandas as pd
            self._jobs_df = pd.DataFrame()
            self._skills_df = pd.DataFrame()
            self._initialized = True
    
    def _ensure_projects_loaded(self):
        """Lazy load projects dataset."""
        if self._projects_initialized:
            return
        
        try:
            from datasets import load_dataset
            import pandas as pd
            
            print(f"📥 Loading projects from: {HF_PROJECTS_DATASET}")
            projects_ds = load_dataset(HF_PROJECTS_DATASET, split="train")
            self._projects_df = projects_ds.to_pandas()
            print(f"✅ Loaded {len(self._projects_df)} projects")
            self._projects_initialized = True
            
        except Exception as e:
            print(f"⚠️ Failed to load projects dataset: {e}")
            import pandas as pd
            self._projects_df = pd.DataFrame()
            self._projects_initialized = True
    
    def _ensure_learning_paths_loaded(self):
        """Lazy load learning paths dataset."""
        if self._paths_initialized:
            return
        
        try:
            from datasets import load_dataset
            import pandas as pd
            
            print(f"📥 Loading learning paths from: {HF_LEARNING_PATHS_DATASET}")
            paths_ds = load_dataset(HF_LEARNING_PATHS_DATASET, split="train")
            self._learning_paths_df = paths_ds.to_pandas()
            print(f"✅ Loaded {len(self._learning_paths_df)} learning path phases")
            self._paths_initialized = True
            
        except Exception as e:
            print(f"⚠️ Failed to load learning paths dataset: {e}")
            import pandas as pd
            self._learning_paths_df = pd.DataFrame()
            self._paths_initialized = True
    
    def get_all_job_titles(self) -> List[str]:
        """Return all unique job titles."""
        self._ensure_loaded()
        if self._jobs_df is None or 'job_title' not in self._jobs_df.columns:
            return []
        return self._jobs_df['job_title'].dropna().unique().tolist()
    
    def find_matching_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find jobs matching a query string.
        Uses case-insensitive partial matching.
        """
        self._ensure_loaded()
        if self._jobs_df is None or self._jobs_df.empty:
            return []
        
        query_lower = query.lower()
        
        # Filter jobs where job_title contains query
        mask = self._jobs_df['job_title'].str.lower().str.contains(query_lower, na=False)
        matched = self._jobs_df[mask].head(limit)
        
        results = []
        for _, row in matched.iterrows():
            results.append({
                'job_link': row.get('job_link', ''),
                'job_title': row.get('job_title', ''),
                'company': row.get('company', ''),
                'job_location': row.get('job_location', ''),
                'job_level': row.get('job_level', ''),
                'job_type': row.get('job_type', '')
            })
        
        return results
    
    def get_job_links_for_titles(self, job_titles: List[str]) -> List[str]:
        """Get job_links for a list of job titles."""
        self._ensure_loaded()
        if self._jobs_df is None or self._jobs_df.empty or not job_titles:
            return []
        
        import pandas as pd
        # Create a mask for matching titles
        titles_set = set(t.lower() for t in job_titles)
        mask = self._jobs_df['job_title'].str.lower().apply(
            lambda x: x in titles_set if pd.notna(x) else False
        )
        
        return self._jobs_df[mask]['job_link'].dropna().unique().tolist()
    
    def get_skills_for_job_links(self, job_links: List[str]) -> Dict[str, List[str]]:
        """Get skills mapping for a list of job_links."""
        self._ensure_loaded()
        if self._skills_df is None or self._skills_df.empty or not job_links:
            return {}
        
        import pandas as pd
        # Filter skills dataframe by job_links
        mask = self._skills_df['job_link'].isin(job_links)
        filtered = self._skills_df[mask]
        
        result = {}
        for _, row in filtered.iterrows():
            link = row['job_link']
            skills_str = row.get('job_skills', '')
            if pd.notna(skills_str) and skills_str:
                # Split skills by comma and clean
                skills = [s.strip() for s in str(skills_str).split(',')]
                result[link] = skills
        
        return result
    
    def get_skills_for_job_titles(self, job_titles: List[str]) -> List[str]:
        """Get all required skills for a list of job titles."""
        job_links = self.get_job_links_for_titles(job_titles)
        skills_map = self.get_skills_for_job_links(job_links)
        
        # Collect all skills
        all_skills = []
        for skills in skills_map.values():
            all_skills.extend(skills)
        
        return all_skills
    
    def get_required_skills(self, query: str, limit_jobs: int = 20) -> List[str]:
        """
        Get required skills for jobs matching the query.
        Returns a deduplicated list of skills ordered by frequency.
        """
        # Find matching jobs
        matched_jobs = self.find_matching_jobs(query, limit=limit_jobs)
        
        if not matched_jobs:
            return []
        
        job_titles = [j['job_title'] for j in matched_jobs]
        all_skills = self.get_skills_for_job_titles(job_titles)
        
        # Count skill frequency and return most common
        skill_counts = Counter(all_skills)
        
        # Return unique skills, prioritizing more common ones
        seen = set()
        result = []
        for skill, count in skill_counts.most_common():
            normalized = skill.strip().lower()
            if normalized not in seen and normalized:
                seen.add(normalized)
                result.append(skill.strip())
        
        return result
    
    def get_job_details(self, job_link: str) -> Optional[Dict]:
        """Get full details for a specific job."""
        self._ensure_loaded()
        if self._jobs_df is None or self._jobs_df.empty:
            return None
        
        row = self._jobs_df[self._jobs_df['job_link'] == job_link]
        if row.empty:
            return None
        
        row = row.iloc[0]
        return {
            'job_link': row.get('job_link', ''),
            'job_title': row.get('job_title', ''),
            'company': row.get('company', ''),
            'job_location': row.get('job_location', ''),
            'job_level': row.get('job_level', ''),
            'job_type': row.get('job_type', '')
        }
    
    def get_similar_job_titles(self, query: str, limit: int = 10) -> List[str]:
        """Get job titles similar to the query (for autocomplete)."""
        all_titles = self.get_all_job_titles()
        query_lower = query.lower()
        
        # Prioritize titles that start with query
        exact_start = [t for t in all_titles if t.lower().startswith(query_lower)]
        partial = [t for t in all_titles if query_lower in t.lower() and t not in exact_start]
        
        return (exact_start + partial)[:limit]
    
    # ==================== PROJECT RETRIEVAL ====================
    
    def get_projects_for_skills(self, skills: List[str], limit: int = 5) -> List[Dict]:
        """
        Get curated project ideas matching the given skills.
        Returns projects that match any of the provided skills.
        """
        self._ensure_projects_loaded()
        if self._projects_df is None or self._projects_df.empty:
            return []
        
        skills_lower = set(s.lower().strip() for s in skills)
        matched_projects = []
        
        for _, row in self._projects_df.iterrows():
            project_skills = row.get('skills', '')
            if project_skills:
                project_skill_set = set(s.strip().lower() for s in str(project_skills).split(','))
                # Check if any skill matches
                if skills_lower & project_skill_set:
                    matched_projects.append({
                        'title': row.get('title', ''),
                        'description': row.get('description', ''),
                        'difficulty': row.get('difficulty', 'intermediate'),
                        'skills': [s.strip() for s in str(project_skills).split(',')]
                    })
        
        # If no matches, return projects based on difficulty mix
        if not matched_projects:
            for _, row in self._projects_df.head(limit).iterrows():
                matched_projects.append({
                    'title': row.get('title', ''),
                    'description': row.get('description', ''),
                    'difficulty': row.get('difficulty', 'intermediate'),
                    'skills': [s.strip() for s in str(row.get('skills', '')).split(',')]
                })
        
        return matched_projects[:limit]
    
    def get_all_projects(self) -> List[Dict]:
        """Get all available projects."""
        self._ensure_projects_loaded()
        if self._projects_df is None or self._projects_df.empty:
            return []
        
        projects = []
        for _, row in self._projects_df.iterrows():
            projects.append({
                'title': row.get('title', ''),
                'description': row.get('description', ''),
                'difficulty': row.get('difficulty', 'intermediate'),
                'skills': [s.strip() for s in str(row.get('skills', '')).split(',')]
            })
        return projects
    
    # ==================== LEARNING PATH RETRIEVAL ====================
    
    def get_learning_path_for_skill(self, skill: str, days: int = 7) -> Dict:
        """
        Get a structured learning path for a skill.
        Returns phases with tasks, scaled to the given number of days.
        """
        self._ensure_learning_paths_loaded()
        if self._learning_paths_df is None or self._learning_paths_df.empty:
            return self._generate_fallback_path(skill, days)
        
        skill_lower = skill.lower().strip()
        
        # Find learning path phases for this skill
        mask = self._learning_paths_df['skill'].str.lower().str.contains(skill_lower, na=False)
        matched = self._learning_paths_df[mask].sort_values('phase')
        
        if matched.empty:
            # Try partial match on related terms
            for _, row in self._learning_paths_df.iterrows():
                if skill_lower in str(row.get('target_role', '')).lower():
                    matched = self._learning_paths_df[
                        self._learning_paths_df['skill'] == row['skill']
                    ].sort_values('phase')
                    break
        
        if matched.empty:
            return self._generate_fallback_path(skill, days)
        
        # Build learning path from matched phases
        total_phases = len(matched)
        days_per_phase = max(1, days // total_phases)
        
        steps = []
        day_counter = 1
        
        for i, (_, row) in enumerate(matched.iterrows()):
            phase_days = days_per_phase if i < total_phases - 1 else days - day_counter + 1
            
            tasks_str = row.get('tasks', '')
            tasks = [t.strip() for t in str(tasks_str).split('|') if t.strip()]
            if not tasks:
                tasks = [f"Learn {skill} fundamentals", f"Practice {skill}", f"Build project"]
            
            steps.append({
                'day_from': day_counter,
                'day_to': day_counter + phase_days - 1,
                'title': row.get('phase_title', f"Phase {i+1}"),
                'tasks': tasks,
                'project': f"{skill} hands-on project"
            })
            
            day_counter += phase_days
        
        return {
            'summary': f"Master {skill} in {days} days",
            'steps': steps
        }
    
    def _generate_fallback_path(self, skill: str, days: int) -> Dict:
        """Generate a generic learning path when no curated data exists."""
        if days >= 21:
            phase1_days = days // 3
            phase2_days = days // 3
            phase3_days = days - phase1_days - phase2_days
            
            return {
                'summary': f"Master {skill} in {days} days",
                'steps': [
                    {
                        'day_from': 1,
                        'day_to': phase1_days,
                        'title': f"{skill} Fundamentals",
                        'tasks': [f"Learn core {skill} concepts", "Complete tutorials", "Practice exercises"],
                        'project': f"Simple {skill} starter project"
                    },
                    {
                        'day_from': phase1_days + 1,
                        'day_to': phase1_days + phase2_days,
                        'title': f"Intermediate {skill}",
                        'tasks': ["Build practical projects", "Learn advanced features", "Study best practices"],
                        'project': f"{skill} intermediate project"
                    },
                    {
                        'day_from': phase1_days + phase2_days + 1,
                        'day_to': days,
                        'title': f"Advanced {skill}",
                        'tasks': ["Master advanced concepts", "Real-world integration", "Portfolio project"],
                        'project': f"{skill} portfolio project"
                    }
                ]
            }
        else:
            return {
                'summary': f"Learn {skill} in {days} days",
                'steps': [
                    {
                        'day_from': 1,
                        'day_to': days,
                        'title': f"Learn {skill}",
                        'tasks': [f"Study {skill} basics", "Complete tutorials", "Build mini-project"],
                        'project': f"{skill} practice project"
                    }
                ]
            }


# Singleton instance
hf_loader = HFDataLoader()

# Convenience functions (maintain same API as db_data_loader)
def get_all_job_titles():
    return hf_loader.get_all_job_titles()

def find_matching_jobs(query: str, limit: int = 10):
    return hf_loader.find_matching_jobs(query, limit)

def get_required_skills(query: str, limit_jobs: int = 20):
    return hf_loader.get_required_skills(query, limit_jobs)

def get_similar_job_titles(query: str, limit: int = 10):
    return hf_loader.get_similar_job_titles(query, limit)

# New convenience functions for projects and learning paths
def get_projects_for_skills(skills: List[str], limit: int = 5):
    return hf_loader.get_projects_for_skills(skills, limit)

def get_learning_path_for_skill(skill: str, days: int = 7):
    return hf_loader.get_learning_path_for_skill(skill, days)

