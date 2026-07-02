import logging
from backend.models.jd import JobDescription
from backend.services.semantic_layer.semantic_match import SemanticMatchEngine
from backend.services.ranking_layer.domain_score import DomainScoreEngine
from backend.services.candidate_parser import CandidateParser
from backend.services.skill_score import SkillScorer
from backend.services.experience_score import ExperienceScorer
from backend.services.career_trajectory import CareerTrajectoryScorer

from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry

logger = logging.getLogger(__name__)

class RetrievalEngine:
    """
    Implements the Top-50 Retrieval Pipeline (5000 -> 500 -> 50 -> 10).
    Coordinates hard filters, semantic search, and hybrid ranking.
    """
    
    @staticmethod
    async def generate_vector_search_query(jd: JobDescription) -> str:
        prompt = f"""
You are an expert technical sourcer building a query for a vector database.
Write a dense, highly optimized paragraph describing the ideal candidate's profile for semantic matching.
Focus heavily on the exact technical skills, the domain context, the seniority level, and synonyms for the required skills.
Return ONLY the raw paragraph text. Do not include markdown, quotes, or conversational filler.

Role: {jd.role}
Domain: {jd.domain}
Required Skills: {', '.join(jd.required_skills)}
Nice to Have: {', '.join(jd.nice_to_have_skills)}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text.strip()
    
    @staticmethod
    async def retrieve_and_rank(jd: JobDescription, is_custom: bool = False, user_id: str = None) -> list:
        """
        Executes the full retrieval and ranking pipeline.
        
        Args:
            jd: The parsed JobDescription model.
            
        Returns:
            List of all 25 ranked candidates.
        """
        # STEP 1: Construct an LLM-optimized semantic string from the JD for embedding
        jd_semantic_string = await RetrievalEngine.generate_vector_search_query(jd)
        
        # STEP 2: Semantic Retrieval (Top 50)
        try:
            semantic_candidates = await SemanticMatchEngine.match_candidates(
                jd_summary_text=jd_semantic_string, 
                top_k=50,
                is_custom=is_custom,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []
            
        if not semantic_candidates:
            return []

        # Apply Hard Filter: Minimum Experience
        if jd.min_experience_years is not None:
            filtered_candidates = []
            for c in semantic_candidates:
                exp = c.get("profile_data", {}).get("profile", {}).get("years_of_experience", 0)
                if exp >= jd.min_experience_years:
                    filtered_candidates.append(c)
            semantic_candidates = filtered_candidates

        # STEP 3: Hybrid Ranking
        ranked_candidates = []
        for candidate in semantic_candidates:
            # Supabase RPC returns the similarity as 'similarity'
            semantic_score = candidate.get("similarity", 0.0) * 100 
            
            # Extract full candidate profile (assuming RPC returns it in 'profile_data')
            profile_data = candidate.get("profile_data", {})
            career_history = profile_data.get("career_history", [])
            
            # Calculate Domain Fit
            domain_score = DomainScoreEngine.calculate_domain_fit(jd.domain, career_history)
            
            # Calculate Skill, Experience, Trajectory, and Potential scores using candidate parser
            try:
                candidate_model = CandidateParser.parse_dict(profile_data)
                skill_report = SkillScorer.calculate_match(candidate_model, jd_text=jd_semantic_string)
                skill_score = skill_report["score"]
                experience_score = ExperienceScorer.calculate_score(candidate_model)
                trajectory_report = CareerTrajectoryScorer.calculate_score(candidate_model)
                trajectory_score = float(trajectory_report.get("career_trajectory_score", 0.0))
                from backend.services.potential_score import PotentialScorer
                potential_report = PotentialScorer.calculate_potential(candidate_model)
                potential_score = float(potential_report.get("potential_score", 0.0))
            except Exception as e:
                logger.error(f"Failed to parse candidate model for scoring: {e}")
                skill_score = 0.0
                experience_score = 0.0
                trajectory_score = 0.0
                potential_score = 0.0

            # Replace the placeholder with the combined Skill, Experience, Trajectory, and Potential scores (50% weight total)
            other_score = (skill_score + experience_score + trajectory_score + potential_score) / 4.0
            
            final_score = (
                (0.40 * semantic_score) + 
                (0.10 * domain_score) + 
                (0.50 * other_score)
            )
            
            ranked_candidates.append({
                "candidate_id": candidate.get("candidate_id"),
                "semantic_score": round(semantic_score, 2),
                "domain_score": domain_score,
                "final_score": round(final_score, 2),
                "profile": profile_data.get("profile", {}),
                "skills": [s.get("name") for s in profile_data.get("skills", []) if isinstance(s, dict)]
            })
            
        # Sort by final score descending, and candidate_id ascending as tie-breaker
        ranked_candidates.sort(key=lambda x: (-x["final_score"], x["candidate_id"]))
        
        # Return top 25 sorted candidates
        return ranked_candidates[:25]
