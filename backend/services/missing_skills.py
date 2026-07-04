import logging
from typing import Dict, List, Set

from backend.models.candidate import Candidate
from backend.services.skills_extractor import SkillsExtractor, normalize_skill_name
from backend.services.skill_score import REQUIRED_SKILL_GROUPS, PREFERRED_SKILL_GROUPS
from backend.services.jd_parser import JDParser

logger = logging.getLogger(__name__)


class MissingSkillsAnalyzer:
    """
    Analyzer service to determine matched, missing, critical missing,
    and optional missing skills of a candidate compared against a Job Description.
    """

    @classmethod
    def analyze_missing_skills(cls, candidate: Candidate, jd_text: str) -> Dict[str, List[str]]:
        """
        Compares candidate skills against JD skills and categorizes them.

        Args:
            candidate: Validated Candidate model instance.
            jd_text: The Job Description text.

        Returns:
            Dictionary containing:
                - matched_skills: List of matching skills/categories.
                - missing_skills: List of all missing skills/categories.
                - critical_missing_skills: List of missing critical skills/categories.
                - optional_missing_skills: List of missing optional skills/categories.
        """
        # 1. Extract candidate skills and normalize them
        candidate_skills = {
            normalize_skill_name(s.name).lower().strip() for s in candidate.skills
        }

        # 2. Extract JD skills/categories
        jd_skills = JDParser.extract_skills(jd_text)

        matched_skills: Set[str] = set()
        missing_skills: Set[str] = set()
        critical_missing_skills: Set[str] = set()
        optional_missing_skills: Set[str] = set()

        # Build sets of synonyms for categorization
        critical_terms: Set[str] = set()
        for group_name, synonyms in REQUIRED_SKILL_GROUPS.items():
            critical_terms.add(group_name.lower().strip())
            for syn in synonyms:
                critical_terms.add(normalize_skill_name(syn).lower().strip())

        optional_terms: Set[str] = set()
        for group_name, synonyms in PREFERRED_SKILL_GROUPS.items():
            optional_terms.add(group_name.lower().strip())
            for syn in synonyms:
                optional_terms.add(normalize_skill_name(syn).lower().strip())

        # 3. Classify each JD skill
        for skill in jd_skills:
            skill_norm = normalize_skill_name(skill).lower().strip()
            
            # Check if candidate matches this skill (or any synonym of the group if this is a group)
            is_matched = False
            
            # First, direct match check
            if skill_norm in candidate_skills:
                is_matched = True
            else:
                # If it's a required group name, check if candidate has any of its synonyms
                for group_name, synonyms in REQUIRED_SKILL_GROUPS.items():
                    if skill_norm == group_name.lower().strip():
                        norm_syns = {normalize_skill_name(syn).lower().strip() for syn in synonyms}
                        if candidate_skills.intersection(norm_syns):
                            is_matched = True
                            break
                            
                # If it's a preferred group name, check if candidate has any of its synonyms
                if not is_matched:
                    for group_name, synonyms in PREFERRED_SKILL_GROUPS.items():
                        if skill_norm == group_name.lower().strip():
                            norm_syns = {normalize_skill_name(syn).lower().strip() for syn in synonyms}
                            if candidate_skills.intersection(norm_syns):
                                is_matched = True
                                break

            # Categorize the skill
            if is_matched:
                matched_skills.add(skill)
            else:
                missing_skills.add(skill)
                
                # Check if it is a critical skill (part of REQUIRED_SKILL_GROUPS)
                is_critical = False
                if skill_norm in critical_terms:
                    is_critical = True
                else:
                    # Check if the skill name contains or is contained in any critical term
                    for term in critical_terms:
                        if term in skill_norm or skill_norm in term:
                            is_critical = True
                            break
                            
                if is_critical:
                    critical_missing_skills.add(skill)
                else:
                    optional_missing_skills.add(skill)

        return {
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "critical_missing_skills": sorted(list(critical_missing_skills)),
            "optional_missing_skills": sorted(list(optional_missing_skills)),
        }
