from fastapi import APIRouter, HTTPException
import logging

from app.models.schemas import SearchRequest, TrackInfo
from app.services.deezer_service import get_deezer_service

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
