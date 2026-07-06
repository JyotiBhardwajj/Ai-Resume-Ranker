from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
import uuid
import logging
from backend.app.core.db import supabase
from backend.services.comparison_system.comparison_engine import ComparisonEngine
from backend.services.risk_engine.risk_analysis import RiskEngine
from backend.services.recommendation_engine.recruiter_copilot import RecruiterCopilot
from backend.services.pdf_parser import PDFResumeParser
from backend.app.utils.gemini_client import generate_embeddings
from backend.app.utils.markdown_synthesizer import synthesize_candidate_markdown

logger = logging.getLogger(__name__)

router = APIRouter()

class CandidateRequest(BaseModel):
    jd_text: str
    candidate_id: str

class ComparisonRequest(BaseModel):
    jd_text: str
    candidate_ids: List[str]

@router.post("/risk")
async def analyze_candidate_risk(req: CandidateRequest):
    """
    Analyzes a candidate for job-hopping, gaps, and missing skills.
    """
    try:
        # Fetch candidate profile from DB
        resp = supabase.table("candidates").select("profile_data").eq("candidate_id", req.candidate_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Candidate {req.candidate_id} not found in database.")
        
        candidate_data = resp.data[0]['profile_data']
        risk_report = await RiskEngine.analyze_risks(req.jd_text, candidate_data)
        return risk_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copilot")
async def generate_recruiter_guide(req: CandidateRequest):
    """
    Generates tailored interview questions and a personalized outreach email.
    """
    try:
        resp = supabase.table("candidates").select("profile_data").eq("candidate_id", req.candidate_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        candidate_data = resp.data[0]['profile_data']
        guide = await RecruiterCopilot.generate_interview_guide(req.jd_text, candidate_data)
        return guide
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_candidates(req: ComparisonRequest):
    """
    Compares multiple candidates side-by-side against the JD.
    """
    try:
        resp = supabase.table("candidates").select("profile_data").in_("candidate_id", req.candidate_ids).execute()
        if not resp.data or len(resp.data) != len(req.candidate_ids):
            raise HTTPException(status_code=404, detail="One or more candidates not found")
            
        profiles = [item['profile_data'] for item in resp.data]
        comparison = await ComparisonEngine.compare_candidates(req.jd_text, profiles)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Parses PDF resumes, generates embeddings, and stores them as Custom Data.
    """
    results = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "failed", "error": "Only PDFs are allowed."})
            continue
        try:
            content = await file.read()
            profile_data = await PDFResumeParser.parse_resume_to_json(content)
            
            cand_id = profile_data.get("candidate_id") or str(uuid.uuid4())
            profile_data["candidate_id"] = cand_id
            
            # Generate markdown and embed
            md_text = synthesize_candidate_markdown(profile_data)
            embedding = await generate_embeddings(md_text)
            
            # Upsert into supabase
            insert_data = {
                "candidate_id": cand_id,
                "profile_data": profile_data,
                "embedding": embedding,
                "is_custom": True
            }
            if user_id:
                insert_data["user_id"] = user_id
                
            supabase.table("candidates").upsert(insert_data).execute()
            
            results.append({"filename": file.filename, "candidate_id": cand_id, "status": "success"})
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
            
    return {"uploaded": results}
