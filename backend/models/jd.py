from pydantic import BaseModel, Field
from typing import List, Optional

class JobDescription(BaseModel):
    """
    Model representing a structured Job Description.
    """
    role: str = Field(..., description="The main job title or role.")
    domain: Optional[str] = Field(None, description="The industry or domain of the job.")
    min_experience_years: float = Field(0.0, description="Minimum required years of experience.")
    max_experience_years: Optional[float] = Field(None, description="Maximum allowed years of experience, if any.")
    required_skills: List[str] = Field(..., description="List of explicitly required skills.")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="List of optional or preferred skills.")
    must_have_requirements: List[str] = Field(default_factory=list, description="High-level absolute constraints or requirements.")
    role_type: str = Field(..., description="Type of role, e.g. Full-time, Contract.")
