from __future__ import annotations

import json
import logging
import os
from typing import Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class ChatGPTVoiceRecognitionService:
    """Leverage ChatGPT (OpenAI) to identify a song from raw audio."""

    def __init__(
        self,
        *,
        client: Optional[OpenAI] = None,
        transcription_model: str = "gpt-4o-mini-transcribe",
        reasoning_model: str = "gpt-4.1-mini",
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key and client is None:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is required for voice recognition."
            )

        self.client = client or OpenAI(api_key=api_key)
        self.transcription_model = transcription_model
        self.reasoning_model = reasoning_model

    def identify_song_from_audio(
        self,
        audio_path: str,
        *,
        hints: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        """Return probable song metadata using transcription + reasoning."""

        transcript = self._transcribe_audio(audio_path)
        identification = self._reason_about_song(transcript, hints=hints)
        identification["transcription"] = transcript
        return identification

    def _transcribe_audio(self, audio_path: str) -> str:
        logger.info("Transcribing audio via ChatGPT model %s", self.transcription_model)
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.transcription_model,
                file=audio_file,
            )
        transcript = response.text.strip() if hasattr(response, "text") else response.get("text", "")  # type: ignore[attr-defined]
        if not transcript:
            raise RuntimeError("Transcription returned empty result")
        logger.debug("Transcription completed (%s characters)", len(transcript))
        return transcript

    def _reason_about_song(self, transcript: str, *, hints: Optional[str]) -> Dict[str, Optional[str]]:
        logger.info("Calling ChatGPT reasoning model %s for song identification", self.reasoning_model)
        system_prompt = (
            "You receive lyrics or humming transcriptions. Identify the most probable song title and artist. "
            "Respond strictly as JSON with keys 'title', 'artist', and optional 'confidence' (0-1)."
        )
        user_prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Transcript: {transcript}\n"
                        f"Hints: {hints or 'None provided'}\n"
                        "Return JSON."
                    ),
                }
            ],
        }
        response = self.client.responses.create(
            model=self.reasoning_model,
            input=[{"role": "system", "content": system_prompt}, user_prompt],
        )
        raw_output = response.output[0].content[0].text if response.output else ""  # type: ignore[attr-defined]
        raw_output = raw_output.strip()
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            logger.warning("Voice reasoning returned non-JSON output, wrapping: %s", raw_output)
            data = {
                "title": None,
                "artist": None,
                "confidence": None,
                "notes": raw_output,
            }
        return {
            "title": data.get("title"),
            "artist": data.get("artist"),
            "confidence": data.get("confidence"),
            "raw_response": raw_output,
        }


_chatgpt_voice_service: Optional[ChatGPTVoiceRecognitionService] = None


def get_chatgpt_voice_service() -> ChatGPTVoiceRecognitionService:
    global _chatgpt_voice_service
    if _chatgpt_voice_service is None:
        _chatgpt_voice_service = ChatGPTVoiceRecognitionService()
    return _chatgpt_voice_service
