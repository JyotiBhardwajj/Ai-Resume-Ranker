import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.candidate_parser import CandidateParser
from backend.services.ranking_engine import RankingEngine, RankedCandidate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ranking"])


class RankRequest(BaseModel):
    """
    Pydantic request model for candidate ranking.
    """
    job_description: str = Field(
        ..., description="The job description text to rank candidates against."
    )
    limit: Optional[int] = Field(
        10, ge=1, le=100, description="Number of top candidates to return."
    )


class RankResponse(BaseModel):
    """
    Pydantic response model containing list of ranked candidates.
    """
    candidates: List[RankedCandidate] = Field(
        ..., description="List of ranked candidates sorted by highest fit score."
    )


@router.post(
    "/rank",
    response_model=RankResponse,
    summary="Rank candidates against a job description.",
)
def rank_candidates(request: RankRequest) -> RankResponse:
    """
    HTTP POST endpoint to load candidates, score them across semantic similarity,
    skills coverage, and career history relevance, and return the top-N ranked matches.
    """
    # Resolve the candidate dataset location
    candidate_path = "data/sample_candidates.json"

    if not os.path.exists(candidate_path):
        logger.error(f"Candidate dataset not found at: {candidate_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Candidate dataset not found at {candidate_path}.",
        )

    try:
        # Load and parse candidates, skipping invalid/honeypot profiles
        candidates = CandidateParser.load_from_json_file(
            candidate_path, ignore_validation_errors=True
        )
    except Exception as e:
        logger.error(f"Failed loading candidate profiles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed loading candidate profiles from database: {str(e)}",
        )

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No valid candidate profiles available to rank.",
        )

    try:
        # Execute the ranking pipeline
        engine = RankingEngine()
        ranked_list = engine.rank_candidates(candidates, request.job_description)
        
        # Apply output limit
        top_candidates = ranked_list[: request.limit]
        return RankResponse(candidates=top_candidates)
    except Exception as e:
        logger.exception("Ranking execution error")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during candidate ranking: {str(e)}",
        )
