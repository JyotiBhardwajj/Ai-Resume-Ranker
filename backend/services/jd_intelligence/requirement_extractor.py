import json
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry

class RequirementExtractor:
    """
    Advanced service to extract deeply implicit requirements from a JD, 
    separating absolute non-negotiables from preferred attributes.
    """
    
    @staticmethod
    async def extract_hard_requirements(jd_text: str) -> dict:
        prompt = f"""
You are an AI analyzing a Job Description for STRICT, non-negotiable requirements.
Extract absolute deal-breakers for this role (e.g., must be a US Citizen, must have Security Clearance, must have a PhD).
Ignore standard skills. Focus only on absolute disqualifiers if missing.

Respond in JSON:
{{
  "absolute_constraints": ["constraint1", "constraint2"],
  "degree_requirements": "string or null",
  "certifications_required": ["cert1"]
}}

Job Description:
{jd_text}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
