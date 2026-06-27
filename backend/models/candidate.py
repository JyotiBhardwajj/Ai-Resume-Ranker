from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Profile(BaseModel):
    """
    Model representing basic demographic and professional overview of a candidate.
    """
    anonymized_name: str = Field(..., description="Anonymized full name.")
    headline: str = Field(..., description="One-line professional headline.")
    summary: str = Field(..., description="Multi-sentence professional summary.")
    location: str = Field(..., description="City, region/state.")
    country: str = Field(..., description="Country of residence.")
    years_of_experience: float = Field(
        ..., ge=0.0, le=50.0, description="Total years of professional experience."
    )
    current_title: str = Field(..., description="Current job title.")
    current_company: str = Field(..., description="Current employer company name.")
    current_company_size: str = Field(
        ...,
        pattern=r"^(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)$",
        description="Employee size bracket of the current company.",
    )
    current_industry: str = Field(..., description="Industry of the current company.")


class CareerHistory(BaseModel):
    """
    Model representing a single professional role / employment record.
    """
    company: str = Field(..., description="Name of the employer company.")
    title: str = Field(..., description="Stated job title for this role.")
    start_date: date = Field(..., description="Date the candidate started this role.")
    end_date: Optional[date] = Field(
        None, description="Date the candidate left this role. Null if current."
    )
    duration_months: int = Field(
        ..., ge=0, description="Total duration of the role in months."
    )
    is_current: bool = Field(
        ..., description="Indicates if the candidate is currently employed here."
    )
    industry: str = Field(..., description="Industry of the company.")
    company_size: str = Field(
        ...,
        pattern=r"^(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)$",
        description="Employee size bracket of the company.",
    )
    description: str = Field(
        ..., description="Role responsibilities, accomplishments, and tech stack."
    )

    @model_validator(mode="after")
    def validate_dates_and_current_status(self) -> "CareerHistory":
        """
        Validates date order consistency and aligns end_date with is_current.
        """
        if self.is_current and self.end_date is not None:
            raise ValueError("Role is marked as current, but end_date is provided.")
        if not self.is_current and self.end_date is None:
            raise ValueError("Role is not marked as current, but end_date is missing.")
        if self.end_date and self.start_date > self.end_date:
            raise ValueError(f"start_date ({self.start_date}) cannot be after end_date ({self.end_date}).")
        return self


class Education(BaseModel):
    """
    Model representing an academic qualification or university background.
    """
    institution: str = Field(..., description="Name of the academic institution.")
    degree: str = Field(..., description="Degree earned.")
    field_of_study: str = Field(..., description="Field or major of study.")
    start_year: int = Field(..., ge=1970, le=2030, description="Academic starting year.")
    end_year: int = Field(..., ge=1970, le=2035, description="Academic completion year.")
    grade: Optional[str] = Field(
        None, description="Grade, GPA, class or percentage scored."
    )
    tier: Optional[str] = Field(
        "unknown",
        pattern=r"^(tier_1|tier_2|tier_3|tier_4|unknown)$",
        description="Institution tier based on prestige.",
    )

    @model_validator(mode="after")
    def validate_academic_years(self) -> "Education":
        """
        Ensures start_year is less than or equal to end_year.
        """
        if self.start_year > self.end_year:
            raise ValueError(f"start_year ({self.start_year}) cannot be after end_year ({self.end_year}).")
        return self


class Skill(BaseModel):
    """
    Model representing a candidate's technical or professional skill.
    """
    name: str = Field(..., description="Name of the skill.")
    proficiency: str = Field(
        ...,
        pattern=r"^(beginner|intermediate|advanced|expert)$",
        description="Proficiency level on the skill.",
    )
    endorsements: int = Field(
        ..., ge=0, description="Total skill endorsements received."
    )
    duration_months: Optional[int] = Field(
        None, ge=0, description="Optional months of hands-on usage."
    )


class Certification(BaseModel):
    """
    Model representing professional certifications.
    """
    name: str = Field(..., description="Name of the certification.")
    issuer: str = Field(..., description="Organization issuing the certification.")
    year: int = Field(..., description="Year the certification was issued.")


