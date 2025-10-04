from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from .deezer_service import DeezerService, get_deezer_service
from .huggingface_audio_service import (
    HuggingFaceAudioEmbedder,
    get_huggingface_audio_embedder,
)
from .style_recommendation_service import (
    StyleRecommendationService,
    get_style_recommendation_service,
)

logger = logging.getLogger(__name__)


class SongRecognitionService:
    """Identify songs and fetch stylistically similar tracks."""

    def __init__(
        self,
        deezer_service: Optional[DeezerService] = None,
        embedder: Optional[HuggingFaceAudioEmbedder] = None,
        style_service: Optional[StyleRecommendationService] = None,
    ) -> None:
        self.deezer = deezer_service or get_deezer_service()
        self.embedder = embedder or get_huggingface_audio_embedder()
        self.style_service = style_service or get_style_recommendation_service()

    def identify_and_recommend(
        self,
        *,
        track_id: Optional[str] = None,
        song_name: Optional[str] = None,
        artist: Optional[str] = None,
        preview_url: Optional[str] = None,
        audio_path: Optional[str] = None,
        candidate_limit: int = 25,
        similar_count: int = 2,
    ) -> Tuple[Dict, List[Dict]]:
        """Identify a track then compute stylistically similar songs."""

        recognized, confidence = self._identify_track(
            track_id=track_id,
            song_name=song_name,
            artist=artist,
            preview_url=preview_url,
            audio_path=audio_path,
            candidate_limit=candidate_limit,
        )

        if not recognized:
            raise ValueError("Unable to identify track with provided information")

        enriched = self.deezer.get_track_metadata(recognized["id"]) or recognized
        if confidence is not None:
            enriched["confidence"] = confidence

        recommendations = self.style_service.recommend_by_track_id(
            enriched["id"],
            candidate_limit=candidate_limit,
            top_k=similar_count,
        )

        return enriched, recommendations

    def _identify_track(
        self,
        *,
        track_id: Optional[str],
        song_name: Optional[str],
        artist: Optional[str],
        preview_url: Optional[str],
        audio_path: Optional[str],
        candidate_limit: int,
    ) -> Tuple[Optional[Dict], Optional[float]]:
        if track_id:
            logger.info("Identifying using provided track_id=%s", track_id)
            metadata = self.deezer.get_track_metadata(track_id)
            return metadata, None

        if song_name:
            query = song_name
            if artist:
                query = f"{song_name} {artist}".strip()
            logger.info("Searching Deezer with query='%s'", query)
            metadata = self.deezer.search_tracks(query, limit=1)
            if metadata:
                logger.info("Track identified via text search: %s", metadata.get("id"))
                return metadata, None

        if preview_url or audio_path:
            logger.info(
                "Attempting audio-based identification via %s",
                "preview URL" if preview_url else "uploaded audio",
            )
            return self._identify_from_audio(
                preview_url=preview_url,
                audio_path=audio_path,
                candidate_limit=candidate_limit,
            )

        return None, None

    def _identify_from_audio(
        self,
        *,
        preview_url: Optional[str],
        audio_path: Optional[str],
        candidate_limit: int,
    ) -> Tuple[Optional[Dict], Optional[float]]:
        if not preview_url and not audio_path:
            return None, None

        with tempfile.TemporaryDirectory(prefix="recognition_") as tmp_dir:
            if audio_path:
                query_path = Path(audio_path)
                cleanup_query = False
            else:
                query_path = Path(tmp_dir) / "query.mp3"
                cleanup_query = True
                self._download_file(preview_url, query_path)  # type: ignore[arg-type]
                logger.debug("Downloaded query audio to %s", query_path)

            try:
                query_embedding = self.embedder.embed(str(query_path))
            finally:
                if cleanup_query and query_path.exists():
                    query_path.unlink()

            candidates = self.deezer.get_chart_tracks(limit=candidate_limit)
            best: Tuple[Optional[Dict], float] = (None, -1.0)

            for candidate in candidates:
                preview = candidate.get("preview_url")
                candidate_id = candidate.get("id")
                if not preview or not candidate_id:
                    continue

                candidate_path = Path(tmp_dir) / f"candidate_{candidate_id}.mp3"
                try:
                    self.deezer.download_preview(preview, str(candidate_path))
                    candidate_embedding = self.embedder.embed(str(candidate_path))
                    similarity = self.embedder.similarity(query_embedding, candidate_embedding)
                except Exception as exc:  # pragma: no cover
                    logger.debug("Skipping candidate %s due to error: %s", candidate_id, exc)
                    continue

                if similarity > best[1]:
                    best = (candidate, similarity)

            if best[0] is None:
                logger.warning("No audio candidates matched query preview")
                return None, None

            metadata = self.deezer.get_track_metadata(best[0]["id"]) or best[0]
            logger.info(
                "Audio identification matched track %s with confidence %.3f",
                metadata.get("id"),
                best[1],
            )
            return metadata, best[1]

    @staticmethod
    def _download_file(url: str, destination: Path) -> None:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(destination, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                handle.write(chunk)


_song_recognition_service: Optional[SongRecognitionService] = None


def get_song_recognition_service() -> SongRecognitionService:
    global _song_recognition_service
    if _song_recognition_service is None:
        _song_recognition_service = SongRecognitionService()
    return _song_recognition_service
