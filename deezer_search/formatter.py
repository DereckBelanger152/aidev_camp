from __future__ import annotations

from typing import Iterable

from .track import DeezerTrack


class TrackFormatter:
    """Formats track collections for CLI output."""

    def format(self, tracks: Iterable[DeezerTrack]) -> str:
        lines = []
        for index, track in enumerate(tracks, start=1):
            preview_info = track.preview or "No preview available"
            lines.append(
                f"{index}. {track.title} - {track.artist} (Album: {track.album})\n"
                f"   Track ID: {track.id}\n"
                f"   Listen: {track.link}\n"
                f"   Preview: {preview_info}"
            )
        return "\n".join(lines) if lines else "No tracks found."
