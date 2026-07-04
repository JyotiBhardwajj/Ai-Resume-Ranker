import logging
from typing import Dict, List, Any

from backend.models.candidate import Candidate
from backend.services.career_trajectory import CareerTrajectoryScorer
from backend.services.skill_score import SkillScorer
from backend.services.experience_score import ExperienceScorer

logger = logging.getLogger(__name__)


class HiddenGemDetector:
    """
    Detector service to identify overlooked high-potential candidates (Hidden Gems)
    who have strong skills and growth but might suffer from tier/bias filters.
    """

    @classmethod
    def detect(cls, candidate: Candidate, jd_text: str, ranking_score: float) -> Dict[str, Any]:
        """
        Detects if a candidate is a hidden gem based on bias factors and potential indicators.

        Args:
            candidate: Validated Candidate model instance.
            jd_text: The Job Description text.
            ranking_score: Stated final ranking score from the ranking engine.

        Returns:
            Dictionary containing is_hidden_gem (bool), confidence (float), and reasons (list of str).
        """
        reasons: List[str] = []
        bias_factors = 0
        potential_indicators = 0

        # --- 1. Evaluate Bias / Overlooked Factors ---
        
        # A. College Bias (No Tier 1 or Tier 2 education)
        has_elite_education = False
        non_cs_major = False
        for edu in candidate.education:
            if edu.tier in ["tier_1", "tier_2"]:
                has_elite_education = True
            
            major_lower = edu.field_of_study.lower()
            if not any(kw in major_lower for kw in ["computer", "software", "information", "data science", "engineering", "math"]):
                non_cs_major = True
                
        if not has_elite_education and len(candidate.education) > 0:
            bias_factors += 1
            reasons.append("Non-target university background (no Tier 1/2 college listing)")
        if non_cs_major:
            bias_factors += 1
            reasons.append("Non-traditional educational major (non-CS background)")

        # B. Company Size Bias (Only worked at small/medium companies)
        worked_at_large_corp = False
        for role in candidate.career_history:
            if role.company_size in ["5001-10000", "10001+"]:
                worked_at_large_corp = True
                break
        if not worked_at_large_corp and len(candidate.career_history) > 0:
            bias_factors += 1
            reasons.append("Small/medium company background (no major corporate brand names)")

        # --- 2. Evaluate High Potential / Strength Factors ---
        
        # A. High Career Growth
        trajectory_report = CareerTrajectoryScorer.calculate_score(candidate)
        cts = trajectory_report["career_trajectory_score"]
        if cts >= 65:
            potential_indicators += 1
            reasons.append(f"Exceptional career velocity (Career Trajectory Score: {cts}/100)")

        # B. Strong Tech/Skill Alignment
        skill_report = SkillScorer.calculate_match(candidate)
        skill_score_val = skill_report["score"]
        if skill_score_val >= 60.0:
            potential_indicators += 1
            reasons.append(f"Strong technical skill alignment (Skill Match: {skill_score_val}%)")

        # C. High Ranking Score
        if ranking_score >= 65.0:
            potential_indicators += 1
            reasons.append(f"High semantic role fit (Final Ranking Score: {ranking_score}%)")

        # D. Open Source footprint
        signals = candidate.redrob_signals
        if signals.github_activity_score >= 40.0:
            potential_indicators += 1
            reasons.append(f"Active open-source contributor (GitHub Score: {signals.github_activity_score})")

        # E. Core experience score
        exp_score = ExperienceScorer.calculate_score(candidate)
        if exp_score >= 80.0:
            potential_indicators += 1
            reasons.append(f"Solid relevant experience depth (Experience Score: {exp_score}%)")

        # --- 3. Decision Logic ---
        # A candidate is a hidden gem if they have at least one bias factor and at least 2 potential indicators.
        is_hidden_gem = bias_factors >= 1 and potential_indicators >= 2

        confidence = 0.0
        if is_hidden_gem:
            # Calculate confidence score based on metrics
            base = 0.60
            # Extra weight for high scores
            extra_potential = max(0, potential_indicators - 2) * 0.10
            extra_bias = max(0, bias_factors - 1) * 0.05
            
            score_factor = (ranking_score / 100.0) * 0.15
            confidence = min(0.98, round(base + extra_potential + extra_bias + score_factor, 2))
        else:
            reasons = []

        return {
            "is_hidden_gem": is_hidden_gem,
            "confidence": confidence,
            "reasons": reasons
        }
