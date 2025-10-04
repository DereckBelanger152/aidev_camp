from __future__ import annotations

import logging
from typing import Iterable, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)


class MusicLLMService:
    """Lightweight text generation service for music-related summaries."""

    def __init__(
        self,
        model_id: str = "distilgpt2",
        max_new_tokens: int = 120,
        temperature: float = 0.7,
        device: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():  # type: ignore[attr-defined]
                device = "mps"
            else:
                device = "cpu"
        self.device = device

        logger.info("Loading LLM model %s on %s", model_id, device)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
        self.generator = pipeline(
            task="text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if device == "cuda" else -1,
        )

    def build_prompt(
        self,
        *,
        hints: Optional[str],
        identified_track: dict,
        similar_tracks: Iterable[dict],
    ) -> str:
        lines = [
            "You are a helpful music curator. Recognise the song and explain why the recommended songs match.",
        ]
        if hints:
            lines.append(f"Hints provided: {hints}.")
        lines.append(
            "Identified song: "
            f"{identified_track.get('title', 'Unknown title')} by {identified_track.get('artist', 'Unknown artist')}.")
        genre = identified_track.get("genre") or identified_track.get("genre_name")
        if genre:
            lines.append(f"Style or genre: {genre}.")
        confidence = identified_track.get("confidence")
        if confidence is not None:
            lines.append(f"Audio match confidence: {confidence:.3f}.")
        lines.append("Similar tracks:")
        for idx, track in enumerate(similar_tracks, start=1):
            lines.append(
                f"{idx}. {track.get('title', 'Unknown')} by {track.get('artist', 'Unknown')} "
                f"(similarity {track.get('similarity', track.get('similarity_score', 0)):.3f})."
            )
        lines.append("Write a short, concise paragraph (max three sentences).\nResponse:")
        return "\n".join(lines)

    def generate_summary(
        self,
        *,
        hints: Optional[str],
        identified_track: dict,
        similar_tracks: Iterable[dict],
    ) -> tuple[str, str]:
        prompt = self.build_prompt(
            hints=hints,
            identified_track=identified_track,
            similar_tracks=similar_tracks,
        )
        try:
            outputs = self.generator(
                prompt,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=self.temperature,
                num_return_sequences=1,
            )
            generated = outputs[0]["generated_text"]
            if generated.startswith(prompt):
                generated = generated[len(prompt) :]
            return prompt, generated.strip()
        except Exception as exc:  # pragma: no cover - model failure
            logger.error("LLM generation failed: %s", exc)
            return prompt, "Unable to generate summary at this time."


_music_llm_service: Optional[MusicLLMService] = None


def get_music_llm_service() -> MusicLLMService:
    global _music_llm_service
    if _music_llm_service is None:
        _music_llm_service = MusicLLMService()
    return _music_llm_service
