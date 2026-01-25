"""
Unit tests for Profile Fusion Engine

Tests verify that:
1. Freshers can reach Intermediate level with repos + projects
2. No penalty for being a fresher
3. Experienced users get appropriate bonuses
4. Diversity bonus applies correctly
5. Scores are clamped to 0-100
"""

import pytest
from backend.app.services.fusion_engine import (
    ProfileFusionEngine,
    SkillInput,
    ResumeContext,
    GitHubData,
    fuse_skill_profile,
    BEGINNER_MAX,
    INTERMEDIATE_MAX,
    EXPERIENCED_BONUS,
    PROJECT_BONUS,
    DIVERSITY_BONUS
)


class TestScoreCalculation:
    """Test the core proficiency calculation."""
    
    def test_manual_only_50_percent_weight(self):
        """Manual score alone should contribute 50%."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=100)
        
        result = engine.calculate_proficiency(skill)
        
        # 100 * 0.5 = 50
        assert result.score == 50
    
    def test_github_adds_40_percent(self):
        """GitHub score should add 40% of its value."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        github = GitHubData(language="Python", score=50)
        
        result = engine.calculate_proficiency(skill, github_data=github)
        
        # 50 * 0.5 (manual) + 50 * 0.4 (github) = 25 + 20 = 45
        assert result.score == 45
    
    def test_experienced_bonus_applied(self):
        """Experienced context should add +15 bonus."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        resume = ResumeContext(skill="Python", context="experienced")
        
        result = engine.calculate_proficiency(skill, resume_context=resume)
        
        # 50 * 0.5 + 15 (experienced) = 40
        assert result.score == 40
    
    def test_fresher_no_penalty(self):
        """Fresher context should NOT reduce score."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        resume_neutral = ResumeContext(skill="Python", context="neutral")
        resume_fresher = ResumeContext(skill="Python", context="fresher")
        
        neutral_result = engine.calculate_proficiency(skill, resume_context=resume_neutral)
        fresher_result = engine.calculate_proficiency(skill, resume_context=resume_fresher)
        
        # Fresher should have same score as neutral (no penalty)
        assert fresher_result.score == neutral_result.score
    
    def test_project_bonus_applied(self):
        """Project mentions should add +10 bonus."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        resume = ResumeContext(skill="Python", context="fresher", has_projects=True)
        
        result = engine.calculate_proficiency(skill, resume_context=resume)
        
        # 50 * 0.5 + 10 (projects) = 35
        assert result.score == 35
    
    def test_diversity_bonus_applied(self):
        """Diversity bonus should add +10 when specified."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        
        without_diversity = engine.calculate_proficiency(skill, apply_diversity_bonus=False)
        with_diversity = engine.calculate_proficiency(skill, apply_diversity_bonus=True)
        
        assert with_diversity.score == without_diversity.score + DIVERSITY_BONUS


class TestLevelLabeling:
    """Test score-to-level mapping."""
    
    def test_beginner_level(self):
        """Score 0-35 should be Beginner."""
        engine = ProfileFusionEngine()
        
        assert engine._get_level(0) == "Beginner"
        assert engine._get_level(35) == "Beginner"
    
    def test_intermediate_level(self):
        """Score 36-65 should be Intermediate."""
        engine = ProfileFusionEngine()
        
        assert engine._get_level(36) == "Intermediate"
        assert engine._get_level(65) == "Intermediate"
    
    def test_advanced_level(self):
        """Score 66-100 should be Advanced."""
        engine = ProfileFusionEngine()
        
        assert engine._get_level(66) == "Advanced"
        assert engine._get_level(100) == "Advanced"


