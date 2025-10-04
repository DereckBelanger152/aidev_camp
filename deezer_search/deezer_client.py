from __future__ import annotations

import logging
from typing import List, Optional

import requests

from .track import DeezerTrack


class DeezerClient:
    """Client wrapper around Deezer's public API."""

    search_url: str = "https://api.deezer.com/search"

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)

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
            )
            for item in payload.get("data", [])
        ]
