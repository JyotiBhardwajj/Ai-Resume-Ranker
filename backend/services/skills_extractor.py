import logging
from typing import Any, Dict, List, Set, Union
from pydantic import BaseModel

try:
    from backend.models.candidate import Candidate, Skill
except ImportError:
    # Dummy definition for local unit testing fallback
    class Skill(BaseModel):  # type: ignore
        name: str
        proficiency: str
        endorsements: int
        duration_months: Any

logger = logging.getLogger(__name__)

# Comprehensive technical skills alias mapping dictionary
ALIAS_MAP: Dict[str, str] = {
    # Languages
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "python2": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "es6": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "cpp": "C++",
    "c++": "C++",
    "golang": "Go",
    "go": "Go",
    "rb": "Ruby",
    "ruby": "Ruby",
    "sh": "Bash/Shell",
    "bash": "Bash/Shell",
    "shell": "Bash/Shell",
    
    # Frameworks / Runtimes
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "express": "Express.js",
    "expressjs": "Express.js",
    
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "pg": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "elasticsearch": "Elasticsearch",
    "es": "Elasticsearch",
    
    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "tf": "Terraform",
    "ansible": "Ansible",
    
    # Data & AI/ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "tf-idf": "TF-IDF",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf_keras": "Keras",
    "keras": "Keras",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "hadoop": "Apache Hadoop",
    "kafka": "Apache Kafka",
    "airflow": "Apache Airflow",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
}

# Hierarchy of proficiency levels for picking the best one when deduplicating
PROFICIENCY_RANK: Dict[str, int] = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


def normalize_skill_name(name: str) -> str:
    """
    Standardizes a technical skill's name using an alias mapping.
    For unmapped skills, applies title case formatting.

    Args:
        name: Raw skill name.

    Returns:
        Standardized skill name.
    """
    clean_name = name.strip().lower()
    
    # Direct alias lookup
    if clean_name in ALIAS_MAP:
        return ALIAS_MAP[clean_name]
        
    # Handle acronym capitalization (e.g. SQL, REST, API, HTML, CSS)
    acronyms = {"sql", "rest", "api", "html", "css", "xml", "json", "graphql", "db", "sdk", "cli", "git", "ci/cd"}
    if clean_name in acronyms:
        return clean_name.upper()
        
    # Fallback: title capitalization of words
    return " ".join(word.capitalize() for word in clean_name.split())


class SkillsExtractor:
    """
    Service to extract, normalize, and deduplicate technical skills from candidate data.
    """

    @classmethod
    def normalize_skill_list(cls, skills: List[Union[dict, Skill]]) -> List[Skill]:
        """
        Deduplicates a list of Skill objects or dicts by their normalized name.
        Aggregates endorsements, retains the maximum duration, and keeps the highest
        proficiency level when duplicate names are merged.

        Args:
            skills: List of skill dictionaries or Skill Pydantic models.

        Returns:
            Deduplicated list of normalized Skill Pydantic models.
        """
        normalized_skills: Dict[str, Dict[str, Any]] = {}

        for skill in skills:
            # Handle both dictionary and BaseModel input
            if isinstance(skill, BaseModel):
                skill_dict = skill.model_dump()
            else:
                skill_dict = dict(skill)
                
            raw_name = skill_dict.get("name", "")
            if not raw_name:
                continue

            normalized_name = normalize_skill_name(raw_name)
            
            # Extract attributes
            proficiency = skill_dict.get("proficiency", "beginner").lower()
            endorsements = int(skill_dict.get("endorsements", 0))
            duration = skill_dict.get("duration_months")
            duration_months = int(duration) if duration is not None else None

            if normalized_name in normalized_skills:
                # Merge logic
                existing = normalized_skills[normalized_name]
                
                # 1. Take the highest proficiency
                existing_prof = existing["proficiency"]
                if PROFICIENCY_RANK.get(proficiency, 1) > PROFICIENCY_RANK.get(existing_prof, 1):
                    existing["proficiency"] = proficiency
                    
                # 2. Add endorsements together
                existing["endorsements"] += endorsements
                
                # 3. Take maximum duration
                if duration_months is not None:
                    if existing["duration_months"] is None:
                        existing["duration_months"] = duration_months
                    else:
                        existing["duration_months"] = max(existing["duration_months"], duration_months)
            else:
                # Add new
                normalized_skills[normalized_name] = {
                    "name": normalized_name,
                    "proficiency": proficiency,
                    "endorsements": endorsements,
                    "duration_months": duration_months,
                }

        # Convert dictionary values back into structured Skill Pydantic models
        return [Skill(**data) for data in normalized_skills.values()]

    @classmethod
    def get_standardized_names(cls, skills: List[Union[dict, Skill]]) -> Set[str]:
        """
        Helper method to get only the set of standardized, deduplicated skill names.

        Args:
            skills: List of skills.

        Returns:
            A set of normalized skill name strings.
        """
        normalized_list = cls.normalize_skill_list(skills)
        return {skill.name for skill in normalized_list}

    @classmethod
    def extract_from_candidate(cls, candidate: Candidate) -> List[Skill]:
        """
        Extracts and normalizes all skills directly from a Candidate model.

        Args:
            candidate: A validated Candidate model.

        Returns:
            Deduplicated list of standardized Skill objects.
        """
        return cls.normalize_skill_list(candidate.skills)
