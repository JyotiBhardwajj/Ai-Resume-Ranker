import logging
from typing import Dict, List, Any

from backend.models.candidate import Candidate
from backend.services.career_trajectory import CareerTrajectoryScorer

logger = logging.getLogger(__name__)


class PotentialScorer:
    """
    Scorer service to compute a Potential Score (0 to 100) evaluating a candidate's
    capacity for future growth, adaptability, skill diversity, and leadership velocity.
    """

    @classmethod
    def calculate_potential(cls, candidate: Candidate) -> Dict[str, Any]:
        """
        Calculates the potential score, confidence, strengths, and growth indicators.

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            Dictionary containing potential_score, confidence, strengths, and growth_indicators.
        """
        strengths: List[str] = []
        growth_indicators: List[str] = []

        # 1. Skill Diversity (Weight: 15%)
        # Base score on quantity of skills
        num_skills = len(candidate.skills)
        if num_skills >= 10:
            s_diversity = 100.0
            strengths.append(f"Highly diverse technical skill set ({num_skills} distinct skills)")
        elif num_skills >= 5:
            s_diversity = 80.0
            strengths.append("Broad foundation of core technical competencies")
        else:
            s_diversity = (num_skills / 5.0) * 100.0
            growth_indicators.append("Opportunity to expand technical skill breadth")

        # 2. Learning Velocity (Weight: 15%)
        # Base on certifications, languages, and profile completion
        certs_count = len(candidate.certifications) if candidate.certifications else 0
        langs_count = len(candidate.languages) if candidate.languages else 0
        
        s_learning = min(100.0, (certs_count * 30.0) + (langs_count * 15.0) + 40.0)
        if certs_count > 0:
            strengths.append(f"Continuous learning commitment ({certs_count} professional certification(s))")
        if langs_count > 1:
            strengths.append("Multilingual communication proficiency")

        # 3. Career Trajectory (Weight: 25%)
        # Extract CTS from existing scorer
        trajectory_report = CareerTrajectoryScorer.calculate_score(candidate)
        s_trajectory = float(trajectory_report["career_trajectory_score"])
        
        if s_trajectory >= 70.0:
            strengths.append(f"Strong upward career trajectory (Trajectory Score: {int(s_trajectory)}/100)")
            growth_indicators.append("Demonstrated capacity to take on higher senior responsibilities")
        elif s_trajectory >= 45.0:
            strengths.append("Steady career trajectory progress")
        else:
            growth_indicators.append("Long periods of role stagnation or frequent transitions")

        # 4. Project Quality (Weight: 15%)
        # Base on GitHub activity and platform skill tests
        github_score = candidate.redrob_signals.github_activity_score
        assessments_count = len(candidate.redrob_signals.skill_assessment_scores)
        
        # Default project score
        s_project = 50.0
        if github_score > 0:
            s_project = github_score
            if github_score >= 40.0:
                strengths.append(f"Proven open-source engineering capability (GitHub Score: {github_score})")
                growth_indicators.append("Regular open-source project contributions")
        if assessments_count > 0:
            s_project = min(100.0, s_project + (assessments_count * 15.0))
            strengths.append(f"Validated platform skills via {assessments_count} technical test(s)")

        # 5. Leadership Indicators (Weight: 15%)
        # Base on career trajectory leadership metrics
        lead_roles = trajectory_report["leadership_roles"]
        promo_count = trajectory_report["promotion_count"]
        
        s_leadership = min(100.0, (lead_roles * 40.0) + (promo_count * 20.0))
        if lead_roles > 0:
            strengths.append(f"Proven leadership and team steering history ({lead_roles} role(s))")
        if promo_count > 0:
            growth_indicators.append(f"Rapid advancement via {promo_count} internal promotion(s)")

        # 6. Domain Adaptability (Weight: 15%)
        # Base on transitions between different industries
        industries = {role.industry.lower().strip() for role in candidate.career_history if role.industry}
        num_industries = len(industries)
        
        s_adaptability = min(100.0, num_industries * 35.0)
        if num_industries >= 3:
            strengths.append(f"High industry flexibility and adaptability ({num_industries} distinct sectors)")
            growth_indicators.append("Successfully navigated diverse industrial domains")
        elif num_industries >= 2:
            strengths.append("Cross-industry professional exposure")

        # Compute weighted potential score [0.0 - 100.0]
        potential_score = (
            (s_diversity * 0.15)
            + (s_learning * 0.15)
            + (s_trajectory * 0.25)
            + (s_project * 0.15)
            + (s_leadership * 0.15)
            + (s_adaptability * 0.15)
        )
        potential_score = int(round(potential_score))

        # Confidence calculation based on data fullness
        completeness = candidate.redrob_signals.profile_completeness_score
        confidence = min(0.99, round((completeness / 100.0) * 0.80 + 0.20, 2))

        return {
            "potential_score": potential_score,
            "confidence": confidence,
            "strengths": strengths,
            "growth_indicators": growth_indicators
        }
