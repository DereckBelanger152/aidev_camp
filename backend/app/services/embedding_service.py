"""
Audio embedding service using OpenL3.
"""

import logging
from typing import Optional

import numpy as np
import librosa
import openl3

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating audio embeddings using OpenL3."""

    def __init__(self):
        """
        Initialize the embedding service with OpenL3.
        """
        logger.info("Initializing OpenL3 embedding service...")

        # OpenL3 configuration
        self.input_repr = "mel128"  # Mel-spectrogram representation (faster than mel256)
        self.content_type = "music"  # Music-specific model
        self.embedding_size = 512  # 512-dimensional embeddings
        self.hop_size = 1.0  # Hop size in seconds (1s = faster, 0.1s = more frames)
        self.sample_rate = 48000  # Target sample rate
        self.center_crop_duration = 15.0  # Process only 15s from center (faster)

        # Load OpenL3 model
        self.model = openl3.models.load_audio_embedding_model(
            input_repr=self.input_repr,
            content_type=self.content_type,
            embedding_size=self.embedding_size
        )

        logger.info("OpenL3 model loaded successfully (music, 512-dim)")

    def generate_embedding(self, audio_path: str, target_sr: int = 48000) -> np.ndarray:
        """
        Generates an OpenL3 embedding for a given audio file.

        Args:
            audio_path: path to an audio file (ideally ~30s clip)
            target_sr: sample rate for the model (default: 48000)

        Returns:
            np.ndarray: normalized embedding vector (1D)
        """
        # Load audio with librosa
        audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)

        # Center crop for speed (take 15s from middle instead of full 30s)
        audio_duration = len(audio) / sr
        if audio_duration > self.center_crop_duration:
            # Calculate center crop indices
            crop_samples = int(self.center_crop_duration * sr)
            center = len(audio) // 2
            start = center - crop_samples // 2
            end = start + crop_samples
            audio = audio[start:end]

        # Generate embeddings using OpenL3
        # Returns: (embedding, timestamps)
        # embedding shape: (num_frames, 512)
        embeddings, timestamps = openl3.get_audio_embedding(
            audio,
            sr,
            model=self.model,
            input_repr=self.input_repr,
            content_type=self.content_type,
            embedding_size=self.embedding_size,
            hop_size=self.hop_size
        )

        # Aggregate frame-level embeddings by taking the mean
        # This gives us a single 512-dimensional vector for the entire audio
        embedding_aggregated = np.mean(embeddings, axis=0)

        # Normalize to unit length
        embedding_normalized = embedding_aggregated / np.linalg.norm(embedding_aggregated)

        return embedding_normalized

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)

        except Exception as e:
            logger.error("Error calculating similarity: %s", e)
            raise


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
