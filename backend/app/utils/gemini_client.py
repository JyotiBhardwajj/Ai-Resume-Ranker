# pyrefly: ignore [missing-import]
from google import genai
import json
from backend.app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.genai.errors import APIError

# Initialize the new Google GenAI client
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else genai.Client()

MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-2"

def get_gemini_client():
    return client

# Configure retry logic: wait 2^x * 2 seconds between retries, max 5 attempts.
# Only retry on APIError where status is 429 (Too Many Requests).
def is_rate_limit_error(exception):
    if isinstance(exception, APIError):
        # 429 corresponds to ResourceExhausted / Too Many Requests
        return exception.code == 429
    return False

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
async def generate_embeddings(text: str) -> list[float]:
    """Generates embeddings for a given text using text-embedding-004, with automatic retries for rate limits."""
    response = await client.aio.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return response.embeddings[0].values

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
async def generate_content_with_retry(contents, config=None, model=MODEL_NAME):
    """Generates content using Gemini with automatic retries for rate limits."""
    return await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
