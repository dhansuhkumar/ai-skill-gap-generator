"""
Profile Fusion Engine - Fresher-Friendly Skill Triangulation

Calculates 0-100 proficiency scores by fusing data from:
1. Manual Input (user's self-assessment)
2. GitHub Analysis (code proof - repo count, quality signals)
3. Resume Context (experience level, project mentions)

The formula is designed to be fair to freshers:
- No penalty for being new to coding
- Rewards coding activity and projects
- GitHub weighs heavily for freshers (40%)
- Experience bonus for seniors, but not required
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Score thresholds for level labels
BEGINNER_MAX = 35
INTERMEDIATE_MAX = 65

# Weight factors
MANUAL_WEIGHT = 0.5  # 50% weight for self-assessment
GITHUB_WEIGHT = 0.4  # 40% weight for GitHub proof

# Bonuses
EXPERIENCED_BONUS = 15
PROJECT_BONUS = 10
DIVERSITY_BONUS = 10


@dataclass
class SkillInput:
    """Input data for a single skill."""
    name: str
    manual_score: int = 50  # User's self-assessment (0-100)


@dataclass
class ResumeContext:
    """Context extracted from resume for a skill."""
    skill: str
    context: str = "neutral"  # "experienced", "fresher", or "neutral"
    has_projects: bool = False
    estimated_years: Optional[int] = None


@dataclass
class GitHubData:
    """GitHub analysis data for a skill/language."""
    language: str
    score: int = 0
    repos: int = 0
    has_tests: bool = False
    has_devops: bool = False


@dataclass
class SkillProficiency:
    """Output proficiency for a skill."""
    skill: str
    score: int
    level: str  # "Beginner", "Intermediate", "Advanced"
    breakdown: dict = field(default_factory=dict)


class ProfileFusionEngine:
    """
    Calculates skill proficiency scores using a weighted fusion algorithm.
    
    Formula (fresher-friendly):
    1. BASE = manual_input * 0.5 (50% weight for self-assessment)
    2. GITHUB_BOOST = github_score * 0.4 (40% weight for code proof)
    3. RESUME_BONUS:
       - If "experienced": +15
       - If "fresher": +0 (no penalty!)
       - If has_projects: +10
    4. DIVERSITY_BONUS (if 5+ languages known): +10
    5. FINAL = clamp(BASE + GITHUB_BOOST + RESUME_BONUS + DIVERSITY_BONUS, 0, 100)
    
    Labeling:
    - 0-35: Beginner
    - 36-65: Intermediate
    - 66-100: Advanced
    """
    
    def __init__(self):
        self.diversity_bonus_applied = False
    
    def calculate_proficiency(
        self,
        skill: SkillInput,
        resume_context: Optional[ResumeContext] = None,
        github_data: Optional[GitHubData] = None,
        apply_diversity_bonus: bool = False
    ) -> SkillProficiency:
        """
        Calculate proficiency score for a single skill.
        
        Args:
            skill: User's self-assessment and skill name
            resume_context: Optional context from resume parser
            github_data: Optional GitHub analysis data
            apply_diversity_bonus: Whether to add diversity bonus (+10)
            
        Returns:
            SkillProficiency with score, level, and breakdown
        """
        breakdown = {}
        
        # 1. BASE from manual input (50% weight)
        base_score = skill.manual_score * MANUAL_WEIGHT
        breakdown["manual_input"] = f"{skill.manual_score} * {MANUAL_WEIGHT} = {base_score:.0f}"
        
        # 2. GITHUB BOOST (40% weight)
        github_boost = 0
        if github_data and github_data.score > 0:
            github_boost = github_data.score * GITHUB_WEIGHT
            breakdown["github_boost"] = f"{github_data.score} * {GITHUB_WEIGHT} = {github_boost:.0f}"
        else:
            breakdown["github_boost"] = "0 (no GitHub data)"
        
        # 3. RESUME BONUS
        resume_bonus = 0
        if resume_context:
            # Experience bonus (only for experienced, NO penalty for freshers)
            if resume_context.context == "experienced":
                resume_bonus += EXPERIENCED_BONUS
                breakdown["experience_bonus"] = f"+{EXPERIENCED_BONUS} (experienced)"
            elif resume_context.context == "fresher":
                breakdown["experience_bonus"] = "+0 (fresher - no penalty)"
            else:
                breakdown["experience_bonus"] = "+0 (neutral)"
            
            # Project bonus
            if resume_context.has_projects:
                resume_bonus += PROJECT_BONUS
                breakdown["project_bonus"] = f"+{PROJECT_BONUS} (has projects)"
            else:
                breakdown["project_bonus"] = "+0 (no projects mentioned)"
        else:
            breakdown["resume_context"] = "not provided"
        
        # 4. DIVERSITY BONUS
        diversity_bonus = DIVERSITY_BONUS if apply_diversity_bonus else 0
        if apply_diversity_bonus:
            breakdown["diversity_bonus"] = f"+{DIVERSITY_BONUS} (5+ languages)"
        
        # 5. FINAL SCORE
        raw_score = base_score + github_boost + resume_bonus + diversity_bonus
        final_score = int(max(0, min(100, raw_score)))
        
        breakdown["raw_total"] = f"{base_score:.0f} + {github_boost:.0f} + {resume_bonus} + {diversity_bonus} = {raw_score:.0f}"
        breakdown["final_clamped"] = final_score
        
        # Determine level
        level = self._get_level(final_score)
        
        return SkillProficiency(
            skill=skill.name,
            score=final_score,
            level=level,
            breakdown=breakdown
        )
    
    def fuse_profile(
        self,
        skills: list[SkillInput],
        resume_data: Optional[dict] = None,
        github_analysis: Optional[dict] = None
    ) -> dict:
        """
        Fuse all data sources to calculate proficiencies for multiple skills.
        
        Args:
            skills: List of skills with manual scores
            resume_data: Output from extract_skills_with_context()
            github_analysis: Output from analyze_github_profile()
            
        Returns:
            {
                "proficiencies": [
                    {"skill": "Python", "score": 65, "level": "Intermediate", ...},
                    ...
                ],
                "average_score": 55,
                "skill_count": 5
            }
        """
        proficiencies = []
        
        # Build lookup maps
        resume_skills_map = {}
        if resume_data:
            for skill_ctx in resume_data.get("skills", []):
                name = skill_ctx.get("skill", "").lower()
                resume_skills_map[name] = ResumeContext(
                    skill=skill_ctx.get("skill", ""),
                    context=skill_ctx.get("context", resume_data.get("global_context", "neutral")),
                    has_projects=skill_ctx.get("has_projects", resume_data.get("has_projects", False)),
                    estimated_years=resume_data.get("estimated_years")
                )
        
        github_langs_map = {}
        if github_analysis:
            for lang, data in github_analysis.get("languages", {}).items():
                github_langs_map[lang.lower()] = GitHubData(
                    language=lang,
                    score=data.get("score", 0),
                    repos=data.get("repos", 0),
                    has_tests=data.get("has_tests", False),
                    has_devops=data.get("has_devops", False)
                )
        
        # Check for diversity bonus (5+ languages in GitHub)
        apply_diversity = len(github_langs_map) >= 5
        
        # Calculate proficiency for each skill
        for skill in skills:
            skill_lower = skill.name.lower()
            
            # Find matching resume context
            resume_ctx = resume_skills_map.get(skill_lower)
            if not resume_ctx and resume_data:
                # Use global context if skill-specific not found
                resume_ctx = ResumeContext(
                    skill=skill.name,
                    context=resume_data.get("global_context", "neutral"),
                    has_projects=resume_data.get("has_projects", False),
                    estimated_years=resume_data.get("estimated_years")
                )
            
            # Find matching GitHub data (need to match language names)
            github_data = github_langs_map.get(skill_lower)
            # Also try common aliases
            if not github_data:
                aliases = {
                    "javascript": ["js", "javascript"],
                    "typescript": ["ts", "typescript"],
                    "python": ["python", "py"],
                    "react": ["javascript", "typescript"],  # React uses JS/TS
                    "node.js": ["javascript"],
                    "node": ["javascript"],
                }
                for alias in aliases.get(skill_lower, []):
                    if alias in github_langs_map:
                        github_data = github_langs_map[alias]
                        break
            
            proficiency = self.calculate_proficiency(
                skill=skill,
                resume_context=resume_ctx,
                github_data=github_data,
                apply_diversity_bonus=apply_diversity
            )
            
            proficiencies.append({
                "skill": proficiency.skill,
                "score": proficiency.score,
                "level": proficiency.level,
                "breakdown": proficiency.breakdown
            })
        
        # Calculate averages
        total_score = sum(p["score"] for p in proficiencies)
        avg_score = total_score // len(proficiencies) if proficiencies else 0
        
        return {
            "proficiencies": proficiencies,
            "average_score": avg_score,
            "skill_count": len(proficiencies),
            "diversity_bonus_applied": apply_diversity
        }
    
    def _get_level(self, score: int) -> str:
        """Determine level label from score."""
        if score <= BEGINNER_MAX:
            return "Beginner"
        elif score <= INTERMEDIATE_MAX:
            return "Intermediate"
        else:
            return "Advanced"


def fuse_skill_profile(
    skills: list[dict],
    resume_data: Optional[dict] = None,
    github_analysis: Optional[dict] = None
) -> dict:
    """
    Convenience function to fuse skill profiles.
    
    Args:
        skills: List of {"name": "Python", "manual_score": 70}
        resume_data: Output from extract_skills_with_context()
        github_analysis: Output from analyze_github_profile()
        
    Returns:
        Fused proficiency data
    """
    engine = ProfileFusionEngine()
    
    skill_inputs = [
        SkillInput(name=s["name"], manual_score=s.get("manual_score", 50))
        for s in skills
    ]
    
    return engine.fuse_profile(
        skills=skill_inputs,
        resume_data=resume_data,
        github_analysis=github_analysis
    )
