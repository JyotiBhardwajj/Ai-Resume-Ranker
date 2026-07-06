import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.models.candidate import Candidate, CareerHistory, Skill
from backend.services.candidate_parser import CandidateParser
from backend.services.career_parser import CareerSummary, extract_from_candidate as extract_career_summary
from backend.services.skills_extractor import SkillsExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

# Path to local database file
CANDIDATE_DATA_PATH = "data/sample_candidates.json"


class CandidateDetailResponse(BaseModel):
    """
    Response model detailing a candidate's structured profile,
    standardized skills, raw experience, and analytical career summary.
    """
    candidate: Candidate = Field(..., description="The core candidate profile details.")
    skills: List[Skill] = Field(..., description="Deduplicated and normalized technical skills list.")
    experience: List[CareerHistory] = Field(..., description="Detailed employment history.")
    career_summary: CareerSummary = Field(..., description="Structured career trajectory metrics.")


class CandidateListResponse(BaseModel):
    """
    Response model representing a paginated candidate profile listing.
    """
    total: int = Field(..., description="Total valid candidates in database.")
    limit: int = Field(..., description="Pagination limit applied.")
    offset: int = Field(..., description="Pagination offset applied.")
    results: List[Candidate] = Field(..., description="List of validated candidates on the current page.")


def _get_candidates_database() -> List[Candidate]:
    """
    Helper to fetch and parse candidate profiles from local storage.
    """
    if not os.path.exists(CANDIDATE_DATA_PATH):
        logger.error(f"Candidate dataset file not found at: {CANDIDATE_DATA_PATH}")
        raise HTTPException(
            status_code=500,
            detail="System Database Error: Candidate dataset is missing.",
        )
    try:
        # Load candidate profiles, automatically filtering out honeypots
        return CandidateParser.load_from_json_file(
            CANDIDATE_DATA_PATH, ignore_validation_errors=True
        )
    except Exception as e:
        logger.error(f"Failed loading candidate database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed loading candidate database: {str(e)}",
        )


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
    summary="Get detailed candidate profile by ID.",
)
def get_candidate_detail(candidate_id: str) -> CandidateDetailResponse:
    """
    Retrieves full details for a single candidate including their validated profile,
    normalized skills set, raw career history, and parsed career metrics summary.
    """
    candidates = _get_candidates_database()
    
    # Search for candidate by ID
    target_candidate = None
    for cand in candidates:
        if cand.candidate_id == candidate_id:
            target_candidate = cand
            break

    if not target_candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate with ID '{candidate_id}' not found.",
        )

    try:
        # Extract normalized skills and career summaries
        normalized_skills = SkillsExtractor.extract_from_candidate(target_candidate)
        career_summary = extract_career_summary(target_candidate)

        return CandidateDetailResponse(
            candidate=target_candidate,
            skills=normalized_skills,
            experience=target_candidate.career_history,
            career_summary=career_summary,
        )
    except Exception as e:
        logger.error(f"Error compiling candidate details for {candidate_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error compiling candidate details: {str(e)}",
        )


@router.get(
    "",
    response_model=CandidateListResponse,
    summary="List candidates with pagination support.",
)
def list_candidates(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return per page."),
    offset: int = Query(0, ge=0, description="Offset index to start returning results from."),
) -> CandidateListResponse:
    """
    Returns a paginated listing of validated candidate profiles from the candidate pool.
    """
    candidates = _get_candidates_database()
    total_count = len(candidates)
    
    # Slice database list
    sliced_candidates = candidates[offset : offset + limit]

    return CandidateListResponse(
        total=total_count,
        limit=limit,
        offset=offset,
        results=sliced_candidates,
    )
