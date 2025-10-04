from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, List

from .normalizer import TextNormalizer
from .track import DeezerTrack


class TrackRanker:
    """Ranks tracks based on normalized title similarity."""

    def __init__(self, normalizer: TextNormalizer | None = None) -> None:
        self.normalizer = normalizer or TextNormalizer()

    def rank(self, query: str, tracks: Iterable[DeezerTrack]) -> List[DeezerTrack]:
        normalized_query = self.normalizer.normalize(query)

        def sort_key(track: DeezerTrack) -> tuple[int, float]:
            normalized_title = self.normalizer.normalize(track.title)
            exact_match = int(normalized_title == normalized_query)
            similarity = SequenceMatcher(None, normalized_query, normalized_title).ratio()
            return exact_match, similarity

        ranked = sorted(tracks, key=sort_key, reverse=True)
        return ranked
