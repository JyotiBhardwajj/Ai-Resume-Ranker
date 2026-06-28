import json
import logging
from typing import Any, Generator, List, Union
from pydantic import ValidationError

from backend.models.candidate import Candidate

logger = logging.getLogger(__name__)


class CandidateParser:
    """
    Parser service to load, validate, normalize, and instantiate Candidate objects
    from various JSON representations, handling anomalies and missing fields.
    """

    @staticmethod
    def normalize_profile(data: dict) -> dict:
        """
        Normalizes profile fields (strips whitespace, handles formatting).

        Args:
            data: Candidate dictionary.

        Returns:
            Dictionary with normalized profile fields.
        """
        profile = data.get("profile", {})
        if not isinstance(profile, dict):
            return data

        # Normalize strings: strip whitespace
        for field in [
            "anonymized_name",
            "headline",
            "summary",
            "location",
            "country",
            "current_title",
            "current_company",
            "current_industry",
        ]:
            if field in profile and isinstance(profile[field], str):
                profile[field] = profile[field].strip()

        # Enforce normalized profile dict back into data
        data["profile"] = profile
        return data

    @staticmethod
    def normalize_collections(data: dict) -> dict:
        """
        Ensures lists like certifications and languages default to empty arrays
        if they are missing or null, and trims all string fields in items.

        Args:
            data: Candidate dictionary.

        Returns:
            Dictionary with normalized collections.
        """
        for field in ["career_history", "education", "skills", "certifications", "languages"]:
            if field not in data or data[field] is None:
                data[field] = []
            elif isinstance(data[field], list):
                # Trim string values inside items
                for item in data[field]:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if isinstance(v, str):
                                item[k] = v.strip()
        return data

    @classmethod
    def normalize_custom_candidate_fields(cls, data: dict) -> dict:
        """
        Detects custom/uploaded candidates (UUID-based or missing required signals)
        and normalizes their fields to match the production schema requirements.
        """
        # 1. Identify if candidate is custom (UUID format or missing redrob_signals)
        cand_id = data.get("candidate_id")
        is_custom = False
        if cand_id and (not str(cand_id).startswith("CAND_") or len(str(cand_id)) == 36):
            is_custom = True
        if "redrob_signals" not in data or data["redrob_signals"] is None:
            is_custom = True
            
        if not is_custom:
            return data

        # 2. Normalize profile
        profile = data.get("profile")
        if not isinstance(profile, dict):
            profile = {}
        
        profile.setdefault("anonymized_name", "Anonymous Candidate")
        profile.setdefault("headline", "Professional Candidate")
        profile.setdefault("summary", "")
        profile.setdefault("location", "Unknown")
        profile.setdefault("country", "India")
        profile.setdefault("years_of_experience", 0.0)
        profile.setdefault("current_title", "Professional")
        profile.setdefault("current_company", "Unknown")
        profile.setdefault("current_company_size", "11-50")
        profile.setdefault("current_industry", "Technology")
        
        # Validate years_of_experience format
        try:
            profile["years_of_experience"] = float(profile["years_of_experience"])
        except (ValueError, TypeError):
            profile["years_of_experience"] = 0.0
            
        # Ensure company size bracket is valid
        allowed_sizes = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
        if profile.get("current_company_size") not in allowed_sizes:
            profile["current_company_size"] = "11-50"
            
        data["profile"] = profile

        # 3. Normalize career history
        history = data.get("career_history")
        if not isinstance(history, list) or not history:
            # Must have at least 1 record
            history = [{
                "company": profile["current_company"],
                "title": profile["current_title"],
                "start_date": "2023-01-01",
                "end_date": None,
                "duration_months": int(profile["years_of_experience"] * 12) or 12,
                "is_current": True,
                "industry": profile["current_industry"],
                "company_size": profile["current_company_size"],
                "description": profile["summary"] or "Employment record"
            }]
        else:
            normalized_history = []
            for item in history:
                if not isinstance(item, dict):
                    continue
                # Map company_name to company
                company = item.get("company") or item.get("company_name") or "Unknown Company"
                title = item.get("title") or "Software Engineer"
                
                # Date parsing helper
                def parse_to_iso_date(dt_val, default_val):
                    if not dt_val or not isinstance(dt_val, str):
                        return default_val
                    dt_str = dt_val.strip()
                    if len(dt_str) == 7 and dt_str[4] == '-': # YYYY-MM
                        return f"{dt_str}-01"
                    if len(dt_str) == 4 and dt_str.isdigit(): # YYYY
                        return f"{dt_str}-01-01"
                    if len(dt_str) >= 10:
                        return dt_str[:10]
                    return default_val

                start_date_str = parse_to_iso_date(item.get("start_date"), "2020-01-01")
                
                # End date handling
                end_val = item.get("end_date")
                if not end_val or str(end_val).lower() in ["current", "present", "none", "null"]:
                    end_date_str = None
                    is_current = True
                else:
                    end_date_str = parse_to_iso_date(end_val, "2021-01-01")
                    is_current = False
                    
                # Safe date check (start_date must be <= end_date)
                if end_date_str and start_date_str > end_date_str:
                    start_date_str, end_date_str = end_date_str, start_date_str

                # Duration
                duration = item.get("duration_months")
                if duration is None:
                    duration = 12 # Default fallback
                else:
                    try:
                        duration = int(duration)
                    except (ValueError, TypeError):
                        duration = 12

                industry = item.get("industry") or profile["current_industry"]
                company_size = item.get("company_size") or profile["current_company_size"]
                if company_size not in allowed_sizes:
                    company_size = "11-50"
                    
                description = item.get("description") or "Employment history record"
                
                normalized_history.append({
                    "company": company,
                    "title": title,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "duration_months": duration,
                    "is_current": is_current,
                    "industry": industry,
                    "company_size": company_size,
                    "description": description
                })
            history = normalized_history if normalized_history else history
            
        data["career_history"] = history

        # 4. Normalize education
        education = data.get("education")
        if isinstance(education, list):
            normalized_edu = []
            for item in education:
                if not isinstance(item, dict):
                    continue
                institution = item.get("institution") or item.get("school_name") or "Unknown School"
                degree = item.get("degree") or item.get("degree_name") or "Degree"
                
                # Try to extract major/field
                field = item.get("field_of_study")
                if not field:
                    if "in " in degree:
                        field = degree.split("in ", 1)[1]
                    else:
                        field = "Computer Science" # Default fallback
                
                grad_year = item.get("year_of_graduation") or item.get("end_year")
                try:
                    end_year = int(grad_year) if grad_year else 2024
                except (ValueError, TypeError):
                    end_year = 2024
                    
                start_year = item.get("start_year")
                try:
                    start_year = int(start_year) if start_year else (end_year - 4)
                except (ValueError, TypeError):
                    start_year = end_year - 4
                    
                # Constrain start_year/end_year to valid bounds
                start_year = max(1970, min(2030, start_year))
                end_year = max(1970, min(2035, end_year))
                if start_year > end_year:
                    start_year = end_year
                    
                grade = item.get("grade")
                tier = item.get("tier") or "unknown"
                if tier not in ["tier_1", "tier_2", "tier_3", "tier_4", "unknown"]:
                    tier = "unknown"
                    
                normalized_edu.append({
                    "institution": institution,
                    "degree": degree,
                    "field_of_study": field,
                    "start_year": start_year,
                    "end_year": end_year,
                    "grade": grade,
                    "tier": tier
                })
            data["education"] = normalized_edu

        # 5. Normalize skills
        skills = data.get("skills")
        if isinstance(skills, list):
            normalized_skills = []
            for item in skills:
                if isinstance(item, str):
                    normalized_skills.append({
                        "name": item,
                        "proficiency": "advanced",
                        "endorsements": 5,
                        "duration_months": 12
                    })
                elif isinstance(item, dict):
                    name = item.get("name")
                    if not name:
                        continue
                    prof = item.get("proficiency") or "advanced"
                    if prof not in ["beginner", "intermediate", "advanced", "expert"]:
                        prof = "advanced"
                    try:
                        endorsements = int(item.get("endorsements") or 5)
                    except (ValueError, TypeError):
                        endorsements = 5
                    try:
                        dur = item.get("duration_months")
                        dur = int(dur) if dur is not None else 12
                    except (ValueError, TypeError):
                        dur = 12
                    normalized_skills.append({
                        "name": name,
                        "proficiency": prof,
                        "endorsements": endorsements,
                        "duration_months": dur
                    })
            data["skills"] = normalized_skills

        # 6. Normalize certifications and languages to empty list if missing
        data.setdefault("certifications", [])
        data.setdefault("languages", [])

        # 7. Inject simulated redrob_signals
        if "redrob_signals" not in data or data["redrob_signals"] is None:
            data["redrob_signals"] = {
                "profile_completeness_score": 85.0,
                "signup_date": "2025-01-01",
                "last_active_date": "2025-06-01",
                "open_to_work_flag": True,
                "profile_views_received_30d": 15,
                "applications_submitted_30d": 3,
                "recruiter_response_rate": 0.85,
                "avg_response_time_hours": 12.0,
                "skill_assessment_scores": {},
                "connection_count": 80,
                "endorsements_received": 12,
                "notice_period_days": 30,
                "expected_salary_range_inr_lpa": {
                    "min": 8.0,
                    "max": 18.0
                },
                "preferred_work_mode": "remote",
                "willing_to_relocate": True,
                "github_activity_score": 60.0,
                "search_appearance_30d": 20,
                "saved_by_recruiters_30d": 3,
                "interview_completion_rate": 0.95,
                "offer_acceptance_rate": 0.75,
                "verified_email": True,
                "verified_phone": True,
                "linkedin_connected": False
            }
            
        return data

    @classmethod
    def parse_dict(cls, data: dict) -> Candidate:
        """
        Parses a candidate dictionary, normalizes fields, and instantiates
        a validated Candidate Pydantic model.

        Args:
            data: Raw dictionary of candidate data.

        Returns:
            Validated Candidate Pydantic model instance.

        Raises:
            ValidationError: If model validation rules are violated.
        """
        # Deep copy to avoid mutating the original data structure
        normalized_data = json.loads(json.dumps(data))
        
        # Run custom candidate normalization if applicable
        normalized_data = cls.normalize_custom_candidate_fields(normalized_data)
        
        # Run standard normalizations
        normalized_data = cls.normalize_profile(normalized_data)
        normalized_data = cls.normalize_collections(normalized_data)

        # Let the Pydantic model validate and initialize
        return Candidate.model_validate(normalized_data)

    @classmethod
    def parse_json_str(cls, json_str: str) -> Candidate:
        """
        Parses a candidate JSON string, normalizes fields, and returns a Candidate object.

        Args:
            json_str: Raw JSON string.

        Returns:
            Validated Candidate Pydantic model instance.

        Raises:
            ValueError: If JSON decode fails.
            ValidationError: If validation fails.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string format: {e}") from e
        return cls.parse_dict(data)

    @classmethod
    def load_from_json_file(
        cls, file_path: str, ignore_validation_errors: bool = False
    ) -> List[Candidate]:
        """
        Loads a list of Candidates from a standard JSON array file.

        Args:
            file_path: Absolute path to the JSON file.
            ignore_validation_errors: If True, invalid candidates are skipped.

        Returns:
            List of validated Candidate objects.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON file root must be a list of candidate objects.")
            
        candidates = []
        for i, item in enumerate(data):
            try:
                candidates.append(cls.parse_dict(item))
            except ValidationError as e:
                if ignore_validation_errors:
                    logger.warning(f"Skipping candidate at index {i} due to validation error: {e}")
                    continue
                logger.error(f"Validation failed for candidate at index {i}: {e}")
                raise
        return candidates

    @classmethod
    def iterate_jsonl_file(
        cls, file_path: str, ignore_validation_errors: bool = False
    ) -> Generator[Candidate, None, None]:
        """
        Generator to stream candidates from a large JSON Lines (.jsonl) file.
        Memory-efficient for production scale.

        Args:
            file_path: Absolute path to the JSONL file.
            ignore_validation_errors: If True, invalid candidates (honeypots) are skipped.

        Yields:
            Validated Candidate objects sequentially.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    yield cls.parse_json_str(clean_line)
                except ValidationError as e:
                    if ignore_validation_errors:
                        logger.warning(f"Skipping line {line_num} due to validation error: {e}")
                        continue
                    raise
