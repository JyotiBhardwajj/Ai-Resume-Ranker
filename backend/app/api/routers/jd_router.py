from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backend.services.jd_intelligence.jd_parser import JDParser
from backend.services.jd_intelligence.requirement_extractor import RequirementExtractor
from backend.services.ranking_layer.retrieval_engine import RetrievalEngine

router = APIRouter()

class JDRequest(BaseModel):
    text: str
    is_custom: bool = False
    user_id: str = None

@router.post("/parse")
async def parse_jd(request: JDRequest):
    """
    Parses a raw job description string into a structured JobDescription model
    and extracts absolute constraints.
    """
    try:
        jd_data = await JDParser.parse_jd_text(request.text)
        hard_reqs = await RequirementExtractor.extract_hard_requirements(request.text)
        return {
            "structured_jd": jd_data.model_dump(),
            "extracted_constraints": hard_reqs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match")
async def match_jd_to_candidates(request: JDRequest):
    """
    Parses the JD and runs the full Hybrid Retrieval Pipeline.
    Returns the top 7 best fit candidates and 18 additional candidates to consider.
    """
    try:
        jd_data = await JDParser.parse_jd_text(request.text)
        ranked_candidates = await RetrievalEngine.retrieve_and_rank(jd_data, request.is_custom, request.user_id)
        return {
            "query_jd": jd_data.model_dump(),
            "top_candidates": ranked_candidates[:7],
            "considered_candidates": ranked_candidates[7:]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
