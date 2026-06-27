import asyncio
import json
import logging
from dotenv import load_dotenv

# Load env vars before importing services
load_dotenv()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.core.db import supabase
from backend.app.utils.gemini_client import generate_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_database():
    try:
        with open("data/sample_candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find data/sample_candidates.json. Make sure you are running from the root directory.")
        return

    logger.info(f"Loaded {len(candidates)} candidates from JSON. Starting embedding and insertion process...")

    for i, candidate in enumerate(candidates):
        cand_id = candidate.get("candidate_id")
        
        # Create a rich semantic string to embed
        profile = candidate.get("profile", {})
        skills = [s.get("name") for s in candidate.get("skills", [])]
        semantic_text = f"Role: {profile.get('current_title', '')}. Summary: {profile.get('summary', '')}. Skills: {', '.join(skills)}."
        
        try:
            logger.info(f"Generating embedding for {cand_id} ({i+1}/{len(candidates)})...")
            embedding = await generate_embeddings(semantic_text)
            
            # Insert into Supabase
            supabase.table("candidates").upsert({
                "candidate_id": cand_id,
                "profile_data": candidate,
                "embedding": embedding
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to process {cand_id}: {e}")
            
    logger.info("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