class TestFresherFriendlyScenarios:
    """Test that freshers can reach good scores."""
    
    def test_fresher_with_github_and_projects_reaches_intermediate(self):
        """
        KEY TEST: Fresher with repos + projects should reach Intermediate.
        
        Manual: 60 * 0.5 = 30
        GitHub: 50 * 0.4 = 20
        Projects: +10
        Total: 60 -> Intermediate!
        """
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=60)
        resume = ResumeContext(skill="Python", context="fresher", has_projects=True)
        github = GitHubData(language="Python", score=50)
        
        result = engine.calculate_proficiency(
            skill, 
            resume_context=resume, 
            github_data=github
        )
        
        assert result.score >= 36, "Fresher with projects + repos should be Intermediate"
        assert result.level == "Intermediate"
    
    def test_fresher_with_diversity_bonus(self):
        """Fresher knowing 5+ languages gets diversity bonus."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=50)
        github = GitHubData(language="Python", score=50)
        
        result = engine.calculate_proficiency(
            skill,
            github_data=github,
            apply_diversity_bonus=True
        )
        
        # 50*0.5 + 50*0.4 + 10 = 25 + 20 + 10 = 55
        assert result.score == 55
        assert result.level == "Intermediate"
    
    def test_senior_reaches_advanced(self):
        """Senior with good GitHub should reach Advanced."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=80)
        resume = ResumeContext(skill="Python", context="experienced", has_projects=True)
        github = GitHubData(language="Python", score=70)
        
        result = engine.calculate_proficiency(
            skill,
            resume_context=resume,
            github_data=github
        )
        
        # 80*0.5 + 70*0.4 + 15 + 10 = 40 + 28 + 25 = 93
        assert result.score >= 66, "Senior should reach Advanced"
        assert result.level == "Advanced"


class TestScoreClamping:
    """Test that scores are properly clamped."""
    
    def test_score_capped_at_100(self):
        """Score should never exceed 100."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=100)
        resume = ResumeContext(skill="Python", context="experienced", has_projects=True)
        github = GitHubData(language="Python", score=100)
        
        result = engine.calculate_proficiency(
            skill,
            resume_context=resume,
            github_data=github,
            apply_diversity_bonus=True
        )
        
        assert result.score <= 100
    
    def test_score_minimum_zero(self):
        """Score should never go below 0."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Unknown", manual_score=0)
        
        result = engine.calculate_proficiency(skill)
        
        assert result.score >= 0


class TestFuseProfile:
    """Test full profile fusion with multiple skills."""
    
    def test_fuse_multiple_skills(self):
        """Should calculate proficiency for all skills."""
        skills = [
            {"name": "Python", "manual_score": 70},
            {"name": "JavaScript", "manual_score": 60},
            {"name": "React", "manual_score": 50},
        ]
        
        result = fuse_skill_profile(skills)
        
        assert result["skill_count"] == 3
        assert len(result["proficiencies"]) == 3
        assert "average_score" in result
    
    def test_fuse_with_github_data(self):
        """GitHub data should influence scores."""
        skills = [{"name": "Python", "manual_score": 50}]
        github = {
            "languages": {
                "Python": {"score": 60, "repos": 3}
            }
        }
        
        result = fuse_skill_profile(skills, github_analysis=github)
        
        # 50*0.5 + 60*0.4 = 25 + 24 = 49
        assert result["proficiencies"][0]["score"] == 49
    
    def test_diversity_bonus_at_5_languages(self):
        """Diversity bonus when 5+ languages in GitHub."""
        skills = [{"name": "Python", "manual_score": 50}]
        github = {
            "languages": {
                "Python": {"score": 30},
                "JavaScript": {"score": 30},
                "Go": {"score": 30},
                "Rust": {"score": 30},
                "TypeScript": {"score": 30},
            }
        }
        
        result = fuse_skill_profile(skills, github_analysis=github)
        
        assert result["diversity_bonus_applied"] is True
    
    def test_javascript_aliases_work(self):
        """React skill should match JavaScript GitHub data."""
        skills = [{"name": "React", "manual_score": 50}]
        github = {
            "languages": {
                "JavaScript": {"score": 60, "repos": 3}
            }
        }
        
        result = fuse_skill_profile(skills, github_analysis=github)
        
        # React should use JavaScript GitHub data
        assert result["proficiencies"][0]["score"] > 25  # More than just manual


class TestBreakdown:
    """Test that score breakdown is provided."""
    
    def test_breakdown_included(self):
        """Result should include calculation breakdown."""
        engine = ProfileFusionEngine()
        skill = SkillInput(name="Python", manual_score=60)
        
        result = engine.calculate_proficiency(skill)
        
        assert "breakdown" in result.__dict__
        assert "manual_input" in result.breakdown
        assert "github_boost" in result.breakdown
