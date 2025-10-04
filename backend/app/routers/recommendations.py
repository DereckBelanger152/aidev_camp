from fastapi import APIRouter, HTTPException, Path
import logging
import tempfile
import os
from typing import List

from app.models.schemas import (
    RecommendationTrack,
    RecommendationResponse,
    AddTracksRequest,
    AddTracksResponse
)
from app.services.deezer_service import get_deezer_service
from app.services.embedding_service import get_embedding_service
from app.services.vector_db_service import get_vector_db_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/recommendations/{track_id}", response_model=RecommendationResponse)
async def get_recommendations(
    track_id: str = Path(..., description="Deezer track ID")
):
    """
    Get song recommendations based on audio similarity.

    Workflow:
    1. Download preview audio for the given track
    2. Generate embedding using CLAP model
    3. Query vector database for top 10 similar tracks
    4. Filter by popularity and return top 3

    Args:
        track_id: Deezer track ID

    Returns:
        RecommendationResponse with top 3 similar tracks

    Raises:
        HTTPException: If track not found or processing error
    """
    audio_file = None

    try:
        logger.info(f"Getting recommendations for track ID: {track_id}")

        # Initialize services
        deezer_service = get_deezer_service()
        embedding_service = get_embedding_service()
        vector_db = get_vector_db_service()

        # Step 1: Get track metadata
        logger.info("Fetching track metadata...")
        track_metadata = deezer_service.get_track_metadata(track_id)

        if not track_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Track {track_id} not found"
            )

        if not track_metadata.get('preview_url'):
            raise HTTPException(
                status_code=400,
                detail="Track does not have a preview available"
            )

        # Step 2: Download preview audio
        logger.info("Downloading preview audio...")
        audio_file = deezer_service.download_preview(track_metadata['preview_url'])

        # Step 3: Generate embedding
        logger.info("Generating audio embedding...")
        embedding = embedding_service.generate_embedding(audio_file)

        # Step 4: Query vector database for similar tracks
        logger.info("Querying vector database...")
        results = vector_db.query_similar(embedding, n_results=10)

        if not results['ids']:
            logger.warning("No similar tracks found in database")
            return RecommendationResponse(
                tracks=[],
                source_track_id=track_id
            )

        # Step 5: Filter by popularity and get top 3
        logger.info("Filtering results by popularity...")
        recommendations = []

        for track_id_result, distance, metadata in zip(
            results['ids'],
            results['distances'],
            results['metadatas']
        ):
            # Skip if same track
            if track_id_result == track_id:
                continue

            # Convert distance to similarity score (1 - distance for cosine)
            similarity_score = 1 - distance

            recommendations.append({
                'id': track_id_result,
                'title': metadata.get('title', 'Unknown'),
                'artist': metadata.get('artist', 'Unknown'),
                'similarity_score': round(similarity_score, 3),
                'popularity': metadata.get('rank', 0),
                'preview_url': metadata.get('preview_url'),
                'cover': metadata.get('cover')
            })

        # Sort by popularity (rank) descending
        recommendations.sort(key=lambda x: x['popularity'], reverse=True)

        # Take top 3
        top_3 = recommendations[:3]

        logger.info(f"Returning {len(top_3)} recommendations")

        return RecommendationResponse(
            tracks=[RecommendationTrack(**track) for track in top_3],
            source_track_id=track_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )
    finally:
        # Cleanup temporary audio file
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                logger.debug(f"Cleaned up temporary file: {audio_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file: {e}")


@router.post("/admin/add-tracks", response_model=AddTracksResponse)
async def add_tracks_to_database(request: AddTracksRequest):
    """
    Add new tracks to the vector database.

    Admin endpoint for extending the database with additional tracks.

    Args:
        request: AddTracksRequest with list of track IDs

    Returns:
        AddTracksResponse with status and count

    Raises:
        HTTPException: If processing error
    """
    try:
        logger.info(f"Adding {len(request.track_ids)} tracks to database")

        deezer_service = get_deezer_service()
        embedding_service = get_embedding_service()
        vector_db = get_vector_db_service()

        added_count = 0
        skipped_count = 0

        for track_id in request.track_ids:
            try:
                # Check if already exists
                if vector_db.track_exists(track_id):
                    logger.info(f"Track {track_id} already exists, skipping")
                    skipped_count += 1
                    continue

                # Get metadata
                metadata = deezer_service.get_track_metadata(track_id)
                if not metadata or not metadata.get('preview_url'):
                    logger.warning(f"Track {track_id} has no preview, skipping")
                    skipped_count += 1
                    continue

                # Download and generate embedding
                audio_file = deezer_service.download_preview(metadata['preview_url'])
                try:
                    embedding = embedding_service.generate_embedding(audio_file)

                    # Add to database
                    vector_db.add_track(
                        track_id=track_id,
                        embedding=embedding,
                        metadata={
                            'title': metadata['title'],
                            'artist': metadata['artist'],
                            'rank': metadata.get('rank', 0),
                            'preview_url': metadata['preview_url'],
                            'cover': metadata.get('cover')
                        }
                    )

                    added_count += 1
                    logger.info(f"Added track {track_id}: {metadata['title']}")

                finally:
                    # Cleanup
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

            except Exception as e:
                logger.error(f"Error processing track {track_id}: {e}")
                skipped_count += 1
                continue

        logger.info(f"Completed: {added_count} added, {skipped_count} skipped")

        return AddTracksResponse(
            status="success",
            added_count=added_count,
            message=f"{added_count} tracks added to database ({skipped_count} skipped)"
        )

    except Exception as e:
        logger.error(f"Error adding tracks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding tracks: {str(e)}"
        )
