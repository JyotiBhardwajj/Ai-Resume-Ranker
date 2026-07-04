import logging
import re
from typing import Dict, List, Set, Any

from backend.models.candidate import Candidate
from backend.services.skills_extractor import SkillsExtractor
from backend.services.skill_score import SkillScorer
from backend.services.experience_score import ExperienceScorer
from backend.services.career_parser import get_seniority_level, extract_from_candidate as extract_career_summary
from backend.services.jd_parser import JDParser

logger = logging.getLogger(__name__)

ACTION_VERBS = [
    "build", "built", "implement", "implemented", "design", "designed",
    "develop", "developed", "create", "created", "engineer", "engineered",
    "optimize", "optimized", "architect", "architected", "manage", "managed",
    "deliver", "delivered", "lead", "led", "deploy", "deployed", "integrate",
    "integrated", "write", "wrote", "scale", "scaled", "launch", "launched"
]


class EvidenceEngine:
    """
    Service to generate structured evidence, highlights, strengths, and rankings justifications
    for candidates matching a specific Job Description.
    """

    @classmethod
    def generate_evidence(cls, candidate: Candidate, jd_text: str) -> Dict[str, Any]:
        """
        Generates justification and evidence details for a candidate profile against the JD.

        Args:
            candidate: Validated Candidate model instance.
            jd_text: The Job Description text.

        Returns:
            Dictionary containing matched_skills, matched_experience, matched_projects,
            strengths, and justification.
        """
        # 1. Matched Skills (Individual skills and category groups)
        jd_skills = {s.lower().strip() for s in JDParser.extract_skills(jd_text)}
        cand_skills_list = SkillsExtractor.extract_from_candidate(candidate)
        cand_skill_names = {s.name for s in cand_skills_list}
        
        matched_individual = []
        for name in cand_skill_names:
            if name.lower().strip() in jd_skills:
                matched_individual.append(name)

        skill_report = SkillScorer.calculate_match(candidate, jd_text=jd_text)
        matched_groups = skill_report.get("matched_skills", [])
        
        # Combine and deduplicate skills
        matched_skills = sorted(list(set(matched_individual + matched_groups)))

        # 2. Matched Experience (Roles aligned with the JD requirements)
        matched_experience = []
        relevant_months = 0
        highest_sl = 0
        peak_title = candidate.profile.current_title

        for role in candidate.career_history:
            sl = get_seniority_level(role.title)
            if sl > highest_sl:
                highest_sl = sl
                peak_title = role.title

            if ExperienceScorer.is_role_relevant(role):
                relevant_months += role.duration_months
                matched_experience.append(
                    f"{role.title} at {role.company} ({role.duration_months} months)"
                )

        relevant_years = round(relevant_months / 12.0, 1)

        # 3. Matched Projects (Extracted project descriptions containing ML/search verbs)
        matched_projects = []
        
        # Sentences from profile summary
        summary_sentences = re.split(r'\.\s+|\n+', candidate.profile.summary)
        # Sentences from career history descriptions
        desc_sentences = []
        for role in candidate.career_history:
            desc_sentences.extend(re.split(r'\.\s+|\n+', role.description))

        all_sentences = [s.strip() for s in (summary_sentences + desc_sentences) if s.strip()]

        for sentence in all_sentences:
            sentence_lower = sentence.lower()
            
            # Check if it mentions an action verb using regex for word boundaries
            has_verb = any(re.search(r"\b" + verb + r"\b", sentence_lower) for verb in ACTION_VERBS)
            
            # Check if it contains any matched skills or search/ML keywords
            has_keyword = False
            for skill in matched_skills:
                if skill.lower() in sentence_lower:
                    has_keyword = True
                    break
                    
            if not has_keyword:
                additional_kws = ["model", "pipeline", "search", "ranking", "dataset", "algorithm", "platform", "system", "infrastructure"]
                has_keyword = any(re.search(r"\b" + kw + r"\b", sentence_lower) for kw in additional_kws)

            if has_verb and has_keyword:
                # Clean clean up punctuation
                cleaned = sentence.rstrip('.')
                if cleaned not in matched_projects and len(cleaned) > 20:
                    matched_projects.append(cleaned)
                    if len(matched_projects) >= 5: # Cap to top 5 projects
                        break

        # 4. Strengths
        strengths = []
        total_years = candidate.profile.years_of_experience
        
        if total_years >= 5.0:
            strengths.append(f"Strong overall professional experience ({total_years} years)")
        if relevant_years >= 3.0:
            strengths.append(f"Deep domain experience in ML/Search fields ({relevant_years} years)")
        if highest_sl >= 3:
            strengths.append(f"Senior leadership capability (Peak role: {peak_title})")
        
        # Redrob signals highlights
        signals = candidate.redrob_signals
        if signals.github_activity_score > 30.0:
            strengths.append(f"Active open-source footprint (GitHub Activity Score: {signals.github_activity_score})")
        if signals.profile_completeness_score >= 90.0:
            strengths.append("High profile completeness and platform engagement")
        if signals.notice_period_days <= 30:
            strengths.append(f"Highly available candidate (Notice period: {signals.notice_period_days} days)")

        if not strengths:
            strengths.append("Possesses core technical qualifications and positive platform engagement signals")

        # 5. Justification summary
        exp_score = ExperienceScorer.calculate_score(candidate)
        skill_score_val = skill_report["score"]
        
        skills_str = ", ".join(matched_skills[:4])
        if len(matched_skills) > 4:
            skills_str += f" (+{len(matched_skills) - 4} more)"

        role_name = JDParser.extract_role(jd_text)

        justification = (
            f"{candidate.profile.anonymized_name} is a strong match for the {role_name} position with a "
            f"skill match score of {skill_score_val}% and experience score of {exp_score}%. "
            f"They bring {total_years} years of total experience, including {relevant_years} years in relevant domains, "
            f"with demonstrated expertise in {skills_str or 'core tech requirements'}. "
            f"Their peak title is '{peak_title}'."
        )

        return {
            "matched_skills": matched_skills,
            "matched_experience": matched_experience,
            "matched_projects": matched_projects,
            "strengths": strengths,
            "justification": justification
        }
