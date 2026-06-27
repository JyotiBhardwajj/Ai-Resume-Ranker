import pypdf
import json
import io
import uuid
import logging
from google.genai import types
from backend.app.utils.gemini_client import generate_content_with_retry, MODEL_NAME

logger = logging.getLogger(__name__)

class PDFResumeParser:
    """
    Parses PDF resumes, extracts text, and uses Gemini to map them to the
    application's native JSON schema with deep semantic normalization.
    """

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError("Invalid PDF file or unable to extract text.")

    @staticmethod
    async def parse_resume_to_json(pdf_bytes: bytes) -> dict:
        raw_text = PDFResumeParser.extract_text_from_pdf(pdf_bytes)
        
        prompt = f"""
You are an expert AI Resume Parser with a deep understanding of industry ontologies.
Your task is to parse the following raw resume text and extract it into a structured JSON profile.

CRITICAL REQUIREMENT: SEMANTIC NORMALIZATION
You must actively normalize the data to canonical industry terms.
1. Domain/Industry Normalization: If the candidate worked at a "medical company", map the industry to "Healthcare". If "Banking software", map to "Fintech". Use broad, canonical industry names.
2. Skill Normalization: Normalize all technical skills to their canonical names. E.g., "Golang" -> "Go", "React.js" -> "React", "K8s" -> "Kubernetes", "AWS Cloud" -> "AWS".

Return ONLY a valid JSON object matching the following structure:
{{
  "candidate_id": "Generate a random UUID string here",
  "profile": {{
    "anonymized_name": "string",
    "headline": "string",
    "summary": "string",
    "location": "string",
    "country": "string",
    "years_of_experience": number,
    "current_title": "string",
    "current_company": "string",
    "current_industry": "string (NORMALIZED)"
  }},
  "career_history": [
    {{
      "title": "string",
      "company_name": "string",
      "start_date": "string (YYYY-MM-DD or MM/YYYY)",
      "end_date": "string (YYYY-MM-DD or MM/YYYY or Present)",
      "duration_months": number,
      "description": "string"
    }}
  ],
  "education": [
    {{
      "degree_name": "string",
      "school_name": "string",
      "year_of_graduation": "string"
    }}
  ],
  "skills": [
    {{
      "name": "string (NORMALIZED)"
    }}
  ]
}}

Resume Text:
{raw_text}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Gemini JSON output: {e}")
            raise ValueError("Failed to parse resume into structured JSON format.")
