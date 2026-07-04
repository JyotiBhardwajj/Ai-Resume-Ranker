import logging
from typing import Dict, List, Any

from backend.models.candidate import Candidate
from backend.services.ranking_engine import RankingEngine
from backend.services.career_trajectory import CareerTrajectoryScorer
from backend.services.potential_score import PotentialScorer

logger = logging.getLogger(__name__)


class CandidateComparisonExplainer:
    """
    Service to compare two candidates ("Why Candidate A > Candidate B")
    and provide recruiter-friendly decision summaries, advantages, and disadvantages.
    """

    @classmethod
    def compare(
        cls, 
        candidate_a: Candidate, 
        candidate_b: Candidate, 
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Compares candidate_a and candidate_b against the job description.

        Args:
            candidate_a: First Candidate model.
            candidate_b: Second Candidate model.
            jd_text: Job Description text.

        Returns:
            Dictionary with winner, winner_score, comparison_summary,
            advantages, disadvantages, and decision_factors.
        """
        # 1. Rank candidates using the RankingEngine to get weighted scores
        engine = RankingEngine()
        ranked = engine.rank_candidates([candidate_a, candidate_b], jd_text)
        
        # Ensure we map results back correctly
        rc_map = {rc.candidate_id: rc for rc in ranked}
        rc_a = rc_map.get(candidate_a.candidate_id)
        rc_b = rc_map.get(candidate_b.candidate_id)

        if not rc_a or not rc_b:
            raise ValueError("Failed to compute ranking scores for both candidates.")

        # Determine winner/loser based on final_score (tie breaker: candidate_id ascending)
        if rc_a.final_score > rc_b.final_score:
            winner_cand, loser_cand = candidate_a, candidate_b
            winner_rc, loser_rc = rc_a, rc_b
        elif rc_b.final_score > rc_a.final_score:
            winner_cand, loser_cand = candidate_b, candidate_a
            winner_rc, loser_rc = rc_b, rc_a
        else:
            # Tie break on ID ascending
            if candidate_a.candidate_id < candidate_b.candidate_id:
                winner_cand, loser_cand = candidate_a, candidate_b
                winner_rc, loser_rc = rc_a, rc_b
            else:
                winner_cand, loser_cand = candidate_b, candidate_a
                winner_rc, loser_rc = rc_b, rc_a

        # 2. Extract downstream potential and trajectory scores
        w_pot = PotentialScorer.calculate_potential(winner_cand)
        l_pot = PotentialScorer.calculate_potential(loser_cand)
        
        w_traj = CareerTrajectoryScorer.calculate_score(winner_cand)
        l_traj = CareerTrajectoryScorer.calculate_score(loser_cand)

        # 3. Compile dimensions for comparison
        w_scores = {
            "final": winner_rc.final_score,
            "semantic": winner_rc.semantic_score,
            "skill": winner_rc.skill_score,
            "experience": winner_rc.experience_score,
            "potential": float(w_pot.get("potential_score", 0)),
            "trajectory": float(w_traj.get("career_trajectory_score", 0)),
            "skills_count": len(winner_rc.matched_skills)
        }

        l_scores = {
            "final": loser_rc.final_score,
            "semantic": loser_rc.semantic_score,
            "skill": loser_rc.skill_score,
            "experience": loser_rc.experience_score,
            "potential": float(l_pot.get("potential_score", 0)),
            "trajectory": float(l_traj.get("career_trajectory_score", 0)),
            "skills_count": len(loser_rc.matched_skills)
        }

        # 4. Generate advantages and disadvantages
        advantages: List[str] = []
        disadvantages: List[str] = []
        decision_factors: List[str] = []

        # Define metrics to check
        comparison_metrics = [
            ("skill", "Core required technical skills alignment"),
            ("semantic", "Semantic profile role alignment"),
            ("experience", "Years of relevant domain experience"),
            ("trajectory", "Career trajectory and progression velocity"),
            ("potential", "Calculated future potential score"),
            ("skills_count", "Volume of matched skill sets")
        ]

        for key, description in comparison_metrics:
            diff = w_scores[key] - l_scores[key]
            if diff > 0:
                advantages.append(f"Superior {description.lower()} (+{round(diff, 1)} difference)")
                # If difference is significant, mark as key decision factor
                if (key in ["skill", "experience", "semantic"] and diff >= 5.0) or (key in ["trajectory", "potential"] and diff >= 10.0):
                    decision_factors.append(description)
            elif diff < 0:
                disadvantages.append(f"Slightly lower {description.lower()} ({round(diff, 1)} difference)")

        if not decision_factors:
            decision_factors.append("Overall balanced score profile")

        # 5. Build recruiter comparison summary text
        w_name = winner_cand.profile.anonymized_name
        l_name = loser_cand.profile.anonymized_name
        
        skills_diff = w_scores["skill"] - l_scores["skill"]
        exp_diff = w_scores["experience"] - l_scores["experience"]
        
        summary_details = []
        if skills_diff > 0:
            summary_details.append(f"stronger technical alignment (skills: {w_scores['skill']}% vs {l_scores['skill']}%)")
        if exp_diff > 0:
            summary_details.append(f"more relevant experience years (experience score: {w_scores['experience']}% vs {l_scores['experience']}%)")
            
        summary_str = ", ".join(summary_details)
        if summary_str:
            comparison_summary = (
                f"{w_name} is ranked higher than {l_name} primarily due to having {summary_str}. "
                f"While {l_name} shows competitive strengths (e.g. potential of {l_scores['potential']}% vs {w_scores['potential']}%), "
                f"{w_name}'s immediate domain fit makes them the preferred candidate for this role."
            )
        else:
            comparison_summary = (
                f"{w_name} slightly outperforms {l_name} across semantic fit metrics, leading to a higher overall rank. "
                f"Both candidates share highly similar technical competencies."
            )

        return {
            "winner": winner_cand.candidate_id,
            "winner_score": int(round(winner_rc.final_score)),
            "comparison_summary": comparison_summary,
            "advantages": advantages,
            "disadvantages": disadvantages,
            "decision_factors": decision_factors
        }
