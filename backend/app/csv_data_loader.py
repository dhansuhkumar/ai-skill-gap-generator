# backend/app/csv_data_loader.py
"""
CSV Data Loader - Loads and queries Kaggle job data CSV files.
Provides deterministic skill gap analysis without AI.
"""

import os
import pandas as pd
import json
from typing import List, Dict, Set, Optional
from collections import Counter

# Base directory for CSV files
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

class CSVDataLoader:
    """Load and query job/skill data from CSV files."""
    
    _instance = None
    _jobs_df = None
    _skills_df = None
    # Removed _summary_df - job_summary.csv is 4.8GB and never used
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_data()
        return cls._instance
    
    def _load_data(self):
        """Load all CSV files into memory."""
        jobs_path = os.path.join(DATA_DIR, 'linkedin_job_postings.csv')
        skills_path = os.path.join(DATA_DIR, 'job_skills.csv')
        # Removed job_summary.csv loading - 4.8GB file that was never used
        
        try:
            self._jobs_df = pd.read_csv(jobs_path)
            print(f"✅ Loaded {len(self._jobs_df)} jobs from linkedin_job_postings.csv")
        except Exception as e:
            print(f"❌ Error loading jobs: {e}")
            self._jobs_df = pd.DataFrame()
        
        try:
            self._skills_df = pd.read_csv(skills_path)
            print(f"✅ Loaded {len(self._skills_df)} job skills from job_skills.csv")
        except Exception as e:
            print(f"❌ Error loading skills: {e}")
            self._skills_df = pd.DataFrame()
        
        print("✅ CSV data loader initialized (job_summary.csv skipped for performance)")
    
    def get_all_job_titles(self) -> List[str]:
        """Return all unique job titles."""
        if self._jobs_df is None or 'job_title' not in self._jobs_df.columns:
            return []
        return self._jobs_df['job_title'].dropna().unique().tolist()
    
    def find_matching_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find jobs matching a query string.
        Uses case-insensitive partial matching.
        """
        if self._jobs_df is None:
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
        if self._jobs_df is None:
            return []
        
        # Create a mask for matching titles
        titles_set = set(t.lower() for t in job_titles)
        mask = self._jobs_df['job_title'].str.lower().apply(
            lambda x: x in titles_set if pd.notna(x) else False
        )
        
        return self._jobs_df[mask]['job_link'].dropna().unique().tolist()
    
    def get_skills_for_job_links(self, job_links: List[str]) -> Dict[str, List[str]]:
        """Get skills mapping for a list of job_links."""
        if self._skills_df is None or not job_links:
            return {}
        
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
        if self._jobs_df is None:
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
csv_loader = CSVDataLoader()

# Convenience functions
def get_all_job_titles():
    return csv_loader.get_all_job_titles()

def find_matching_jobs(query: str, limit: int = 10):
    return csv_loader.find_matching_jobs(query, limit)

def get_required_skills(query: str, limit_jobs: int = 20):
    return csv_loader.get_required_skills(query, limit_jobs)

def get_similar_job_titles(query: str, limit: int = 10):
    return csv_loader.get_similar_job_titles(query, limit)
