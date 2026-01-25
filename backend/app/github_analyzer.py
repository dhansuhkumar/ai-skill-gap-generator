"""
GitHub Analyzer - Fresher-Friendly Complexity Scoring

Analyzes GitHub repositories to calculate skill proficiency scores
that reward coding activity and diversity, not just stars/experience.

Scoring Model (0-100 per language):
- +30 base for having ≥1 repo in language
- +5 per additional repo (max +20)
- +10 for tests/ folder
- +10 for Dockerfile or .github/workflows
- +5 for types.ts or py.typed
- +5 for repo stars > 5 (small bonus)
- +10 global diversity bonus for 3+ languages
"""

import logging
import requests
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# Scoring constants
BASE_SCORE_FOR_REPO = 30
ADDITIONAL_REPO_BONUS = 5
MAX_ADDITIONAL_REPO_BONUS = 20
TESTS_FOLDER_BONUS = 10
DEVOPS_BONUS = 10  # Dockerfile or .github/workflows
TYPE_SAFETY_BONUS = 5  # types.ts or py.typed
STARS_BONUS = 5  # Only if > 5 stars
DIVERSITY_BONUS = 10  # If 3+ languages
DIVERSITY_THRESHOLD = 3


@dataclass
class RepoAnalysis:
    """Analysis result for a single repository."""
    name: str
    language: str
    stars: int = 0
    has_tests: bool = False
    has_devops: bool = False
    has_types: bool = False
    bonus_points: int = 0


@dataclass
class LanguageScore:
    """Score for a programming language/skill."""
    repos: int = 0
    total_bytes: int = 0
    score: int = 0
    has_tests: bool = False
    has_devops: bool = False
    has_types: bool = False
    starred_repos: int = 0


@dataclass
class GitHubAnalysisResult:
    """Complete analysis result for a GitHub profile."""
    username: str
    languages: dict = field(default_factory=dict)  # {lang: LanguageScore}
    total_repos: int = 0
    diversity_bonus: int = 0
    error: Optional[str] = None


