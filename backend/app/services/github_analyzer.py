"""
GitHub Profile Analyzer Service

Analyzes a user's GitHub repositories to calculate proficiency scores
for each programming language based on code volume and recency.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GithubProfileAnalyzer:
    """Analyzes GitHub profiles to extract language proficiency scores."""
    
    BASE_URL = "https://api.github.com"
    RECENCY_THRESHOLD_MONTHS = 3
    RECENCY_MULTIPLIER = 1.2
    NORMALIZATION_THRESHOLD_BYTES = 1_000_000  # 1MB = 100 points
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits
        """
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def analyze_profile(self, username: str) -> Dict:
        """
        Analyze a GitHub user's profile for language proficiency.
        
        Args:
            username: GitHub username
            
        Returns:
            Dict with 'skills' (language scores) and 'chart_data' (recharts format)
        """
        try:
            # Fetch user's repositories
            repos = self._fetch_user_repos(username)
            
            if not repos:
                return {
                    "error": "No repositories found",
                    "skills": {},
                    "chart_data": []
                }
            
            # Get top 10 most recently pushed repos
            top_repos = sorted(
                repos,
                key=lambda r: r.get('pushed_at', ''),
                reverse=True
            )[:10]
            
            # Aggregate language stats
            language_bytes = self._aggregate_language_stats(username, top_repos)
            
            # Calculate proficiency scores
            skills = self._calculate_proficiency_scores(language_bytes, top_repos)
            
            # Format for recharts
            chart_data = self._format_for_recharts(skills)
            
            return {
                "skills": skills,
                "chart_data": chart_data,
                "repos_analyzed": len(top_repos)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                return {
                    "error": "GitHub API rate limit exceeded. Please try again later.",
                    "skills": {},
                    "chart_data": []
                }
            return {
                "error": f"Failed to fetch GitHub data: {str(e)}",
                "skills": {},
                "chart_data": []
            }
        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "skills": {},
                "chart_data": []
            }
    
    def _fetch_user_repos(self, username: str) -> List[Dict]:
        """Fetch all repositories for a user with pagination."""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.BASE_URL}/users/{username}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'pushed',
                'direction': 'desc'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend(page_repos)
            
            # Limit to 100 repos total to avoid excessive API calls
            if len(repos) >= 100 or len(page_repos) < per_page:
                break
                
            page += 1
        
        return repos
    
    def _aggregate_language_stats(self, username: str, repos: List[Dict]) -> Dict[str, int]:
        """Fetch and aggregate language statistics across repositories."""
        language_bytes = {}
        
        for repo in repos:
            try:
                # Fetch language stats for this repo
                url = f"{self.BASE_URL}/repos/{username}/{repo['name']}/languages"
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                languages = response.json()
                
                # Aggregate bytes per language
                for lang, bytes_count in languages.items():
                    language_bytes[lang] = language_bytes.get(lang, 0) + bytes_count
                    
            except Exception as e:
                logger.warning(f"Failed to fetch languages for {repo['name']}: {e}")
                continue
        
        return language_bytes
    
    def _calculate_proficiency_scores(
        self, 
        language_bytes: Dict[str, int],
        repos: List[Dict]
    ) -> Dict[str, int]:
        """
        Calculate proficiency scores with recency multiplier.
        
        Args:
            language_bytes: Raw byte counts per language
            repos: Repository data for recency calculation
            
        Returns:
            Dict mapping language names to scores (0-100)
        """
        if not language_bytes:
            return {}
        
        # Calculate recency multiplier
        now = datetime.utcnow()
        recent_threshold = now - timedelta(days=self.RECENCY_THRESHOLD_MONTHS * 30)
        
        # Check if any repos are recent
        has_recent_activity = any(
            datetime.strptime(repo.get('pushed_at', '1970-01-01T00:00:00Z'), '%Y-%m-%dT%H:%M:%SZ') > recent_threshold
            for repo in repos
        )
        
        # Apply recency multiplier to all languages if there's recent activity
        multiplier = self.RECENCY_MULTIPLIER if has_recent_activity else 1.0
        
        # Calculate scores
        scores = {}
        for lang, bytes_count in language_bytes.items():
            # Apply multiplier
            adjusted_bytes = bytes_count * multiplier
            
            # Normalize to 0-100 scale
            score = min(100, int((adjusted_bytes / self.NORMALIZATION_THRESHOLD_BYTES) * 100))
            scores[lang] = score
        
        return scores
    
    def _format_for_recharts(self, skills: Dict[str, int]) -> List[Dict]:
        """
        Format skills data for Recharts RadarChart.
        
        Args:
            skills: Dict mapping language names to scores
            
        Returns:
            List of dicts with 'subject', 'A', and 'fullMark' keys
        """
        # Sort by score descending and take top 8 for readability
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:8]
        
        return [
            {
                "subject": lang,
                "A": score,
                "fullMark": 100
            }
            for lang, score in sorted_skills
        ]
