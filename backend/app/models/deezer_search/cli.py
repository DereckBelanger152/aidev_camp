from __future__ import annotations

import argparse
import logging
from typing import Iterable, Optional

from .formatter import TrackFormatter
from .search_model import DeezerSongSearchModel
from .track import DeezerTrack


class SongSearchCLI:
    """Command-line interface for Deezer song search."""

    def __init__(
        self,
        model: Optional[DeezerSongSearchModel] = None,
        formatter: Optional[TrackFormatter] = None,
    ) -> None:
        self.model = model or DeezerSongSearchModel()
        self.formatter = formatter or TrackFormatter()

    def run(self, argv: Optional[Iterable[str]] = None) -> int:
        args = self._parse_args(argv)
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(name)s - %(levelname)s - %(message)s",
        )

        try:
            tracks = self.model.predict(args.song_name, limit=args.limit)
        except Exception as err:  # pragma: no cover - CLI catch-all
            logging.error("Song search failed: %s", err)
            return 1

        print(self.formatter.format(tracks))
        return 0

    @staticmethod
    def _parse_args(argv: Optional[Iterable[str]]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Find a song on Deezer by name.")
        parser.add_argument("song_name", help="Name of the song to search for.")
        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            default=3,
            help="Maximum number of tracks to return (default: 3).",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose logging for debugging purposes.",
        )
        return parser.parse_args(argv)