class GitHubAnalyzer:
    """
    Analyzes GitHub profiles to calculate fresher-friendly skill scores.
    
    Rewards:
    - Having code (repos)
    - Code quality signals (tests, CI/CD, types)
    - Language diversity
    
    Does NOT heavily penalize:
    - Low/no stars
    - Being new to coding
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits.
                         Anonymous API allows 60 requests/hour; authenticated allows 5000/hour.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkillGapAnalyzer/1.0"
        })
        if github_token:
            self.session.headers["Authorization"] = f"token {github_token}"
    
    def analyze_profile(self, username: str) -> GitHubAnalysisResult:
        """
        Analyze a GitHub user's profile and calculate skill scores.
        
        Args:
            username: GitHub username to analyze
            
        Returns:
            GitHubAnalysisResult with language scores and bonuses
        """
        result = GitHubAnalysisResult(username=username)
        
        try:
            # Fetch user's public repos
            repos = self._fetch_repos(username)
            if not repos:
                result.error = "No public repositories found"
                return result
            
            result.total_repos = len(repos)
            
            # Analyze each repo and aggregate by language
            language_data: dict[str, LanguageScore] = {}
            
            for repo in repos:
                repo_analysis = self._analyze_repo(username, repo)
                if not repo_analysis or not repo_analysis.language:
                    continue
                
                lang = repo_analysis.language
                if lang not in language_data:
                    language_data[lang] = LanguageScore()
                
                ld = language_data[lang]
                ld.repos += 1
                ld.total_bytes += repo.get("size", 0) * 1024  # size is in KB
                
                if repo_analysis.has_tests:
                    ld.has_tests = True
                if repo_analysis.has_devops:
                    ld.has_devops = True
                if repo_analysis.has_types:
                    ld.has_types = True
                if repo_analysis.stars > 5:
                    ld.starred_repos += 1
            
            # Calculate scores for each language
            for lang, ld in language_data.items():
                ld.score = self._calculate_language_score(ld)
            
            result.languages = {
                lang: {
                    "repos": ld.repos,
                    "bytes": ld.total_bytes,
                    "score": ld.score,
                    "has_tests": ld.has_tests,
                    "has_devops": ld.has_devops,
                    "has_types": ld.has_types,
                    "starred_repos": ld.starred_repos
                }
                for lang, ld in language_data.items()
            }
            
            # Apply diversity bonus if 3+ languages
            if len(language_data) >= DIVERSITY_THRESHOLD:
                result.diversity_bonus = DIVERSITY_BONUS
                # Add diversity bonus to all language scores
                for lang_data in result.languages.values():
                    lang_data["score"] = min(100, lang_data["score"] + DIVERSITY_BONUS)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error for {username}: {e}")
            result.error = f"GitHub API error: {str(e)}"
            return result
        except Exception as e:
            logger.error(f"Error analyzing GitHub profile {username}: {e}")
            result.error = f"Analysis error: {str(e)}"
            return result
    
    def _fetch_repos(self, username: str, per_page: int = 100) -> list:
        """Fetch public repositories for a user."""
        url = f"{GITHUB_API_BASE}/users/{username}/repos"
        params = {
            "type": "owner",
            "sort": "updated",
            "per_page": per_page
        }
        
        response = self.session.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            logger.warning(f"GitHub user not found: {username}")
            return []
        
        response.raise_for_status()
        return response.json()
    
    def _analyze_repo(self, username: str, repo: dict) -> Optional[RepoAnalysis]:
        """
        Analyze a single repository for complexity indicators.
        
        Checks for:
        - tests/ folder
        - Dockerfile or .github/workflows
        - types.ts or py.typed
        """
        if repo.get("fork"):
            # Skip forked repos - we want original work
            return None
        
        name = repo.get("name", "")
        language = repo.get("language")
        stars = repo.get("stargazers_count", 0)
        
        if not language:
            return None
        
        analysis = RepoAnalysis(
            name=name,
            language=language,
            stars=stars
        )
        
        # Check repo contents for complexity indicators
        # Using the contents API to check for specific files/folders
        try:
            contents = self._fetch_repo_contents(username, name)
            content_names = {item.get("name", "").lower() for item in contents}
            content_paths = {item.get("path", "").lower() for item in contents}
            
            # Check for tests folder
            if "tests" in content_names or "test" in content_names or "__tests__" in content_names:
                analysis.has_tests = True
            
            # Check for DevOps files
            if "dockerfile" in content_names or ".github" in content_names:
                analysis.has_devops = True
            
            # Check for type safety files
            if "types.ts" in content_names or "py.typed" in content_names:
                analysis.has_types = True
            
            # Calculate bonus points
            if analysis.has_tests:
                analysis.bonus_points += TESTS_FOLDER_BONUS
            if analysis.has_devops:
                analysis.bonus_points += DEVOPS_BONUS
            if analysis.has_types:
                analysis.bonus_points += TYPE_SAFETY_BONUS
            if analysis.stars > 5:
                analysis.bonus_points += STARS_BONUS
                
        except Exception as e:
            # If we can't fetch contents, just use basic repo info
            logger.debug(f"Could not fetch contents for {username}/{name}: {e}")
        
        return analysis
    
    def _fetch_repo_contents(self, username: str, repo_name: str) -> list:
        """Fetch root directory contents of a repository."""
        url = f"{GITHUB_API_BASE}/repos/{username}/{repo_name}/contents"
        
        response = self.session.get(url, timeout=10)
        if response.status_code != 200:
            return []
        
        return response.json()
    
    def _calculate_language_score(self, lang_data: LanguageScore) -> int:
        """
        Calculate the fresher-friendly score for a language.
        
        Formula:
        - Base: 30 points for having at least 1 repo
        - +5 per additional repo (max +20)
        - +10 for tests
        - +10 for devops
        - +5 for types
        - +5 for starred repos
        """
        if lang_data.repos == 0:
            return 0
        
        score = BASE_SCORE_FOR_REPO
        
        # Additional repo bonus (max 20)
        additional_repos = lang_data.repos - 1
        repo_bonus = min(additional_repos * ADDITIONAL_REPO_BONUS, MAX_ADDITIONAL_REPO_BONUS)
        score += repo_bonus
        
        # Quality bonuses
        if lang_data.has_tests:
            score += TESTS_FOLDER_BONUS
        if lang_data.has_devops:
            score += DEVOPS_BONUS
        if lang_data.has_types:
            score += TYPE_SAFETY_BONUS
        if lang_data.starred_repos > 0:
            score += STARS_BONUS
        
        # Clamp to 0-100
        return min(max(score, 0), 100)


def analyze_github_profile(username: str, github_token: Optional[str] = None) -> dict:
    """
    Convenience function to analyze a GitHub profile.
    
    Args:
        username: GitHub username
        github_token: Optional auth token for higher rate limits
        
    Returns:
        Dictionary with analysis results
    """
    analyzer = GitHubAnalyzer(github_token)
    result = analyzer.analyze_profile(username)
    
    return {
        "username": result.username,
        "languages": result.languages,
        "total_repos": result.total_repos,
        "diversity_bonus": result.diversity_bonus,
        "language_count": len(result.languages),
        "error": result.error
    }
