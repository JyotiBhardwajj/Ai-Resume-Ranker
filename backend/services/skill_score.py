import logging
from typing import Dict, List, Set, Optional
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME
from backend.models.candidate import Candidate
from backend.services.skills_extractor import normalize_skill_name

logger = logging.getLogger(__name__)

# Job Description Required Skill Categories and their aliases/synonyms
REQUIRED_SKILL_GROUPS: Dict[str, Set[str]] = {
    "Python": {
        "Python", "py", "python3", "python2"
    },
    "Embeddings & Semantic Search": {
        "Embeddings", "Sentence-Transformers", "OpenAI Embeddings", 
        "BGE", "E5", "Semantic Search", "Dense Retrieval", "RAG", "NLP", 
        "Fine-Tuning LLMs", "Image Classification", "Speech Recognition", "TTS"
    },
    "Vector Databases & Hybrid Search": {
        "Vector Database", "Vector Databases", "Pinecone", "Weaviate", 
        "Qdrant", "Milvus", "OpenSearch", "Elasticsearch", "FAISS"
    },
    "Ranking Evaluation": {
        "Evaluation Frameworks", "NDCG", "MRR", "MAP", "Ranking Evaluation", 
        "A/B Testing", "A/B Test"
    }
}

# Job Description Preferred/Desired Skill Categories and their aliases/synonyms
PREFERRED_SKILL_GROUPS: Dict[str, Set[str]] = {
    "LLM Fine-tuning": {
        "LLM Fine-Tuning", "LoRA", "QLoRA", "PEFT", "Weights & Biases", 
        "BentoML", "GANs"
    },
    "Learning to Rank": {
        "Learning to Rank", "LTR", "XGBoost", "Statistical Modeling", 
        "Feature Engineering"
    },
    "Distributed Systems & Large-scale Inference": {
        "Distributed Systems", "Inference Optimization", "Large-Scale Inference", 
        "Apache Beam", "Apache Spark", "Apache Kafka", "Apache Airflow", 
        "Snowflake", "dbt", "AWS", "GCP"
    }
}


class SkillScorer:
    """
    Service to compare candidate skills against Job Description requirements,
    calculating a percentage match score while resolving tech synonyms and aliases.
    """

    @classmethod
    def calculate_match(cls, candidate: Candidate, jd_text: Optional[str] = None) -> dict:
        """
        Calculates a percentage match score and lists matched/missing categories.

        Args:
            candidate: Validated Candidate model instance.
            jd_text: Optional Job Description text.

        Returns:
            Dictionary containing:
                - score: float percentage match [0.0 - 100.0]
                - matched_skills: list of matched skill group names
                - missing_skills: list of missing skill group names
        """
        # Extract and normalize candidate's skill names
        candidate_skills = {
            normalize_skill_name(s.name).lower().strip() for s in candidate.skills
        }

        matched_skills: List[str] = []
        missing_skills: List[str] = []

        if jd_text:
            from backend.services.missing_skills import MissingSkillsAnalyzer
            analysis = MissingSkillsAnalyzer.analyze_missing_skills(candidate, jd_text)
            matched_skills = analysis.get("matched_skills", [])
            missing_skills = analysis.get("missing_skills", [])
            critical_missing = analysis.get("critical_missing_skills", [])
            optional_missing = analysis.get("optional_missing_skills", [])
            
            # Map matched skills to check which ones are critical vs optional based on REQUIRED_SKILL_GROUPS
            critical_matched = []
            optional_matched = []
            
            # Let's classify all matched skills
            critical_terms = set()
            for group_name, synonyms in REQUIRED_SKILL_GROUPS.items():
                critical_terms.add(group_name.lower().strip())
                for syn in synonyms:
                    critical_terms.add(normalize_skill_name(syn).lower().strip())
                    
            for skill in matched_skills:
                skill_norm = normalize_skill_name(skill).lower().strip()
                is_critical = False
                if skill_norm in critical_terms:
                    is_critical = True
                else:
                    for term in critical_terms:
                        if term in skill_norm or skill_norm in term:
                            is_critical = True
                            break
                if is_critical:
                    critical_matched.append(skill)
                else:
                    optional_matched.append(skill)
            
            num_critical = len(critical_matched) + len(critical_missing)
            num_optional = len(optional_matched) + len(optional_missing)
            
            if num_critical > 0 and num_optional > 0:
                critical_score = (len(critical_matched) / num_critical) * 75.0
                optional_score = (len(optional_matched) / num_optional) * 25.0
                total_score = round(critical_score + optional_score, 2)
            elif num_critical > 0:
                total_score = round((len(critical_matched) / num_critical) * 100.0, 2)
            elif num_optional > 0:
                total_score = round((len(optional_matched) / num_optional) * 100.0, 2)
            else:
                total_score = 0.0
        else:
            # 1. Evaluate Required Skills (Weight: 75% of total score, 18.75% each)
            required_matches = 0
            for group_name, synonyms in REQUIRED_SKILL_GROUPS.items():
                norm_synonyms = {
                    normalize_skill_name(s).lower().strip() for s in synonyms
                }
                if candidate_skills.intersection(norm_synonyms):
                    required_matches += 1
                    matched_skills.append(group_name)
                else:
                    missing_skills.append(group_name)

            # 2. Evaluate Preferred Skills (Weight: 25% of total score, 8.33% each)
            preferred_matches = 0
            for group_name, synonyms in PREFERRED_SKILL_GROUPS.items():
                norm_synonyms = {
                    normalize_skill_name(s).lower().strip() for s in synonyms
                }
                if candidate_skills.intersection(norm_synonyms):
                    preferred_matches += 1
                    matched_skills.append(group_name)
                else:
                    missing_skills.append(group_name)

            # 3. Calculate percentage score
            num_required = len(REQUIRED_SKILL_GROUPS)
            num_preferred = len(PREFERRED_SKILL_GROUPS)

            required_percentage = (required_matches / num_required) * 75.0
            preferred_percentage = (preferred_matches / num_preferred) * 25.0

            total_score = round(required_percentage + preferred_percentage, 2)

        return {
            "score": total_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }
