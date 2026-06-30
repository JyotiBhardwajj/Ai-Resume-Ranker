import json
import logging
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry
from backend.app.utils.markdown_synthesizer import synthesize_candidate_markdown

logger = logging.getLogger(__name__)

class RiskEngine:
    """
    Analyzes a candidate's profile for potential risks (gaps, job hopping, skill mismatches).
    """

    @staticmethod
    async def analyze_risks(jd_text: str, candidate_profile: dict) -> dict:
        prompt = f"""
You are a meticulous technical recruiter conducting risk analysis.
Review the candidate's career history and skills against the Job Description.
Identify red flags such as:
1. Job hopping: Defined as multiple consecutive roles lasting less than 1.5 years without clear promotions.
2. Large employment gaps: Defined strictly as any gap between roles exceeding 6 months.
3. Missing critical skills: Evaluate the candidate's skills against the JD's REQUIRED skills.
4. Mismatched seniority levels: e.g. A mid-level engineer applying for a Staff/Principal role.

Return ONLY a valid JSON object matching this schema:
{{
  "risk_level": "Low" | "Medium" | "High",
  "risk_score_0_to_100": number,
  "risk_factors": ["string"],
  "mitigating_factors": ["string"]
}}

Job Description:
{jd_text}

Candidate Profile:
{synthesize_candidate_markdown(candidate_profile)}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Failed to parse Risk Analysis output: {e}")
            raise ValueError("Failed to analyze risks")
