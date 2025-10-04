from __future__ import annotations

import logging
from typing import Optional

import librosa
import numpy as np
import torch
from transformers import ClapModel, ClapProcessor

logger = logging.getLogger(__name__)


class HuggingFaceAudioEmbedder:
    """Generate audio embeddings using a Hugging Face CLAP model."""

    def __init__(
        self,
        model_id: str = "laion/clap-htsat-unfused",
        device: Optional[str] = None,
        target_sample_rate: int = 48000,
        max_duration: float = 30.0,
    ) -> None:
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():  # type: ignore[attr-defined]
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self.sample_rate = target_sample_rate
        self.max_duration = max_duration

        logger.info("Loading Hugging Face audio model %s on %s", model_id, self.device)
        self.processor = ClapProcessor.from_pretrained(model_id)
        self.model = ClapModel.from_pretrained(model_id).to(self.device)
        self.model.eval()

    def embed(self, audio_path: str) -> np.ndarray:
        """Return a normalized embedding vector for the given audio file."""

        audio, _ = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True,
            duration=self.max_duration,
        )
        if audio.size == 0:
            raise ValueError(f"Audio file {audio_path} produced an empty waveform")

        inputs = self.processor(
            audios=audio,
            sampling_rate=self.sample_rate,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            audio_features = self.model.get_audio_features(**inputs)

        embedding = audio_features.cpu().numpy().flatten()
        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise ValueError("Generated embedding has zero norm")
        return embedding / norm

    @staticmethod
    def similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


_hf_audio_embedder: Optional[HuggingFaceAudioEmbedder] = None


def get_huggingface_audio_embedder() -> HuggingFaceAudioEmbedder:
    global _hf_audio_embedder
    if _hf_audio_embedder is None:
        _hf_audio_embedder = HuggingFaceAudioEmbedder()
    return _hf_audio_embedder
