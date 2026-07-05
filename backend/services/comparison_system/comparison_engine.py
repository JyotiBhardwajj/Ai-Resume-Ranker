import json
import logging
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry

logger = logging.getLogger(__name__)

class ComparisonEngine:
    """
    Compares multiple candidates against each other and the Job Description.
    """
    
    @staticmethod
    async def compare_candidates(jd_text: str, candidates: list) -> dict:
        prompt = f"""
You are an expert AI recruiter. Compare the following candidates strictly against the Job Description.
Evaluate their strengths, weaknesses, and provide a final recommendation on who is the best fit.

Return ONLY a valid JSON object matching this schema:
{{
  "comparisons": [
    {{
      "candidate_id": "string",
      "strengths": ["string"],
      "weaknesses": ["string"]
    }}
  ],
  "recommended_candidate_id": "string",
  "reasoning": "string"
}}

Job Description:
{jd_text}

Candidates:
{json.dumps(candidates, indent=2)}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        try:
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Failed to parse Comparison output: {e}")
            raise ValueError("Failed to compare candidates")
