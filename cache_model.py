from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Downloading and caching all-MiniLM-L6-v2 to local HuggingFace cache...")
    # This will download the model weights (~90MB) and store them in ~/.cache/huggingface
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    logger.info("Model cached successfully! You can now run rank.py without an internet connection.")
