import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from backend.models.candidate import Candidate, CareerHistory

logger = logging.getLogger(__name__)


class CareerSummary(BaseModel):
    """
    Model representing parsed career trajectory analytics for a candidate.
    """
    total_experience_months: int = Field(
        ..., ge=0, description="Sum of durations across all roles in months."
    )
    total_experience_years: float = Field(
        ..., ge=0.0, description="Total experience scaled in years."
    )
    number_of_roles: int = Field(
        ..., ge=0, description="Total number of distinct roles held."
    )
    number_of_company_changes: int = Field(
        ..., ge=0, description="Number of times the candidate transitioned to a different company."
    )
    promotions_count: int = Field(
        ..., ge=0, description="Number of internal promotions (same company, higher seniority title)."
    )
    leadership_roles_count: int = Field(
        ..., ge=0, description="Number of roles with leadership responsibilities."
    )
    leadership_duration_months: int = Field(
        ..., ge=0, description="Total months spent in leadership positions."
    )
    initial_role_complexity: int = Field(
        ..., ge=1, le=4, description="Functional complexity level of the earliest role."
    )
    latest_role_complexity: int = Field(
        ..., ge=1, le=4, description="Functional complexity level of the latest role."
    )
    complexity_progression: int = Field(
        ..., description="Difference in functional complexity (latest_complexity - initial_complexity)."
    )
    is_currently_employed: bool = Field(
        ..., description="Indicates if the candidate has an active current role."
    )
    current_title: Optional[str] = Field(
        None, description="Title of the candidate's current role if employed."
    )
    current_company: Optional[str] = Field(
        None, description="Company name of the candidate's current role if employed."
    )


def get_seniority_level(title: str) -> int:
    """
    Maps a job title to a numeric seniority level (0-5) using keyword parsing.

    Args:
        title: Job title string.

    Returns:
        Integer seniority level (0 = Intern, 5 = Executive/CTO).
    """
    title_lower = title.lower()
    
    # Level 0: Interns
    if any(k in title_lower for k in ["intern", "trainee", "co-op", "apprentice"]):
        return 0
        
    # Level 5: Executives
    if any(k in title_lower for k in ["director", "vp", "vice president", "cto", "cxo", "architect (chief)", "founder"]):
        return 5
        
    # Level 4: Lead / Principal / Manager
    if any(k in title_lower for k in ["lead", "staff", "principal", "manager", "supervisor"]):
        return 4
        
    # Level 3: Senior
    if any(k in title_lower for k in ["senior", "sr", "l3", "specialist (senior)"]):
        return 3
        
    # Level 1: Junior
    if any(k in title_lower for k in ["junior", "jr", "associate", "analyst (entry)", "l1", "assistant"]):
        return 1
        
    # Level 2: Mid-level (Default)
    return 2


def get_role_complexity(title: str) -> int:
    """
    Maps a job title to a functional complexity rank (1-4).

    Args:
        title: Job title string.

    Returns:
        Integer complexity level (1 = Operations/Support, 4 = Advanced Tech/AI).
    """
    title_lower = title.lower()
    
    # Level 4: Advanced Tech / AI / Architecture
    if any(k in title_lower for k in ["machine learning", "ml", "ai", "data scientist", "deep learning", "nlp", "computer vision", "architect"]):
        return 4
        
    # Level 3: Core Systems & Backend
    if any(k in title_lower for k in ["backend", "fullstack", "devops", "systems", "infrastructure", "cloud", "database", "data engineer"]):
        return 3
        
    # Level 2: Front-Facing Execution & Testing
    if any(k in title_lower for k in ["frontend", "qa", "tester", "quality assurance", "designer", "ui/ux", "writer"]):
        return 2
        
    # Level 1: Support / Operations (Default)
    return 1


