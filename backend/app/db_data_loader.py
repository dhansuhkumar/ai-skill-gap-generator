"""
Database Data Loader - Replaces CSV loader with Supabase queries.
Provides the same interface as CSVDataLoader but fetches from database.
"""

import os
from typing import List, Dict, Optional
from collections import Counter
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

class DBDataLoader:
    """Load and query job/skill data from Supabase database."""
    
    _instance = None
    _supabase: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_connection()
        return cls._instance
    
    def _init_connection(self):
        """Initialize Supabase connection."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️  Supabase credentials not configured")
            self._supabase = None
            return
        
        try:
            self._supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Database connection initialized")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            self._supabase = None
    
    def get_all_job_titles(self) -> List[str]:
        """Return all unique job titles."""
        if not self._supabase:
            return []
        
        try:
            result = self._supabase.table('job_postings')\
                .select('job_title')\
                .execute()
            
            # Extract unique titles
            titles = set()
            for row in result.data:
                if row.get('job_title'):
                    titles.add(row['job_title'])
            
            return list(titles)
        except Exception as e:
            print(f"❌ Error fetching job titles: {e}")
            return []
    
    def find_matching_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find jobs matching a query string.
        Uses case-insensitive partial matching.
        """
        if not self._supabase:
            return []
        
        try:
            # Supabase uses ilike for case-insensitive matching
            result = self._supabase.table('job_postings')\
                .select('job_link, job_title, company, job_location, job_level, job_type')\
                .ilike('job_title', f'%{query}%')\
                .limit(limit)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"❌ Error finding matching jobs: {e}")
            return []
    
    def get_job_links_for_titles(self, job_titles: List[str]) -> List[str]:
        """Get job_links for a list of job titles."""
        if not self._supabase or not job_titles:
            return []
        
        try:
            # Query for jobs with matching titles
            result = self._supabase.table('job_postings')\
                .select('job_link')\
                .in_('job_title', job_titles)\
                .execute()
            
            return [row['job_link'] for row in result.data if row.get('job_link')]
        except Exception as e:
            print(f"❌ Error fetching job links: {e}")
            return []
    
    def get_skills_for_job_links(self, job_links: List[str]) -> Dict[str, List[str]]:
        """Get skills mapping for a list of job_links."""
        if not self._supabase or not job_links:
            return {}
        
        try:
            # Query skills for these job links
            result = self._supabase.table('job_skills')\
                .select('job_link, job_skills')\
                .in_('job_link', job_links)\
                .execute()
            
            skills_map = {}
            for row in result.data:
                link = row.get('job_link')
                skills_str = row.get('job_skills', '')
                
                if link and skills_str:
                    # Split skills by comma and clean
                    skills = [s.strip() for s in str(skills_str).split(',') if s.strip()]
                    skills_map[link] = skills
            
            return skills_map
        except Exception as e:
            print(f"❌ Error fetching skills: {e}")
            return {}
    
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
        
        job_titles = [j['job_title'] for j in matched_jobs if j.get('job_title')]
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
        if not self._supabase:
            return None
        
        try:
            result = self._supabase.table('job_postings')\
                .select('*')\
                .eq('job_link', job_link)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"❌ Error fetching job details: {e}")
            return None
    
    def get_similar_job_titles(self, query: str, limit: int = 10) -> List[str]:
        """Get job titles similar to the query (for autocomplete)."""
        if not self._supabase:
            return []
        
        try:
            # Search for titles starting with or containing the query
            result = self._supabase.table('job_postings')\
                .select('job_title')\
                .ilike('job_title', f'%{query}%')\
                .limit(limit * 2)\
                .execute()
            
            # Extract and deduplicate titles
            titles = []
            seen = set()
            
            # Prioritize titles that start with query
            for row in result.data:
                title = row.get('job_title')
                if title and title.lower() not in seen:
                    seen.add(title.lower())
                    if title.lower().startswith(query.lower()):
                        titles.insert(0, title)
                    else:
                        titles.append(title)
            
            return titles[:limit]
        except Exception as e:
            print(f"❌ Error fetching similar titles: {e}")
            return []


# Singleton instance
db_loader = DBDataLoader()

# Convenience functions (maintain same API as csv_data_loader)
def get_all_job_titles():
    return db_loader.get_all_job_titles()

def find_matching_jobs(query: str, limit: int = 10):
    return db_loader.find_matching_jobs(query, limit)

def get_required_skills(query: str, limit_jobs: int = 20):
    return db_loader.get_required_skills(query, limit_jobs)

def get_similar_job_titles(query: str, limit: int = 10):
    return db_loader.get_similar_job_titles(query, limit)
