"""
Unit tests for GitHub Analyzer - Fresher-Friendly Scoring

Tests verify that:
1. Freshers can reach Intermediate level with repos + tests
2. Stars are optional (no penalty for 0 stars)
3. Diversity bonus applies correctly
4. Score is clamped to 0-100
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.github_analyzer import (
    GitHubAnalyzer,
    LanguageScore,
    analyze_github_profile,
    BASE_SCORE_FOR_REPO,
    TESTS_FOLDER_BONUS,
    DEVOPS_BONUS,
    TYPE_SAFETY_BONUS,
    STARS_BONUS,
    DIVERSITY_BONUS,
    DIVERSITY_THRESHOLD
)


class TestLanguageScoreCalculation:
    """Test the core scoring algorithm."""
    
    def test_single_repo_base_score(self):
        """A single repo gives base score of 30."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO  # 30
    
    def test_multiple_repos_bonus(self):
        """Additional repos add +5 each, max +20."""
        analyzer = GitHubAnalyzer()
        
        # 3 repos = 30 base + (2 * 5) = 40
        lang_data = LanguageScore(repos=3)
        score = analyzer._calculate_language_score(lang_data)
        assert score == 40
        
        # 5 repos = 30 base + (4 * 5) = 50
        lang_data = LanguageScore(repos=5)
        score = analyzer._calculate_language_score(lang_data)
        assert score == 50
        
        # 10 repos = 30 base + max(20) = 50 (capped)
        lang_data = LanguageScore(repos=10)
        score = analyzer._calculate_language_score(lang_data)
        assert score == 50  # Additional repos capped at +20
    
    def test_tests_folder_bonus(self):
        """Tests folder adds +10."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1, has_tests=True)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO + TESTS_FOLDER_BONUS  # 40
    
    def test_devops_bonus(self):
        """Dockerfile or .github/workflows adds +10."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1, has_devops=True)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO + DEVOPS_BONUS  # 40
    
    def test_type_safety_bonus(self):
        """types.ts or py.typed adds +5."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1, has_types=True)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO + TYPE_SAFETY_BONUS  # 35
    
    def test_stars_bonus_small(self):
        """Stars >5 adds only +5 (not +15)."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1, starred_repos=1)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO + STARS_BONUS  # 35
    
    def test_no_stars_no_penalty(self):
        """Zero stars should NOT reduce score - fresher friendly!"""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=1, starred_repos=0)
        score = analyzer._calculate_language_score(lang_data)
        assert score == BASE_SCORE_FOR_REPO  # 30, no penalty
    
    def test_fresher_can_reach_intermediate(self):
        """
        KEY TEST: A fresher with 3 repos and tests should reach Intermediate (>35).
        
        Score = 30 (base) + 10 (2 extra repos) + 10 (tests) = 50
        50 is in Intermediate range (36-65)
        """
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=3, has_tests=True)
        score = analyzer._calculate_language_score(lang_data)
        assert score == 50
        assert score >= 36, "Fresher with 3 repos + tests should be Intermediate"
    
    def test_all_bonuses_combined(self):
        """Test with all quality indicators present."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(
            repos=5,
            has_tests=True,
            has_devops=True,
            has_types=True,
            starred_repos=1
        )
        score = analyzer._calculate_language_score(lang_data)
        # 30 (base) + 20 (4 repos) + 10 (tests) + 10 (devops) + 5 (types) + 5 (stars) = 80
        assert score == 80
    
    def test_score_clamped_to_100(self):
        """Score should never exceed 100."""
        analyzer = GitHubAnalyzer()
        # Extreme case with many repos and all bonuses
        lang_data = LanguageScore(
            repos=20,
            has_tests=True,
            has_devops=True,
            has_types=True,
            starred_repos=5
        )
        score = analyzer._calculate_language_score(lang_data)
        assert score <= 100
    
    def test_zero_repos_zero_score(self):
        """No repos means 0 score."""
        analyzer = GitHubAnalyzer()
        lang_data = LanguageScore(repos=0)
        score = analyzer._calculate_language_score(lang_data)
        assert score == 0


class TestGitHubAPIIntegration:
    """Test API integration with mocked responses."""
    
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repos')
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repo_contents')
    def test_analyze_profile_basic(self, mock_contents, mock_repos):
        """Test basic profile analysis with mocked API."""
        mock_repos.return_value = [
            {
                "name": "my-python-project",
                "language": "Python",
                "stargazers_count": 2,
                "size": 100,
                "fork": False
            }
        ]
        mock_contents.return_value = [
            {"name": "README.md", "path": "README.md"},
            {"name": "tests", "path": "tests"},  # Has tests folder!
        ]
        
        analyzer = GitHubAnalyzer()
        result = analyzer.analyze_profile("student123")
        
        assert result.username == "student123"
        assert result.total_repos == 1
        assert "Python" in result.languages
        assert result.languages["Python"]["has_tests"] is True
    
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repos')
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repo_contents')
    def test_diversity_bonus_applied(self, mock_contents, mock_repos):
        """Test diversity bonus when user has 3+ languages."""
        mock_repos.return_value = [
            {"name": "py-project", "language": "Python", "stargazers_count": 0, "size": 50, "fork": False},
            {"name": "js-project", "language": "JavaScript", "stargazers_count": 0, "size": 50, "fork": False},
            {"name": "go-project", "language": "Go", "stargazers_count": 0, "size": 50, "fork": False},
        ]
        mock_contents.return_value = []
        
        analyzer = GitHubAnalyzer()
        result = analyzer.analyze_profile("diverse_coder")
        
        assert result.diversity_bonus == DIVERSITY_BONUS
        # Each language should have diversity bonus added
        for lang_data in result.languages.values():
            assert lang_data["score"] >= BASE_SCORE_FOR_REPO + DIVERSITY_BONUS
    
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repos')
    def test_empty_profile(self, mock_repos):
        """Test handling of user with no repos."""
        mock_repos.return_value = []
        
        analyzer = GitHubAnalyzer()
        result = analyzer.analyze_profile("newbie")
        
        assert result.error == "No public repositories found"
        assert result.total_repos == 0
    
    @patch('backend.app.github_analyzer.GitHubAnalyzer._fetch_repos')
    def test_forked_repos_ignored(self, mock_repos):
        """Forked repos should not count - we want original work."""
        mock_repos.return_value = [
            {"name": "forked-project", "language": "Python", "fork": True, "stargazers_count": 100, "size": 1000},
        ]
        
        analyzer = GitHubAnalyzer()
        result = analyzer.analyze_profile("fork_only")
        
        # No languages since only forked repos
        assert len(result.languages) == 0


class TestConvenienceFunction:
    """Test the analyze_github_profile convenience function."""
    
    @patch('backend.app.github_analyzer.GitHubAnalyzer.analyze_profile')
    def test_analyze_github_profile_returns_dict(self, mock_analyze):
        """Convenience function should return a dictionary."""
        from backend.app.github_analyzer import GitHubAnalysisResult
        
        mock_analyze.return_value = GitHubAnalysisResult(
            username="test_user",
            languages={"Python": {"repos": 2, "score": 40}},
            total_repos=2,
            diversity_bonus=0
        )
        
        result = analyze_github_profile("test_user")
        
        assert isinstance(result, dict)
        assert result["username"] == "test_user"
        assert "languages" in result
        assert "total_repos" in result
        assert "diversity_bonus" in result
        assert "language_count" in result