def is_leadership_role(title: str, description: str) -> bool:
    """
    Detects if a role carries leadership, management, or technical steering weight.

    Args:
        title: Job title string.
        description: Job description text.

    Returns:
        Boolean indicating leadership status.
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # Title indicators
    leadership_titles = ["lead", "manager", "director", "vp", "president", "head", "principal", "founder", "cto", "chief", "supervisor"]
    if any(k in title_lower for k in leadership_titles):
        return True
        
    # Description indicators
    leadership_descriptions = [
        "managed a team", "led a team", "mentored junior", 
        "headed the", "directed the", "supervised a", 
        "technical direction", "architecture steering"
    ]
    if any(k in desc_lower for k in leadership_descriptions):
        return True
        
    return False


def parse_career_history(
    career_history: List[Union[dict, CareerHistory]]
) -> CareerSummary:
    """
    Analyzes a list of career history entries and computes career summary metrics.

    Args:
        career_history: List of CareerHistory models or raw dictionaries.

    Returns:
        A CareerSummary object containing calculated metrics.
    """
    # 1. Standardize to dicts and sort chronologically (oldest first)
    standardized_roles: List[dict] = []
    for role in career_history:
        if isinstance(role, BaseModel):
            standardized_roles.append(role.model_dump())
        else:
            standardized_roles.append(role)
            
    # Sort by start_date
    standardized_roles.sort(key=lambda x: str(x.get("start_date", "")))
    
    number_of_roles = len(standardized_roles)
    if number_of_roles == 0:
        return CareerSummary(
            total_experience_months=0,
            total_experience_years=0.0,
            number_of_roles=0,
            number_of_company_changes=0,
            promotions_count=0,
            leadership_roles_count=0,
            leadership_duration_months=0,
            initial_role_complexity=1,
            latest_role_complexity=1,
            complexity_progression=0,
            is_currently_employed=False
        )

    # 2. Compute metrics
    total_experience_months = 0
    company_changes = 0
    promotions = 0
    leadership_count = 0
    leadership_duration = 0
    is_currently_employed = False
    current_title = None
    current_company = None

    for i, role in enumerate(standardized_roles):
        duration = int(role.get("duration_months", 0))
        total_experience_months += duration
        
        # Check current employment status
        if role.get("is_current", False):
            is_currently_employed = True
            current_title = role.get("title")
            current_company = role.get("company")
            
        # Leadership check
        title = role.get("title", "")
        desc = role.get("description", "")
        if is_leadership_role(title, desc):
            leadership_count += 1
            leadership_duration += duration

        # Transition checks (only if not the last role in sorted order)
        if i < number_of_roles - 1:
            next_role = standardized_roles[i+1]
            co1 = role.get("company", "").lower().strip()
            co2 = next_role.get("company", "").lower().strip()
            
            if co1 != co2:
                company_changes += 1
            else:
                # Promotion check: same company, and seniority level increased
                sl1 = get_seniority_level(title)
                sl2 = get_seniority_level(next_role.get("title", ""))
                if sl2 > sl1:
                    promotions += 1

    total_experience_years = round(total_experience_months / 12.0, 1)

    # 3. Role progression (earliest vs latest functional complexity)
    initial_complexity = get_role_complexity(standardized_roles[0].get("title", ""))
    latest_complexity = get_role_complexity(standardized_roles[-1].get("title", ""))
    complexity_progression = latest_complexity - initial_complexity

    return CareerSummary(
        total_experience_months=total_experience_months,
        total_experience_years=total_experience_years,
        number_of_roles=number_of_roles,
        number_of_company_changes=company_changes,
        promotions_count=promotions,
        leadership_roles_count=leadership_count,
        leadership_duration_months=leadership_duration,
        initial_role_complexity=initial_complexity,
        latest_role_complexity=latest_complexity,
        complexity_progression=complexity_progression,
        is_currently_employed=is_currently_employed,
        current_title=current_title,
        current_company=current_company
    )


def extract_from_candidate(candidate: Candidate) -> CareerSummary:
    """
    Extracts career summary analytics directly from a validated Candidate model.

    Args:
        candidate: Validated Candidate model instance.

    Returns:
        CareerSummary object.
    """
    return parse_career_history(candidate.career_history)
