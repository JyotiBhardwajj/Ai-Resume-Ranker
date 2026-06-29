import logging
from backend.models.candidate import Candidate, CareerHistory
from backend.services.career_parser import get_seniority_level

logger = logging.getLogger(__name__)

# Keywords mapping to relevant ML, AI, Search, NLP, or Information Retrieval domains
RELEVANT_KEYWORDS = [
    "machine learning", "ml", "ai", "nlp", "computer vision", "search", "retrieval", 
    "ranking", "recommendation", "data scientist", "deep learning", "information retrieval",
    "vector search", "embeddings", "hybrid search", "re-ranking", "dense retrieval", 
    "rag", "recommendation system", "learning to rank", "ltr", "data engineer", "spark", "airflow"
]


class ExperienceScorer:
    """
    Service to compare candidate experience against Job Description expectations,
    producing a normalized fit score from 0 to 100 based on experience metrics.
    """

    @staticmethod
    def is_role_relevant(role: CareerHistory) -> bool:
        """
        Determines if a professional role matches the JD's technical domains
        (Applied ML, NLP, Search, Ranking, or Data Pipelines).

        Args:
            role: CareerHistory model instance.

        Returns:
            Boolean indicating relevance.
        """
        title_lower = role.title.lower()
        desc_lower = role.description.lower()

        # Check if any target domain keyword is present
        for kw in RELEVANT_KEYWORDS:
            if kw in title_lower or kw in desc_lower:
                return True
        return False

    @classmethod
    def calculate_score(cls, candidate: Candidate) -> float:
        """
        Calculates a normalized score (0.0 to 100.0) based on:
        - Total years of experience (Target: 5 - 9 years)
        - Relevant ML/Search experience years (Target: 4+ years)
        - Seniority level of roles (Target: Senior or Lead)

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            Float experience score.
        """
        total_years = candidate.profile.years_of_experience

        # 1. Total Years Score (Weight: 30%)
        # Target: 5.0 to 9.0 years
        if 5.0 <= total_years <= 9.0:
            s_total = 100.0
        elif total_years < 5.0:
            s_total = (total_years / 5.0) * 100.0
        else:  # overqualification decay
            if total_years <= 12.0:
                s_total = 95.0
            elif total_years <= 15.0:
                s_total = 80.0
            else:
                s_total = 60.0

        # 2. Relevant Experience Score (Weight: 45%)
        # Target: 4+ years of relevant ML/AI/Retrieval/Data experience
        relevant_months = 0
        for role in candidate.career_history:
            if cls.is_role_relevant(role):
                relevant_months += role.duration_months

        relevant_years = relevant_months / 12.0
        if relevant_years >= 4.0:
            s_relevant = 100.0
        else:
            s_relevant = (relevant_years / 4.0) * 100.0

        # 3. Role Seniority Score (Weight: 25%)
        # Target: Senior/Lead judgment (Senior is Level 3, Lead is Level 4)
        highest_sl = 0
        for role in candidate.career_history:
            sl = get_seniority_level(role.title)
            if sl > highest_sl:
                highest_sl = sl

        # Map peak seniority level to score
        seniority_scores = {
            5: 100.0,  # Executive / CTO / Principal Architect
            4: 100.0,  # Lead / Manager / Staff
            3: 90.0,   # Senior
            2: 60.0,   # Mid-level
            1: 30.0,   # Junior
            0: 10.0,   # Intern
        }
        s_seniority = seniority_scores.get(highest_sl, 0.0)

        # Compute final weighted score [0.0, 100.0]
        total_score = (0.30 * s_total) + (0.45 * s_relevant) + (0.25 * s_seniority)
        return round(total_score, 2)
