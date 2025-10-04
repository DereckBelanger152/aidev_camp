import requests
import logging
from typing import Optional, Dict, List
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

DEEZER_API_BASE = "https://api.deezer.com"


class DeezerService:
    """Service for interacting with the Deezer API."""

    def __init__(self):
        self.base_url = DEEZER_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicRecommendationApp/1.0'
        })

    def _parse_track(self, track_data: Dict) -> Dict:
        """
        Parse raw track data from Deezer API.

        Args:
            track_data: Raw track data from API

        Returns:
            Standardized track dictionary
        """
        return {
            'id': str(track_data['id']),
            'title': track_data['title'],
            'artist': track_data['artist']['name'],
            'preview_url': track_data.get('preview'),
            'cover': track_data['album'].get('cover_big') or track_data['album'].get('cover_medium'),
            'rank': track_data.get('rank', 0)
        }

    def search_tracks(self, query: str, limit: int = 1, return_all: bool = False):
        """
        Search for tracks by name.

        Args:
            query: Search query (track name)
            limit: Maximum number of results
            return_all: If True, return all results; if False, return first result only

        Returns:
            Single track dict (return_all=False) or list of tracks (return_all=True) or None
        """
        try:
            url = f"{self.base_url}/search"
            params = {
                'q': query,
                'limit': limit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            tracks_data = data.get('data', [])

            if not tracks_data:
                return [] if return_all else None

            tracks = [self._parse_track(track) for track in tracks_data]

            return tracks if return_all else tracks[0]

        except Exception as e:
            logger.error(f"Error searching tracks: {e}")
            raise

    def get_track_metadata(self, track_id: str) -> Optional[Dict]:
        """
        Get detailed metadata for a track.

        Args:
            track_id: Deezer track ID

        Returns:
            Track metadata
        """
        try:
            url = f"{self.base_url}/track/{track_id}"
            response = self.session.get(url)
            response.raise_for_status()

            track = response.json()

            return {
                'id': str(track['id']),
                'title': track['title'],
                'artist': track['artist']['name'],
                'preview_url': track.get('preview'),
                'cover': track['album'].get('cover_big') or track['album'].get('cover_medium'),
                'rank': track.get('rank', 0),
                'duration': track.get('duration', 0)
            }

        except Exception as e:
            logger.error(f"Error fetching track metadata: {e}")
            raise

    def download_preview(self, preview_url: str, output_path: Optional[str] = None) -> str:
        """
        Download audio preview from Deezer.

        Args:
            preview_url: URL to preview MP3
            output_path: Optional output path, creates temp file if not provided

        Returns:
            Path to downloaded file
        """
        try:
            if output_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.mp3',
                    prefix='deezer_preview_'
                )
                output_path = temp_file.name
                temp_file.close()

            # Download preview
            response = self.session.get(preview_url, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded preview to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error downloading preview: {e}")
            raise

    def get_chart_tracks(self, limit: int = 100, index: int = 0) -> List[Dict]:
        """
        Get top chart tracks from Deezer.

        Args:
            limit: Number of tracks to fetch (max 100 per request)
            index: Starting index for pagination

        Returns:
            List of track metadata
        """
        try:
            url = f"{self.base_url}/chart/0/tracks"
            params = {
                'limit': min(limit, 100),
                'index': index
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            tracks = []

            for track in data.get('data', []):
                tracks.append({
                    'id': str(track['id']),
                    'title': track['title'],
                    'artist': track['artist']['name'],
                    'preview_url': track.get('preview'),
                    'cover': track['album'].get('cover_big') or track['album'].get('cover_medium'),
                    'rank': track.get('rank', 0),
                    'position': track.get('position', index + len(tracks))
                })

            return tracks

        except Exception as e:
            logger.error(f"Error fetching chart tracks: {e}")
            raise

    def get_top_tracks(self, total_count: int = 1000) -> List[Dict]:
        """
        Get top N tracks from Deezer charts using pagination.

        Args:
            total_count: Total number of tracks to fetch

        Returns:
            List of track metadata
        """
        all_tracks = []
        index = 0
        batch_size = 100

        while len(all_tracks) < total_count:
            remaining = total_count - len(all_tracks)
            limit = min(batch_size, remaining)

            tracks = self.get_chart_tracks(limit=limit, index=index)

            if not tracks:
                break

            all_tracks.extend(tracks)
            index += len(tracks)

            logger.info(f"Fetched {len(all_tracks)}/{total_count} tracks")

        return all_tracks[:total_count]


# Global instance
_deezer_service: Optional[DeezerService] = None


def get_deezer_service() -> DeezerService:
    """Get or create the global Deezer service instance."""
    global _deezer_service
    if _deezer_service is None:
        _deezer_service = DeezerService()
    return _deezer_service
