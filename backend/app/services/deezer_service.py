import requests
import logging
import unicodedata
from typing import Optional, Dict, List
from pathlib import Path
import tempfile
from difflib import SequenceMatcher

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
        self._genre_cache: Dict[int, Optional[str]] = {0: None}
        self._search_cache: Dict[tuple, Optional[Dict]] = {}

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for comparison (lowercase, remove accents).

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        return normalized.strip().casefold()

    def get_genre(self, genre_id: int) -> Optional[str]:
        """
        Get genre name by ID with caching.

        Args:
            genre_id: Deezer genre ID

        Returns:
            Genre name or None
        """
        if genre_id in self._genre_cache:
            return self._genre_cache[genre_id]

        try:
            url = f"{self.base_url}/genre/{genre_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            name = None if data.get('error') else data.get('name')
            self._genre_cache[genre_id] = name
            return name
        except Exception as e:
            logger.debug(f"Failed to resolve genre {genre_id}: {e}")
            self._genre_cache[genre_id] = None
            return None

    def search_tracks(
        self,
        query: str,
        limit: int = 1,
        strict: bool = False,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Search for tracks by name.

        Args:
            query: Search query (track name)
            limit: Maximum number of results
            strict: If True, use strict search (track:"query")
            use_cache: If True, use cached results

        Returns:
            First track found or None
        """
        # Check cache
        cache_key = (query, limit, strict)
        if use_cache and cache_key in self._search_cache:
            logger.debug(f"Returning cached result for: {query}")
            return self._search_cache[cache_key]

        try:
            url = f"{self.base_url}/search"
            search_query = f'track:"{query}"' if strict else query
            params = {
                'q': search_query,
                'limit': limit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                track = data['data'][0]
                result = {
                    'id': str(track['id']),
                    'title': track['title'],
                    'artist': track['artist']['name'],
                    'album': track['album'].get('title', ''),
                    'link': track.get('link', ''),
                    'preview_url': track.get('preview'),
                    'cover': track['album'].get('cover_big') or track['album'].get('cover_medium'),
                    'rank': track.get('rank', 0),
                    'genre': None
                }

                # Try to get genre
                genre_id = track.get('genre_id') or track.get('album', {}).get('genre_id')
                if genre_id:
                    result['genre'] = self.get_genre(int(genre_id))

                # Cache result
                if use_cache:
                    self._search_cache[cache_key] = result

                return result

            result = None
            if use_cache:
                self._search_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error searching tracks: {e}")
            raise

    def search_tracks_ranked(
        self,
        query: str,
        limit: int = 5,
        fallback: bool = True
    ) -> List[Dict]:
        """
        Search for tracks and rank by title similarity.

        Args:
            query: Search query (track name)
            limit: Maximum number of results
            fallback: If True and strict search fails, try relaxed search

        Returns:
            List of tracks ranked by similarity
        """
        try:
            # Try strict search first
            url = f"{self.base_url}/search"
            fetch_limit = max(2 * limit, 10)  # Fetch more for better ranking
            params = {
                'q': f'track:"{query}"',
                'limit': fetch_limit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            tracks = data.get('data', [])

            # Fallback to relaxed search if no results
            if not tracks and fallback:
                logger.debug(f"No strict results for '{query}', trying relaxed search")
                params['q'] = query
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                tracks = data.get('data', [])

            if not tracks:
                return []

            # Rank tracks by title similarity
            normalized_query = self.normalize_text(query)
            ranked_tracks = []

            for track in tracks:
                track_title = track['title']
                normalized_title = self.normalize_text(track_title)

                # Calculate similarity
                exact_match = int(normalized_title == normalized_query)
                similarity = SequenceMatcher(None, normalized_query, normalized_title).ratio()

                # Try to get genre
                genre = None
                genre_id = track.get('genre_id') or track.get('album', {}).get('genre_id')
                if genre_id:
                    genre = self.get_genre(int(genre_id))

                ranked_tracks.append({
                    'id': str(track['id']),
                    'title': track_title,
                    'artist': track['artist']['name'],
                    'album': track['album'].get('title', ''),
                    'link': track.get('link', ''),
                    'preview_url': track.get('preview'),
                    'cover': track['album'].get('cover_big') or track['album'].get('cover_medium'),
                    'rank': track.get('rank', 0),
                    'genre': genre,
                    '_exact_match': exact_match,
                    '_similarity': similarity
                })

            # Sort by exact match first, then similarity
            ranked_tracks.sort(key=lambda t: (t['_exact_match'], t['_similarity']), reverse=True)

            # Remove internal scoring fields
            for track in ranked_tracks:
                track.pop('_exact_match', None)
                track.pop('_similarity', None)

            return ranked_tracks[:limit]

        except Exception as e:
            logger.error(f"Error in ranked search: {e}")
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
