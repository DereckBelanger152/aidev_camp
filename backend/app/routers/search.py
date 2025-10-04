from fastapi import APIRouter, HTTPException
import logging
from typing import List

from app.models.schemas import SearchRequest, TrackInfo
from app.services.deezer_service import get_deezer_service
from app.services.vector_db_service import get_vector_db_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=TrackInfo)
async def search_track(request: SearchRequest):
    """
    Search for a track by name using Deezer API.

    Args:
        request: SearchRequest with query string

    Returns:
        TrackInfo with first match from Deezer

    Raises:
        HTTPException: If no track found or API error
    """
    try:
        logger.info(f"Searching for track: {request.query}")

        deezer_service = get_deezer_service()
        track = deezer_service.search_tracks(request.query, limit=1)

        if not track:
            logger.warning(f"No track found for query: {request.query}")
            raise HTTPException(
                status_code=404,
                detail=f"No track found for '{request.query}'. Please check spelling and try again."
            )

        # Add confirmation message
        track['message'] = "C'est bien ce morceau que vous voulez rechercher?"

        logger.info(f"Found track: {track['title']} by {track['artist']} (ID: {track['id']})")

        return TrackInfo(**track)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching track: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching track: {str(e)}"
        )


@router.get("/trending", response_model=List[TrackInfo])
async def get_trending_tracks(limit: int = 8):
    """
    Get trending/popular tracks from the database.

    Returns the top tracks sorted by popularity (rank).

    Args:
        limit: Number of tracks to return (default: 8)

    Returns:
        List of TrackInfo objects

    Raises:
        HTTPException: If database error
    """
    try:
        logger.info(f"Fetching {limit} trending tracks")

        vector_db = get_vector_db_service()

        # Get all tracks from the database
        results = vector_db.collection.get(
            include=['metadatas']
        )

        if not results['ids'] or not results['metadatas']:
            logger.warning("No tracks found in database")
            return []

        # Convert to list of tracks with metadata
        tracks = []
        for track_id, metadata in zip(results['ids'], results['metadatas']):
            tracks.append({
                'id': track_id,
                'title': metadata.get('title', 'Unknown'),
                'artist': metadata.get('artist', 'Unknown'),
                'preview_url': metadata.get('preview_url', ''),
                'cover': metadata.get('cover', ''),
                'rank': metadata.get('rank', 0)
            })

        # Sort by popularity (rank descending)
        tracks.sort(key=lambda x: x['rank'], reverse=True)

        # Take top N tracks
        top_tracks = tracks[:limit]

        logger.info(f"Returning {len(top_tracks)} trending tracks")

        return [TrackInfo(**track) for track in top_tracks]

    except Exception as e:
        logger.error(f"Error fetching trending tracks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trending tracks: {str(e)}"
        )
