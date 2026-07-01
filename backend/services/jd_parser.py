import logging
import re
from typing import Dict, List, Set

from backend.services.skills_extractor import ALIAS_MAP, normalize_skill_name
from backend.services.skill_score import REQUIRED_SKILL_GROUPS, PREFERRED_SKILL_GROUPS

logger = logging.getLogger(__name__)

# Standard roles to search for
STANDARD_ROLES = [
    "Senior Applied ML/Search Ranking Engineer",
    "Search Ranking Engineer",
    "Senior Applied Machine Learning Engineer",
    "Applied Machine Learning Engineer",
    "Applied ML Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "Data Scientist",
    "Senior Backend Engineer",
    "Backend Engineer",
    "Senior Data Engineer",
    "Data Engineer",
    "Senior Software Engineer",
    "Software Engineer",
]


class JDParser:
    """
    Service to parse and extract structured metadata from raw Job Descriptions.
    """

    @classmethod
    def extract_role(cls, jd_text: str) -> str:
        """
        Extracts the job role/title from the job description.
        """
        if not jd_text:
            return "Software Engineer"

        # 1. Search for title prefixes like "Title:", "Role:", "Position:"
        title_patterns = [
            r"(?i)(?:job\s+)?title\s*:\s*(.*)",
            r"(?i)(?:job\s+)?role\s*:\s*(.*)",
            r"(?i)(?:job\s+)?position\s*:\s*(.*)",
        ]
        for pattern in title_patterns:
            match = re.search(pattern, jd_text)
            if match:
                title = match.group(1).strip()
                # If the title is on a line with other things, split by newlines
                title = title.split("\n")[0].strip()
                if title:
                    return title

        # 2. Check for exact/substring matches of standard roles
        for role in STANDARD_ROLES:
            # Match using word boundaries to avoid false positives
            pattern = r"(?i)\b" + re.escape(role) + r"\b"
            if re.search(pattern, jd_text):
                return role

        # 3. Fallback: Check the first non-empty line if it is short
        lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
        if lines and len(lines[0]) < 80:
            return lines[0]

        return "Software Engineer"

    @classmethod
    def extract_experience_required(cls, jd_text: str) -> int:
        """
        Extracts the minimum years of experience required from the job description.
        """
        if not jd_text:
            return 0

        # Patterns like: "6+ years", "5-7 years", "3 to 5 years", "experience: 4 years"
        experience_patterns = [
            # e.g., "5-7 years", "5 to 7 years"
            r"\b(\d+)\s*(?:-|to)\s*\d+\s*(?:years?|yrs?)\b",
            # e.g., "6+ years", "6 years"
            r"\b(\d+)\+?\s*(?:years?|yrs?)\b",
            # e.g., "experience: 4 years"
            r"(?i)\bexperience\s*:\s*(\d+)\s*(?:years?|yrs?)\b",
        ]

        for pattern in experience_patterns:
            matches = re.findall(pattern, jd_text, re.IGNORECASE)
            if matches:
                try:
                    # Return the first found number
                    return int(matches[0])
                except (ValueError, IndexError):
                    continue

        return 0

    @classmethod
    def extract_skills(cls, jd_text: str) -> List[str]:
        """
        Extracts technical skills and categories recognized in the job description.
        """
        if not jd_text:
            return []

        matched_skills: Set[str] = set()

        # 1. Check direct ALIAS_MAP keys and values
        for alias, standard_name in ALIAS_MAP.items():
            # Use custom boundary matching to handle special characters (like C++)
            pattern = r"(?i)(?<!\w)" + re.escape(alias) + r"(?!\w)"
            if re.search(pattern, jd_text):
                matched_skills.add(standard_name)

        # 2. Check REQUIRED_SKILL_GROUPS and PREFERRED_SKILL_GROUPS
        all_groups = {**REQUIRED_SKILL_GROUPS, **PREFERRED_SKILL_GROUPS}
        for group_name, synonyms in all_groups.items():
            # Check synonyms
            for synonym in synonyms:
                pattern = r"(?i)(?<!\w)" + re.escape(synonym) + r"(?!\w)"
                if re.search(pattern, jd_text):
                    matched_skills.add(group_name)
                    break

        # Return sorted list
        return sorted(list(matched_skills))

    @classmethod
    def extract_domain(cls, jd_text: str) -> str:
        """
        Determines the primary domain of the job description using weighted keywords.
        """
        if not jd_text:
            return "Software Engineering"

        # Domain scoring weights based on domain specificity
        domain_weights = {
            "Search & Ranking": 3.0,
            "Machine Learning / AI": 2.0,
            "Backend Engineering": 1.0,
            "DevOps & Cloud": 1.0,
        }

        # Define keywords for each domain
        domain_keywords = {
            "Search & Ranking": [
                "search", "ranking", "recommendation", "information retrieval", 
                "retrieval", "ndcg", "mrr", "map", "ltr", "learning to rank",
                "dense retrieval", "hybrid search", "re-ranking", "vector search",
                "embeddings", "vector database", "vector databases", "milvus", 
                "pinecone", "weaviate", "qdrant", "faiss"
            ],
            "Machine Learning / AI": [
                "machine learning", "ml", "deep learning", "nlp", "computer vision", 
                "llm", "embeddings", "sentence-transformers", "pytorch", "tensorflow",
                "transformers", "fine-tuning", "artificial intelligence", "ai"
            ],
            "Backend Engineering": [
                "backend", "database", "distributed systems", "software engineer", 
                "infrastructure", "python", "sql", "api", "postgres", "redis",
                "kafka", "spark", "airflow"
            ],
            "DevOps & Cloud": [
                "devops", "cloud", "aws", "kubernetes", "docker", "terraform", 
                "ci/cd", "gcp", "azure", "deployment"
            ],
        }

        scores = {domain: 0.0 for domain in domain_keywords}

        # Count matches and apply weights
        for domain, keywords in domain_keywords.items():
            weight = domain_weights[domain]
            for keyword in keywords:
                # Case-insensitive substring count with custom boundaries
                pattern = r"(?i)(?<!\w)" + re.escape(keyword) + r"(?!\w)"
                matches = re.findall(pattern, jd_text)
                scores[domain] += len(matches) * weight

        # Find domain with max score
        max_domain = max(scores, key=lambda k: scores[k])
        
        # Default fallback if no keywords found
        if scores[max_domain] == 0:
            return "Software Engineering"

        return max_domain

