from __future__ import annotations

import asyncio
import base64
import binascii
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models.schemas import (
    IdentifiedTrack,
    LLMSummary,
    RecommendationTrack,
    SongIdentificationRequest,
    SongIdentificationResponse,
    VoiceIdentificationRequest,
    VoiceIdentificationResponse,
)
from app.services import (
    get_chatgpt_voice_service,
    get_music_llm_service,
    get_song_recognition_service,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ai/identify", response_model=SongIdentificationResponse)
async def identify_song(request: SongIdentificationRequest) -> SongIdentificationResponse:
    """Identify a song (optionally using hints) and recommend stylistically similar tracks."""

    recognition_service = get_song_recognition_service()
    llm_service = get_music_llm_service()

    try:
        identified_track, recommendations = await asyncio.to_thread(
            recognition_service.identify_and_recommend,
            track_id=request.track_id,
            song_name=request.song_name,
            artist=request.artist,
            preview_url=str(request.preview_url) if request.preview_url else None,
            audio_path=None,
            candidate_limit=request.candidate_limit,
            similar_count=request.similar_count,
        )
    except ValueError as exc:
        logger.warning("Song identification failed: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - runtime failure
        logger.error("Song identification error: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to identify song at this time")

    hints_parts = []
    if request.song_name:
        hints_parts.append(f"title hint '{request.song_name}'")
    if request.artist:
        hints_parts.append(f"artist hint '{request.artist}'")
    if request.track_id:
        hints_parts.append(f"track id {request.track_id}")
    if request.preview_url:
        hints_parts.append("audio preview supplied")

    return _build_identification_response(
        identified_track,
        recommendations,
        hints_description=", ".join(hints_parts) if hints_parts else None,
        llm_service=llm_service,
    )


@router.post("/ai/identify/upload", response_model=SongIdentificationResponse)
async def identify_song_from_upload(
    file: UploadFile = File(..., description="MP3 or audio file to analyse"),
    similar_count: int = Query(2, ge=1, le=5, description="Number of similar tracks to return"),
    candidate_limit: int = Query(25, ge=5, le=100, description="Candidate pool size for audio matching"),
) -> SongIdentificationResponse:
    """Identify a song from an uploaded audio file and return stylistically similar tracks."""

    recognition_service = get_song_recognition_service()
    llm_service = get_music_llm_service()

    suffix = Path(file.filename or "audio.mp3").suffix or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="upload_query_") as tmp_file:
        contents = await file.read()
        tmp_file.write(contents)
        tmp_path = tmp_file.name

    try:
        identified_track, recommendations = await asyncio.to_thread(
            recognition_service.identify_and_recommend,
            audio_path=tmp_path,
            candidate_limit=candidate_limit,
            similar_count=similar_count,
        )
    except ValueError as exc:
        logger.warning("Song identification failed for uploaded audio: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - runtime failure
        logger.error("Song identification error for uploaded audio: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to identify song at this time")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            logger.debug("Temporary upload file %s could not be removed", tmp_path)

    hints_description = f"uploaded audio file '{file.filename or Path(tmp_path).name}'"

    return _build_identification_response(
        identified_track,
        recommendations,
        hints_description=hints_description,
        llm_service=llm_service,
    )


@router.post("/ai/identify/voice", response_model=VoiceIdentificationResponse)
async def identify_song_from_voice(request: VoiceIdentificationRequest) -> VoiceIdentificationResponse:
    """Use a ChatGPT voice plugin to recognise a song from recorded audio and suggest similar songs."""

    chatgpt_voice = get_chatgpt_voice_service()
    recognition_service = get_song_recognition_service()
    llm_service = get_music_llm_service()

    with _decode_audio_to_tempfile(request.audio_base64, request.filename) as audio_path:
        try:
            voice_result = await asyncio.to_thread(
                chatgpt_voice.identify_song_from_audio,
                audio_path,
                hints=request.hints,
            )
        except Exception as exc:
            logger.error("Voice identification failed: %s", exc)
            raise HTTPException(status_code=500, detail="Voice recognition failed; please retry")

        title = voice_result.get("title")
        artist = voice_result.get("artist")
        if not title and not artist:
            raise HTTPException(
                status_code=404,
                detail="ChatGPT voice plugin could not determine the song",
            )

        try:
            identified_track, recommendations = await asyncio.to_thread(
                recognition_service.identify_and_recommend,
                song_name=title,
                artist=artist,
                candidate_limit=request.candidate_limit,
                similar_count=request.similar_count,
            )
        except ValueError as exc:
            logger.warning("Song identification failed based on voice plugin output: %s", exc)
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            logger.error("Similarity search failed after voice identification: %s", exc)
            raise HTTPException(status_code=500, detail="Unable to compute similar songs")

        hints_description = (
            f"chatgpt voice recognition (title={title or 'unknown'}, artist={artist or 'unknown'})"
        )

        base_response = _build_identification_response(
            identified_track,
            recommendations,
            hints_description=hints_description,
            llm_service=llm_service,
        )

        return VoiceIdentificationResponse(
            identified_track=base_response.identified_track,
            similar_tracks=base_response.similar_tracks,
            llm_summary=base_response.llm_summary,
            transcription=voice_result.get("transcription"),
            voice_confidence=voice_result.get("confidence"),
        )


def _build_identification_response(
    identified_track: dict,
    recommendations: Iterable[dict],
    *,
    hints_description: Optional[str],
    llm_service,
) -> SongIdentificationResponse:
    similar_tracks: List[RecommendationTrack] = []
    for track in recommendations:
        similarity = track.get("similarity") or track.get("similarity_score") or 0.0
        similar_tracks.append(
            RecommendationTrack(
                id=str(track.get("id", "")),
                title=track.get("title", "Unknown"),
                artist=track.get("artist", "Unknown"),
                similarity_score=float(round(similarity, 3)),
                popularity=track.get("rank") or track.get("popularity"),
                preview_url=track.get("preview") or track.get("preview_url"),
                cover=track.get("cover"),
            )
        )

    identified_payload = IdentifiedTrack(**identified_track)

    prompt, summary = llm_service.generate_summary(
        hints=hints_description,
        identified_track={**identified_track, "confidence": identified_track.get("confidence")},
        similar_tracks=[track.model_dump() for track in similar_tracks],
    )

    return SongIdentificationResponse(
        identified_track=identified_payload,
        similar_tracks=similar_tracks,
        llm_summary=LLMSummary(prompt=prompt, response=summary),
    )


class _TempFileContext:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> str:
        return str(self.path)

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
        except OSError:
            logger.debug("Failed to delete temporary voice file %s", self.path)


def _decode_audio_to_tempfile(audio_base64: str, filename: Optional[str]) -> _TempFileContext:
    try:
        if "," in audio_base64:  # Handle data URI prefix
            audio_base64 = audio_base64.split(",", 1)[1]
        audio_bytes = base64.b64decode(audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload") from exc

    suffix = Path(filename or "voice.mp3").suffix or ".mp3"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="voice_query_")
    tmp_file.write(audio_bytes)
    tmp_file.flush()
    tmp_file.close()
    return _TempFileContext(Path(tmp_file.name))
