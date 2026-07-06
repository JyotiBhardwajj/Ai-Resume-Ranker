import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.jd_parser import JDParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-description", tags=["Job Description"])


class JDAnalyzeRequest(BaseModel):
    """
    Pydantic request model for analyzing a job description.
    """
    job_description: str = Field(
        ..., 
        description="The raw job description text to parse and analyze.",
        examples=["Strong Python backend engineer with 6+ years experience, skilled in embeddings, Milvus vector database, Kafka, Airflow, and search evaluation frameworks like NDCG."]
    )


class JDAnalyzeResponse(BaseModel):
    """
    Pydantic response model containing parsed job description details.
    """
    role: str = Field(
        ..., 
        description="The extracted or inferred job title/role.",
        examples=["Senior Applied ML/Search Ranking Engineer"]
    )
    skills: List[str] = Field(
        ..., 
        description="List of recognized technical skills or domain categories.",
        examples=["Python", "Embeddings & Semantic Search", "Vector Databases & Hybrid Search", "Ranking Evaluation", "Apache Airflow", "Apache Kafka"]
    )
    experience_required: int = Field(
        ..., 
        description="Minimum years of professional experience required for the role.",
        examples=[6]
    )
    domain: str = Field(
        ..., 
        description="Primary technology/professional domain identified.",
        examples=["Search & Ranking"]
    )


@router.post(
    "/analyze",
    response_model=JDAnalyzeResponse,
    summary="Parse and analyze job description metadata.",
)
def analyze_job_description(request: JDAnalyzeRequest) -> JDAnalyzeResponse:
    """
    HTTP POST endpoint to parse raw job description text and extract structured metadata:
    - role/title
    - list of standard skills/categories
    - minimum years of experience required
    - primary domain category
    """
    if not request.job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description text cannot be empty or whitespace.",
        )

    try:
        # Perform extraction
        role = JDParser.extract_role(request.job_description)
        skills = JDParser.extract_skills(request.job_description)
        experience_required = JDParser.extract_experience_required(request.job_description)
        domain = JDParser.extract_domain(request.job_description)

        return JDAnalyzeResponse(
            role=role,
            skills=skills,
            experience_required=experience_required,
            domain=domain,
        )
    except Exception as e:
        logger.exception("Error occurred while analyzing job description")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing the job description: {str(e)}",
        )
