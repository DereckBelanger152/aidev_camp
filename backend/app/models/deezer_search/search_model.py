from __future__ import annotations

import logging
from typing import List, Optional

from .cache import ResultCache
from .deezer_client import DeezerClient
from .normalizer import TextNormalizer
from .ranker import TrackRanker
from .track import DeezerTrack


class DeezerSongSearchModel:
    """Coordinates Deezer lookups, ranking, and caching."""

    def __init__(
        self,
        client: Optional[DeezerClient] = None,
        ranker: Optional[TrackRanker] = None,
        cache: Optional[ResultCache[DeezerTrack]] = None,
        normalizer: Optional[TextNormalizer] = None,
    ) -> None:
        base_normalizer = normalizer or TextNormalizer()
        self.client = client or DeezerClient()
        self.ranker = ranker or TrackRanker(base_normalizer)
        self.cache = cache or ResultCache[DeezerTrack]()
        self.normalizer = base_normalizer
        self.logger = logging.getLogger(self.__class__.__name__)

    def predict(self, song_name: str, *, limit: int = 5) -> List[DeezerTrack]:
        """Return best-matching tracks for a song name using heuristically ranked search."""

        if not song_name or not song_name.strip():
            raise ValueError("song_name must be a non-empty string")

        normalized_query = self.normalizer.normalize(song_name)
        sanitized_limit = max(1, limit)
        cache_key = (normalized_query, sanitized_limit)
        cached_tracks = self.cache.get(cache_key)
        if cached_tracks is not None:
            self.logger.debug("Returning cached result for %s", song_name)
            return list(cached_tracks)

        fetch_limit = max(2 * sanitized_limit, 5)
        tracks = self._fetch_tracks(song_name, fetch_limit, strict=True)
        if not tracks:
            self.logger.debug("No results for strict query, trying relaxed search")
            tracks = self._fetch_tracks(song_name, fetch_limit, strict=False)

        ranked_tracks = self.ranker.rank(song_name, tracks)
        trimmed_tracks = ranked_tracks[:sanitized_limit]
        self.cache.set(cache_key, tuple(trimmed_tracks))
        return trimmed_tracks

    def _fetch_tracks(self, song_name: str, limit: int, *, strict: bool) -> List[DeezerTrack]:
        return self.client.search_tracks(song_name.strip(), limit=limit, strict=strict)
