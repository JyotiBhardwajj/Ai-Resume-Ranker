import json
import logging
from google.genai import types
from backend.app.utils.gemini_client import client, MODEL_NAME, generate_content_with_retry
from backend.app.utils.markdown_synthesizer import synthesize_candidate_markdown

logger = logging.getLogger(__name__)

class RecruiterCopilot:
    """
    Generates personalized interview guides and outreach emails based on JD/Candidate alignment.
    """

    @staticmethod
    async def generate_interview_guide(jd_text: str, candidate_profile: dict) -> dict:
        prompt = f"""
You are an expert recruiter preparing an interview guide for a hiring manager.
Based on the JD and the candidate's profile, generate personalized interview questions that probe their specific weaknesses and verify their claimed strengths.

Generate a personalized outreach email to recruit this candidate for the role. The email MUST strictly follow this exact template structure, but seamlessly weave in 1-2 personalized sentences in the second paragraph mentioning their specific impressive experience relevant to the JD:

Subject: Next Steps: Your application for [Job Title] at [Company Name]

Dear [Candidate Name],

Thank you for applying to the [Job Title] role at [Company Name].

We have reviewed your application and background. We are highly impressed by your experience (tailor this sentence here with 1 specific detail from their profile related to the JD) and have shortlisted you for the next round of our hiring process.

We would love to invite you for a short, [15/20-minute] introductory phone call. This will be a great opportunity to learn more about your background, discuss the role, and answer any questions you have about working with us.

Please use this [Link to Scheduling Tool] to pick a time slot that works best for your schedule.

If none of those times work for you, reply directly to this email with 2-3 windows when you are free this week.

We look forward to speaking with you!

Best regards,

[Your Name/The Talent Acquisition Team]
[Your Title]
[Company Name]

Return ONLY a valid JSON object matching this schema:
{{
  "technical_questions": ["string"],
  "behavioral_questions": ["string"],
  "areas_to_probe": ["string"],
  "personalized_outreach_email": "string"
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
            logger.error(f"Failed to parse Copilot output: {e}")
            raise ValueError("Failed to generate recruiter copilot guide")
