import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.models.candidate import Candidate

logger = logging.getLogger(__name__)


class CandidateEmbedder:
    """
    Service to generate semantic embeddings for Candidate profiles using Sentence-Transformers.
    """

    def __init__(
        self, model_name: str = "all-MiniLM-L6-v2", device: str = None
    ) -> None:
        """
        Initializes the candidate embedder with a sentence-transformer model.

        Args:
            model_name: Hugging Face model hub path or local directory containing the model.
            device: Computes device (e.g. 'cpu', 'cuda'). Defaults to automatic detection.
        """
        logger.info(f"Loading sentence-transformer model: {model_name} on device: {device or 'auto'}")
        self.model = SentenceTransformer(model_name, device=device)

    def prepare_text_representation(self, candidate: Candidate) -> str:
        """
        Compiles skills, projects, experience, and education details of a candidate
        into a structured text document designed for semantic dense retrieval.

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            A single structured text string.
        """
        # 1. Stated Headline, Summary, and general metadata
        headline = candidate.profile.headline.strip()
        yoe = candidate.profile.years_of_experience
        summary = candidate.profile.summary.strip()
        
        # Integrate projects via github signals placeholder
        github_score = candidate.redrob_signals.github_activity_score
        github_text = (
            f"GitHub Open Source Activity Score: {github_score}/100."
            if github_score >= 0
            else "No public GitHub account linked."
        )
        profile_part = (
            f"Candidate Professional Headline: {headline}\n"
            f"Total Years of Experience: {yoe}\n"
            f"Summary & Highlights: {summary}\n"
            f"Projects & Open Source Contributions: {github_text}"
        )

        # 2. Skills representation
        skills_list = []
        for s in candidate.skills:
            dur_str = f" used for {s.duration_months} months" if s.duration_months else ""
            skills_list.append(f"{s.name} ({s.proficiency} proficiency{dur_str})")
        skills_text = (
            "Technical Skills: " + ", ".join(skills_list)
            if skills_list
            else "Technical Skills: None listed"
        )

        # 3. Experience (Career History) representation
        exp_list = []
        for job in candidate.career_history:
            end_date_str = "Present" if job.is_current else str(job.end_date)
            exp_list.append(
                f"- Role: {job.title} at {job.company} ({job.industry}) from {job.start_date} to {end_date_str} ({job.duration_months} months).\n"
                f"  Duties & Achievements: {job.description.strip()}"
            )
        experience_text = (
            "Professional Experience:\n" + "\n".join(exp_list)
            if exp_list
            else "Professional Experience: None listed"
        )

        # 4. Education representation
        edu_list = []
        for edu in candidate.education:
            grade_str = f" with grade {edu.grade}" if edu.grade else ""
            edu_list.append(
                f"- {edu.degree} in {edu.field_of_study} from {edu.institution} ({edu.start_year} - {edu.end_year}){grade_str}."
            )
        education_text = (
            "Academic Education:\n" + "\n".join(edu_list)
            if edu_list
            else "Academic Education: None listed"
        )

        # Combine all compiled fields
        full_text = (
            f"Candidate Profile Documents\n"
            f"===========================\n"
            f"{profile_part}\n\n"
            f"{skills_text}\n\n"
            f"{experience_text}\n\n"
            f"{education_text}"
        )
        return full_text

    def embed_candidate(self, candidate: Candidate) -> np.ndarray:
        """
        Generates a dense vector embedding representation for a single Candidate.

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            A 1D numpy array representing the candidate embedding vector.
        """
        text_representation = self.prepare_text_representation(candidate)
        embedding = self.model.encode(text_representation, convert_to_numpy=True)
        return embedding

    def embed_candidates(
        self,
        candidates: List[Candidate],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> List[np.ndarray]:
        """
        Generates embedding vectors for a batch of Candidate profiles.

        Args:
            candidates: List of Candidate model instances.
            batch_size: Size of batches sent to the transformer model.
            show_progress_bar: If True, prints embedding progress.

        Returns:
            List of 1D numpy arrays representing candidate embeddings.
        """
        if not candidates:
            return []
            
        texts = [self.prepare_text_representation(c) for c in candidates]
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )
        return [emb for emb in embeddings]
