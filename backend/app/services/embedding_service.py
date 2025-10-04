import torch
import librosa
import numpy as np
from pathlib import Path
import logging
from typing import Optional
from laion_clap import CLAP_Module

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating audio embeddings using CLAP model."""

    def __init__(self, model_name: str = "music_audioset_epoch_15_esc_90.14.pt"):
        """
        Initialize the embedding service with CLAP model.

        Args:
            model_name: Name of the CLAP checkpoint to use
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")

        # Initialize CLAP model
        self.model = CLAP_Module(enable_fusion=False, device=self.device)
        self.model.load_ckpt(model_name)

        # Audio processing parameters
        self.sample_rate = 48000  # CLAP expects 48kHz
        self.target_length = 10  # seconds

        logger.info(f"CLAP model loaded: {model_name}")

    def load_audio(self, audio_path: str) -> np.ndarray:
        """
        Load and preprocess audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Preprocessed audio array
        """
        try:
            # Load audio with librosa
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)

            # Pad or trim to target length
            target_samples = self.sample_rate * self.target_length
            if len(audio) < target_samples:
                # Pad with zeros
                audio = np.pad(audio, (0, target_samples - len(audio)))
            else:
                # Trim to target length
                audio = audio[:target_samples]

            return audio

        except Exception as e:
            logger.error(f"Error loading audio from {audio_path}: {e}")
            raise

    def generate_embedding(self, audio_path: str) -> np.ndarray:
        """
        Generate embedding vector for an audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Normalized embedding vector (512-dim for CLAP)
        """
        try:
            # Load audio
            audio = self.load_audio(audio_path)

            # Generate embedding using CLAP
            with torch.no_grad():
                audio_tensor = torch.from_numpy(audio).unsqueeze(0).to(self.device)
                embedding = self.model.get_audio_embedding_from_data(
                    x=audio_tensor,
                    use_tensor=True
                )

            # Convert to numpy and normalize
            embedding_np = embedding.cpu().numpy().flatten()
            embedding_normalized = embedding_np / np.linalg.norm(embedding_np)

            logger.info(f"Generated embedding of shape {embedding_normalized.shape}")
            return embedding_normalized

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Ensure normalized
        emb1_norm = embedding1 / np.linalg.norm(embedding1)
        emb2_norm = embedding2 / np.linalg.norm(embedding2)

        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)

        return float(similarity)


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
