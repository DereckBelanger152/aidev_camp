from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeezerTrack:
    """Represents a track returned by the Deezer API."""

    id: int
    title: str
    artist: str
    album: str
    link: str
    preview: Optional[str]
