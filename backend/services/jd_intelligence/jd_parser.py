import json
import logging
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry
from backend.models.jd import JobDescription

logger = logging.getLogger(__name__)

class JDParser:
    """
    Service to parse unstructured Job Description text into structured JSON.
    """
    
    @staticmethod
    async def parse_jd_text(jd_text: str) -> JobDescription:
        prompt = f"""
You are a senior technical recruiter and job description parser.

Your task is to extract structured hiring information from an unstructured Job Description (JD).

IMPORTANT RULES:

1. Return ONLY a valid JSON object.
2. Do NOT include explanations, markdown, comments, or extra text.
3. Infer information only when the JD strongly implies it.
4. If information is not available, return null.
5. Deduplicate skills and requirements.
6. Normalize skill names (e.g., "Amazon Web Services" -> "AWS", "K8s" -> "Kubernetes").
7. Extract only actual technical/professional skills. Ignore generic traits like:
   - Team player
   - Good communication
   - Fast learner
   - Leadership
   - Problem solving

FIELD EXTRACTION RULES:

role:
- Extract the primary job title.
- Example: "Senior Backend Engineer", "Machine Learning Engineer".

domain:
- Extract industry/domain if mentioned.
- Examples: Fintech, Healthcare, E-commerce, EdTech, SaaS.
- Otherwise null.

min_experience_years:
- Extract minimum years required.
- "5+ years" => 5
- "3-6 years" => 3

max_experience_years:
- Extract maximum years if specified.
- "3-6 years" => 6
- "5+ years" => null

required_skills:
- Skills explicitly required.
- Include programming languages, frameworks, databases, cloud platforms, tools, methodologies.
- Examples:
  Python, Java, Spring Boot, PostgreSQL, Kafka, AWS, Kubernetes.

nice_to_have_skills:
- Skills mentioned as:
  "preferred"
  "plus"
  "good to have"
  "bonus"
  "nice to have"
  "preferred qualification"

must_have_requirements:
- Non-skill mandatory requirements.
- Examples:
  Bachelor's degree
  Master's degree
  Security clearance
  Work authorization
  Certifications
  Domain experience requirements

role_type:
- Extract if present.
- Examples:
  Full-time
  Contract
  Internship
  Part-time
  Temporary
  Freelance
- If not mentioned, return null.

--- EXAMPLE 1 ---

Input JD:
"We are looking for a Senior Data Engineer with 5+ years of experience. You must know Python, SQL, and AWS. Experience with Docker and Kubernetes is a big plus. You'll be working in our Fintech domain. Need a Bachelor's degree."

Output:
{{
  "role": "Senior Data Engineer",
  "domain": "Fintech",
  "min_experience_years": 5.0,
  "max_experience_years": null,
  "required_skills": ["Python", "SQL", "AWS"],
  "nice_to_have_skills": ["Docker", "Kubernetes"],
  "must_have_requirements": ["Bachelor's degree"],
  "role_type": null
}}

--- EXAMPLE 2 ---

Input JD:
"Seeking a Machine Learning Engineer with 3-6 years of experience. Required skills include Python, TensorFlow, PyTorch, and AWS. Experience in healthcare is preferred. Master's degree preferred. Full-time role."

Output:
{{
  "role": "Machine Learning Engineer",
  "domain": "Healthcare",
  "min_experience_years": 3.0,
  "max_experience_years": 6.0,
  "required_skills": ["Python", "TensorFlow", "PyTorch", "AWS"],
  "nice_to_have_skills": ["Experience in healthcare is preferred"],
  "must_have_requirements": ["Master's degree"],
  "role_type": "Full-time"
}}

Now analyze the following Job Description and return ONLY the JSON:

{jd_text}
"""
        response = await generate_content_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobDescription,
            )
        )
        
        try:
            raw_text = response.text.strip()
            # Clean up markdown code blocks if the model outputs them
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            # Find the last closing brace to ignore trailing hallucinations
            last_brace_idx = raw_text.rfind("}")
            if last_brace_idx != -1:
                raw_text = raw_text[:last_brace_idx + 1]
            
            data = json.loads(raw_text)
            return JobDescription.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to parse JD from Gemini: {e}")
            logger.error(f"Raw Gemini Output: {response.text}")
            raise ValueError("Failed to parse JD into valid structure.")
