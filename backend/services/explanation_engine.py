import logging
from typing import Dict, List, Any

from backend.models.candidate import Candidate
from backend.services.evidence_engine import EvidenceEngine
from backend.services.missing_skills import MissingSkillsAnalyzer
from backend.services.potential_score import PotentialScorer

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """
    Service to generate structured, recruiter-friendly, and explainable ranking details
    for ranked candidates matching a Job Description.
    """

    @classmethod
    def generate_explanation(
        cls, 
        candidate: Candidate, 
        jd_text: str, 
        rank: int, 
        score: float
    ) -> Dict[str, Any]:
        """
        Generates explainable ranking output for a candidate.

        Args:
            candidate: Validated Candidate model instance.
            jd_text: The Job Description text.
            rank: Assigned rank (integer).
            score: Computed fit score.

        Returns:
            Dictionary containing ranking details, explanation text, strengths,
            concerns, matched_skills, and missing_skills.
        """
        # 1. Fetch data from upstream services
        evidence = EvidenceEngine.generate_evidence(candidate, jd_text)
        missing_analysis = MissingSkillsAnalyzer.analyze_missing_skills(candidate, jd_text)
        potential = PotentialScorer.calculate_potential(candidate)

        # 2. Build recruiter-friendly concerns list
        concerns: List[str] = []
        
        # A. Critical skills concerns
        critical_missing = missing_analysis.get("critical_missing_skills", [])
        if critical_missing:
            concerns.append(f"Missing critical required skill(s): {', '.join(critical_missing)}")
            
        # B. Availability/Notice Period
        notice_days = candidate.redrob_signals.notice_period_days
        if notice_days >= 90:
            concerns.append(f"Long notice period of {notice_days} days could delay immediate placement")
        elif notice_days >= 60:
            concerns.append(f"Notice period of {notice_days} days is moderate")

        # C. Stagnation / Job-hopping indicators
        for gi in potential.get("growth_indicators", []):
            if "stagnation" in gi.lower() or "job-hopping" in gi.lower():
                concerns.append(gi)

        if not concerns:
            concerns.append("No major technical or behavioral concerns detected")

        # 3. Combine strengths from evidence and potential scorers
        strengths = list(set(evidence.get("strengths", []) + potential.get("strengths", [])))
        strengths.sort()

        # 4. Generate the main recruiter explanation text
        explanation_justification = evidence.get("justification", "")
        potential_val = potential.get("potential_score", 0)
        
        explanation = (
            f"Candidate {candidate.profile.anonymized_name} is ranked #{rank} with a fit score of {score}%. "
            f"{explanation_justification} "
            f"Additionally, their calculated Future Potential Score is {potential_val}% (confidence: {int(potential.get('confidence', 0.0) * 100)}%), "
            f"marking them as a strong asset for long-term growth and technical adaptability."
        )

        return {
            "candidate_id": candidate.candidate_id,
            "rank": rank,
            "score": int(round(score)),
            "explanation": explanation,
            "strengths": strengths,
            "concerns": concerns,
            "matched_skills": missing_analysis.get("matched_skills", []),
            "missing_skills": missing_analysis.get("missing_skills", [])
        }
