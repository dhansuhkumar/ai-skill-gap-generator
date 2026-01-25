"""
Unit tests for Resume Parser Context Detection

Tests verify that:
1. Senior/Lead keywords are detected as "experienced"
2. Student/Intern keywords are detected as "fresher"
3. Date ranges are correctly parsed for years of experience
4. Project mentions are detected
"""

import pytest
from backend.app.resume_parser import (
    _detect_context,
    _extract_years_of_experience,
    _has_project_mentions,
    _get_skill_context_window,
    SENIOR_KEYWORDS,
    FRESHER_KEYWORDS
)


class TestContextDetection:
    """Test seniority/fresher detection."""
    
    def test_senior_keywords_detected(self):
        """Senior/Lead keywords should return 'experienced'."""
        test_cases = [
            "Senior Python Developer with 5+ years experience",
            "Tech Lead at Google working on ML systems",
            "Principal Engineer at Amazon",
            "Software Architect designing distributed systems",
            "Staff Engineer at Meta",
        ]
        for text in test_cases:
            assert _detect_context(text) == "experienced", f"Failed for: {text}"
    
    def test_fresher_keywords_detected(self):
        """Student/Intern keywords should return 'fresher'."""
        test_cases = [
            "Computer Science Student at MIT",
            "Python Intern at startup",
            "Recent Bootcamp Graduate seeking first role",
            "B.Tech in Computer Science, 2024",
            "Junior Developer looking for opportunities",
            "Fresher with strong Python skills",
        ]
        for text in test_cases:
            assert _detect_context(text) == "fresher", f"Failed for: {text}"
    
    def test_neutral_when_no_keywords(self):
        """No special keywords should return 'neutral'."""
        text = "Python Developer with React experience"
        assert _detect_context(text) == "neutral"
    
    def test_neutral_when_both_keywords(self):
        """Both senior AND fresher keywords should return 'neutral'."""
        text = "Senior Developer looking for Junior team members, also teaching students"
        assert _detect_context(text) == "neutral"
    
    def test_case_insensitive(self):
        """Detection should be case insensitive."""
        assert _detect_context("SENIOR DEVELOPER") == "experienced"
        assert _detect_context("STUDENT INTERN") == "fresher"


class TestYearsOfExperience:
    """Test date range extraction."""
    
    def test_year_range_with_present(self):
        """'2021 - Present' should calculate years correctly."""
        text = "Python Developer 2021 - Present"
        years = _extract_years_of_experience(text)
        # Should be at least 3 years (2021 to 2026)
        assert years is not None
        assert years >= 3
    
    def test_year_range_explicit(self):
        """'2020 - 2023' should return 3 years."""
        text = "Worked at Company X from 2020 - 2023"
        years = _extract_years_of_experience(text)
        assert years == 3
    
    def test_month_year_range(self):
        """'Jan 2020 - Dec 2022' should work."""
        text = "Software Engineer Jan 2020 - Dec 2022"
        years = _extract_years_of_experience(text)
        assert years == 2
    
    def test_no_dates_returns_none(self):
        """Text without date ranges should return None."""
        text = "Experienced Python developer with strong skills"
        years = _extract_years_of_experience(text)
        assert years is None
    
    def test_multiple_ranges_returns_max(self):
        """Multiple date ranges should return the maximum."""
        text = """
        Python Developer 2018 - 2020
        Senior Developer 2020 - Present
        """
        years = _extract_years_of_experience(text)
        # Should return the longer duration
        assert years is not None
        assert years >= 2


class TestProjectMentions:
    """Test project detection."""
    
    def test_project_keyword_detected(self):
        """Project-related keywords should be detected."""
        test_cases = [
            "Built a web application using React",
            "Developed a Python API for data processing",
            "Created a portfolio website",
            "Deployed services on AWS",
            "GitHub: github.com/user/repo",
        ]
        for text in test_cases:
            assert _has_project_mentions(text) is True, f"Failed for: {text}"
    
    def test_no_project_keywords(self):
        """Text without project keywords should return False."""
        text = "Proficient in Python and JavaScript"
        assert _has_project_mentions(text) is False


class TestSkillContextWindow:
    """Test context window extraction."""
    
    def test_extracts_surrounding_text(self):
        """Should extract text around the skill mention."""
        text = "As a Senior Python Developer, I built many applications using React and Node.js"
        window = _get_skill_context_window(text, "Python", window_size=50)
        
        assert "Python" in window
        assert "Senior" in window  # Should include context before
    
    def test_skill_not_found_returns_empty(self):
        """If skill not in text, return empty string."""
        text = "JavaScript developer with React experience"
        window = _get_skill_context_window(text, "Python")
        assert window == ""
    
    def test_handles_skill_at_start(self):
        """Should handle skill at beginning of text."""
        text = "Python is my primary language for backend development"
        window = _get_skill_context_window(text, "Python", window_size=20)
        assert "Python" in window


class TestFresherFriendlyScenarios:
    """Test scenarios that should be fair to freshers."""
    
    def test_fresher_with_projects_is_positive(self):
        """A fresher mentioning projects should have has_projects=True."""
        text = """
        B.Tech Computer Science Student
        Developed a full-stack web application using React and Node.js
        Built a Python API for my portfolio project
        """
        assert _detect_context(text) == "fresher"
        assert _has_project_mentions(text) is True
    
    def test_bootcamp_graduate_detected_as_fresher(self):
        """Bootcamp graduates should be detected as freshers (no penalty)."""
        text = "Full Stack Bootcamp Graduate with portfolio projects"
        assert _detect_context(text) == "fresher"
        assert _has_project_mentions(text) is True