class Language(BaseModel):
    """
    Model representing language capabilities.
    """
    language: str = Field(..., description="Language name.")
    proficiency: str = Field(
        ...,
        pattern=r"^(basic|conversational|professional|native)$",
        description="Proficiency level.",
    )


class ExpectedSalaryRange(BaseModel):
    """
    Expected salary range in INR Lakhs Per Annum.
    """
    min: float = Field(..., ge=0.0, description="Minimum salary expected in INR LPA.")
    max: float = Field(..., ge=0.0, description="Maximum salary expected in INR LPA.")

    @model_validator(mode="after")
    def validate_salary_range(self) -> "ExpectedSalaryRange":
        """
        Ensures minimum expected salary does not exceed maximum. Swaps them if they are out of order.
        """
        if self.min > self.max:
            self.min, self.max = self.max, self.min
        return self


class RedrobSignals(BaseModel):
    """
    Model for simulated Redrob platform behavioral activity signals.
    """
    profile_completeness_score: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage score of completeness."
    )
    signup_date: date = Field(..., description="Date candidate registered.")
    last_active_date: date = Field(..., description="Date candidate last logged in.")
    open_to_work_flag: bool = Field(..., description="Is seeking work.")
    profile_views_received_30d: int = Field(..., ge=0)
    applications_submitted_30d: int = Field(..., ge=0)
    recruiter_response_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Response rate to recruiter messages."
    )
    avg_response_time_hours: float = Field(..., ge=0.0)
    skill_assessment_scores: Dict[str, float] = Field(
        default_factory=dict, description="Skill scores completed on platform."
    )
    connection_count: int = Field(..., ge=0)
    endorsements_received: int = Field(..., ge=0)
    notice_period_days: int = Field(..., ge=0, le=180)
    expected_salary_range_inr_lpa: ExpectedSalaryRange = Field(
        ..., description="Salary expectations range in INR LPA."
    )
    preferred_work_mode: str = Field(
        ...,
        pattern=r"^(remote|hybrid|onsite|flexible)$",
        description="Stated work-mode preference.",
    )
    willing_to_relocate: bool = Field(..., description="Is willing to relocate.")
    github_activity_score: float = Field(
        ..., ge=-1.0, le=100.0, description="GitHub score, -1 if not linked."
    )
    search_appearance_30d: int = Field(..., ge=0)
    saved_by_recruiters_30d: int = Field(..., ge=0)
    interview_completion_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Rate of interviews attended."
    )
    offer_acceptance_rate: float = Field(
        ..., ge=-1.0, le=1.0, description="Rate of offers accepted, -1 if no history."
    )
    verified_email: bool = Field(...)
    verified_phone: bool = Field(...)
    linkedin_connected: bool = Field(...)

    @model_validator(mode="after")
    def validate_activity_dates(self) -> "RedrobSignals":
        """
        Validates order of platform signup and last active activity. Swaps them if they are out of order.
        """
        if self.signup_date > self.last_active_date:
            self.signup_date, self.last_active_date = self.last_active_date, self.signup_date
        return self


class Candidate(BaseModel):
    """
    Top-level model representing a full candidate profile.
    """
    candidate_id: str = Field(
        ..., pattern=r"^(CAND_[0-9]{7}|[a-fA-F0-9\-]{36})$", description="Unique identifier format CAND_XXXXXXX or UUID."
    )
    profile: Profile = Field(..., description="Candidate profile details.")
    career_history: List[CareerHistory] = Field(
        ..., min_length=1, max_length=10, description="Career history roles list."
    )
    education: List[Education] = Field(
        default_factory=list, max_length=5, description="Academic history records."
    )
    skills: List[Skill] = Field(
        default_factory=list, description="Skill profile records."
    )
    certifications: List[Certification] = Field(
        default_factory=list, description="Professional certifications list."
    )
    languages: List[Language] = Field(
        default_factory=list, description="Languages spoken."
    )
    redrob_signals: RedrobSignals = Field(
        ..., description="Redrob behavioral engagement signals."
    )
