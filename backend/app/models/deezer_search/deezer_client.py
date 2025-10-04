from __future__ import annotations

import logging
from typing import Dict, List, Optional

import requests

from .track import DeezerTrack


class DeezerClient:
    """Client wrapper around Deezer's public API."""

    search_url: str = "https://api.deezer.com/search"
    genre_url: str = "https://api.deezer.com/genre"

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._genre_cache: Dict[int, Optional[str]] = {0: None}

    def search_tracks(self, query: str, *, limit: int, strict: bool = True) -> List[DeezerTrack]:
        """Perform a Deezer track search and map results to dataclasses."""

        params = {
            "q": f'track:"{query}"' if strict else query,
            "limit": max(1, limit),
        }
        self.logger.debug("Querying Deezer", extra={"params": params})
        response = self.session.get(self.search_url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return [
            DeezerTrack(
                id=int(item["id"]),
                title=item.get("title", ""),
                artist=item.get("artist", {}).get("name", ""),
                album=item.get("album", {}).get("title", ""),
                link=item.get("link", ""),
                preview=item.get("preview"),
                genre=self._extract_genre(item),
            )
            for item in payload.get("data", [])
        ]

    def _extract_genre(self, item: dict) -> Optional[str]:
        genre_id = item.get("genre_id") or item.get("album", {}).get("genre_id")
        if genre_id is None:
            return None
        try:
            genre_key = int(genre_id)
        except (TypeError, ValueError):
            return None
        if genre_key in self._genre_cache:
            return self._genre_cache[genre_key]
        try:
            response = self.session.get(f"{self.genre_url}/{genre_key}", timeout=10)
            response.raise_for_status()
            payload = response.json()
            name = None if payload.get("error") else payload.get("name")
        except requests.RequestException as err:
            self.logger.debug("Failed to resolve genre %s: %s", genre_key, err)
            name = None
        self._genre_cache[genre_key] = name
        return name
