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


class HFDataLoader:
    """Load and query job/skill data from HuggingFace Datasets with local caching."""
    
    _instance = None
    _jobs_df = None
    _skills_df = None
    _initialized = False
    
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
