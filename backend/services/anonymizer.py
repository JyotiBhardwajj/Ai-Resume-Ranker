import logging
import re
from typing import Dict, List, Any

from backend.models.candidate import Candidate

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b")


class CandidateAnonymizer:
    """
    Service to anonymize candidate profiles for bias-free hiring.
    Scrubs names, company names, college names, and personal identifiers
    from text fields, replacing them with generic codes (e.g. Company A, University B).
    """

    @classmethod
    def anonymize(cls, candidate: Candidate) -> Dict[str, Any]:
        """
        Anonymizes candidate identifying fields.

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            Dictionary containing {"anonymous_candidate": anonymized_candidate_dict}
        """
        cand_dict = candidate.model_dump()
        
        # 1. Collect all unique company names and institution names
        company_names = set()
        if candidate.profile.current_company:
            company_names.add(candidate.profile.current_company.strip())
        for role in candidate.career_history:
            if role.company:
                company_names.add(role.company.strip())
                
        institution_names = set()
        for edu in candidate.education:
            if edu.institution:
                institution_names.add(edu.institution.strip())

        # Sort names to ensure deterministic mapping
        sorted_companies = sorted(list(company_names), key=len, reverse=True)
        sorted_institutions = sorted(list(institution_names), key=len, reverse=True)

        # 2. Build mapping dictionaries
        company_map: Dict[str, str] = {}
        for idx, co in enumerate(sorted_companies):
            letter = chr(ord('A') + idx)
            company_map[co] = f"Company {letter}"

        institution_map: Dict[str, str] = {}
        for idx, inst in enumerate(sorted_institutions):
            letter = chr(ord('A') + idx)
            institution_map[inst] = f"University {letter}"

        # Get candidate name tokens to scrub
        name_tokens = []
        name_str = candidate.profile.anonymized_name.strip()
        if name_str:
            name_tokens.append(name_str)
            # Add split name tokens (e.g. "Ira", "Vora") if they are long enough
            for token in name_str.split():
                if len(token) > 2:
                    name_tokens.append(token)
        # Sort name tokens by length descending to match full name first
        name_tokens.sort(key=len, reverse=True)

        # 3. Text scrubbing helper
        def scrub_text(text: str) -> str:
            if not text:
                return text
                
            # Replace email and phone numbers
            text = EMAIL_REGEX.sub("[Scrubbed Email]", text)
            text = PHONE_REGEX.sub("[Scrubbed Phone]", text)

            # Replace candidate names
            for token in name_tokens:
                pattern = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
                text = pattern.sub("Candidate", text)

            # Replace company names
            for co, anon in company_map.items():
                pattern = re.compile(r"\b" + re.escape(co) + r"\b", re.IGNORECASE)
                text = pattern.sub(anon, text)

            # Replace university/institution names
            for inst, anon in institution_map.items():
                pattern = re.compile(r"\b" + re.escape(inst) + r"\b", re.IGNORECASE)
                text = pattern.sub(anon, text)

            return text

        # 4. Perform replacements on candidate fields
        # Anonymize profile
        anon_profile = cand_dict["profile"]
        anon_profile["anonymized_name"] = f"Candidate {candidate.candidate_id}"
        anon_profile["current_company"] = company_map.get(
            candidate.profile.current_company, "Anonymized Company"
        )
        anon_profile["headline"] = scrub_text(candidate.profile.headline)
        anon_profile["summary"] = scrub_text(candidate.profile.summary)

        # Anonymize career history
        anon_history = []
        for i, role in enumerate(cand_dict["career_history"]):
            raw_role = candidate.career_history[i]
            role["company"] = company_map.get(raw_role.company, "Anonymized Company")
            role["description"] = scrub_text(raw_role.description)
            # Keep dates (dates are start/end objects in model_dump)
            if role["start_date"] and not isinstance(role["start_date"], str):
                role["start_date"] = role["start_date"].isoformat()
            if role["end_date"] and not isinstance(role["end_date"], str):
                role["end_date"] = role["end_date"].isoformat()
            anon_history.append(role)
        cand_dict["career_history"] = anon_history

        # Anonymize education
        anon_edu = []
        for i, edu in enumerate(cand_dict["education"]):
            raw_edu = candidate.education[i]
            edu["institution"] = institution_map.get(raw_edu.institution, "Anonymized University")
            anon_edu.append(edu)
        cand_dict["education"] = anon_edu

        # Format dates in redrob signals
        sig = cand_dict["redrob_signals"]
        if sig["signup_date"] and not isinstance(sig["signup_date"], str):
            sig["signup_date"] = sig["signup_date"].isoformat()
        if sig["last_active_date"] and not isinstance(sig["last_active_date"], str):
            sig["last_active_date"] = sig["last_active_date"].isoformat()

        return {
            "anonymous_candidate": cand_dict
        }
