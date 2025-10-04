from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from .deezer_service import DeezerService, get_deezer_service
from .huggingface_audio_service import (
    HuggingFaceAudioEmbedder,
    get_huggingface_audio_embedder,
)

logger = logging.getLogger(__name__)


class StyleRecommendationService:
    """Use audio embeddings to suggest stylistically similar Deezer tracks."""

    def __init__(
        self,
        deezer_service: Optional[DeezerService] = None,
        embedder: Optional[HuggingFaceAudioEmbedder] = None,
    ) -> None:
        self.deezer = deezer_service or get_deezer_service()
        self.embedder = embedder or get_huggingface_audio_embedder()

    def recommend_by_track_id(
        self,
        track_id: str,
        *,
        candidate_limit: int = 25,
        top_k: int = 2,
    ) -> List[Dict]:
        metadata = self.deezer.get_track_metadata(track_id)
        if not metadata or not metadata.get("preview_url"):
            raise ValueError("Selected track has no preview available for analysis")

        with tempfile.TemporaryDirectory(prefix="style_") as tmp_dir:
            query_path = Path(tmp_dir) / f"query_{track_id}.mp3"
            self.deezer.download_preview(metadata["preview_url"], str(query_path))
            query_embedding = self.embedder.embed(str(query_path))

            candidates = self._collect_candidates(track_id, limit=candidate_limit)
            scored = self._score_candidates(
                candidates,
                query_embedding,
                temp_dir=tmp_dir,
                exclude_id=track_id,
            )

        ranked = sorted(scored, key=lambda item: item["similarity"], reverse=True)
        return ranked[:top_k]

    def _collect_candidates(self, track_id: str, limit: int) -> List[Dict]:
        seen_ids: set[str] = {track_id}
        candidates: List[Dict] = []

        try:
            related = self.deezer.get_related_tracks(track_id, limit=limit)
        except Exception as exc:  # pragma: no cover
            logger.debug("Failed to fetch related tracks: %s", exc)
            related = []

        for track in related:
            if not track or track.get("id") in seen_ids:
                continue
            seen_ids.add(track["id"])
            candidates.append(track)
            if len(candidates) >= limit:
                return candidates

        if len(candidates) < limit:
            try:
                charts = self.deezer.get_chart_tracks(limit=limit * 2)
            except Exception as exc:  # pragma: no cover
                logger.debug("Failed to fetch chart tracks: %s", exc)
                charts = []
            for track in charts:
                if (
                    not track
                    or track.get("id") in seen_ids
                    or not track.get("preview_url")
                ):
                    continue
                seen_ids.add(track["id"])
                candidates.append(track)
                if len(candidates) >= limit:
                    break

        return candidates

    def _score_candidates(
        self,
        candidates: List[Dict],
        query_embedding,
        *,
        temp_dir: str,
        exclude_id: str,
    ) -> List[Dict]:
        results: List[Dict] = []
        temp_path = Path(temp_dir)

        for candidate in candidates:
            candidate_id = candidate.get("id")
            preview_url = candidate.get("preview_url")
            if not candidate_id or candidate_id == exclude_id or not preview_url:
                continue

            preview_path = temp_path / f"candidate_{candidate_id}.mp3"
            try:
                self.deezer.download_preview(preview_url, str(preview_path))
                embedding = self.embedder.embed(str(preview_path))
                similarity = self.embedder.similarity(query_embedding, embedding)
                enriched = candidate.copy()
                enriched["similarity"] = similarity
                results.append(enriched)
            except Exception as exc:  # pragma: no cover
                logger.debug("Skipping candidate %s: %s", candidate_id, exc)

        return results


_style_recommendation_service: Optional[StyleRecommendationService] = None


def get_style_recommendation_service() -> StyleRecommendationService:
    global _style_recommendation_service
    if _style_recommendation_service is None:
        _style_recommendation_service = StyleRecommendationService()
    return _style_recommendation_service
