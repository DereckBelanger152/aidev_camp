#!/usr/bin/env python3
"""
Script to add songs to the vector database by search query.

This script:
1. Searches Deezer for tracks matching a query
2. Downloads preview audio for each track
3. Generates embeddings using CLAP model
4. Stores embeddings in ChromaDB

Usage:
    python scripts/add_songs_by_query.py "artist name" --count 10
    python scripts/add_songs_by_query.py "genre" --count 20 --skip-existing
"""

import sys
import os
import argparse
import logging
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.deezer_service import get_deezer_service
from app.services.embedding_service import get_embedding_service
from app.services.vector_db_service import get_vector_db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_songs_by_query(query: str, count: int = 10, skip_existing: bool = True):
    """
    Add songs matching a search query to the vector database.

    Args:
        query: Search query for Deezer
        count: Number of tracks to add
        skip_existing: If True, skip tracks that already exist in database
    """
    logger.info("=" * 60)
    logger.info(f"Adding Songs by Query: '{query}'")
    logger.info("=" * 60)

    try:
        # Initialize services
        logger.info("Initializing services...")
        deezer_service = get_deezer_service()
        embedding_service = get_embedding_service()
        vector_db = get_vector_db_service()

        # Check database status
        existing_count = vector_db.count_tracks()
        logger.info(f"Current database size: {existing_count} tracks")

        # Step 1: Search for tracks
        logger.info(f"\nStep 1/3: Searching Deezer for '{query}'...")
        logger.info(f"Fetching up to {count} tracks...\n")

        tracks = deezer_service.search_tracks(query, limit=count, return_all=True)

        if not tracks:
            logger.error(f"No tracks found for query: '{query}'")
            return

        logger.info(f"✓ Found {len(tracks)} tracks")

        # Display found tracks
        logger.info("\nTracks found:")
        for idx, track in enumerate(tracks, 1):
            has_preview = "✓" if track.get('preview_url') else "✗"
            logger.info(f"  {idx:2d}. {track['title']:<30} by {track['artist']:<20} [Preview: {has_preview}]")

        # Step 2: Process each track
        logger.info(f"\nStep 2/3: Processing {len(tracks)} tracks...")

        success_count = 0
        skip_count = 0
        error_count = 0

        start_time = time.time()

        for idx, track in enumerate(tracks, 1):
            track_id = track['id']

            try:
                # Check if already exists
                if skip_existing and vector_db.track_exists(track_id):
                    logger.info(f"[{idx}/{len(tracks)}] Track {track_id} already exists, skipping")
                    skip_count += 1
                    continue

                # Check if preview available
                if not track.get('preview_url'):
                    logger.warning(f"[{idx}/{len(tracks)}] Track {track_id} has no preview, skipping")
                    skip_count += 1
                    continue

                # Download preview
                logger.info(f"[{idx}/{len(tracks)}] Processing: {track['title']} by {track['artist']}")
                audio_file = deezer_service.download_preview(track['preview_url'])

                try:
                    # Generate embedding
                    embedding = embedding_service.generate_embedding(audio_file)

                    # Store in database
                    vector_db.add_track(
                        track_id=track_id,
                        embedding=embedding,
                        metadata={
                            'title': track['title'],
                            'artist': track['artist'],
                            'rank': track.get('rank', 0),
                            'preview_url': track['preview_url'],
                            'cover': track.get('cover'),
                            'position': track.get('position', idx)
                        }
                    )

                    success_count += 1
                    logger.info(f"[{idx}/{len(tracks)}] ✓ Added successfully")

                finally:
                    # Cleanup audio file
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

                # Rate limiting: small delay between requests
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[{idx}/{len(tracks)}] ✗ Error processing track {track_id}: {e}")
                error_count += 1
                continue

        # Step 3: Summary
        total_time = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("Operation Complete!")
        logger.info("=" * 60)
        logger.info(f"Query: '{query}'")
        logger.info(f"✓ Successfully added: {success_count} tracks")
        logger.info(f"⊘ Skipped: {skip_count} tracks")
        logger.info(f"✗ Errors: {error_count} tracks")
        logger.info(f"Total time: {total_time:.1f} seconds")

        if success_count > 0:
            logger.info(f"Average time per track: {total_time/success_count:.1f}s")

        logger.info(f"\nFinal database size: {vector_db.count_tracks()} tracks")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\n\nOperation interrupted by user")
        logger.info(f"Current database size: {vector_db.count_tracks()} tracks")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add songs to vector database by search query",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add 10 songs by Queen:
    python scripts/add_songs_by_query.py "Queen" --count 10

  Add 20 rock songs:
    python scripts/add_songs_by_query.py "rock" --count 20

  Add songs without skipping existing:
    python scripts/add_songs_by_query.py "jazz" --count 15 --no-skip-existing
        """
    )
    parser.add_argument(
        'query',
        type=str,
        help='Search query for Deezer (artist, song, genre, etc.)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of tracks to add (default: 10)'
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Do not skip tracks that already exist in database'
    )

    args = parser.parse_args()

    # Validate count
    if args.count < 1:
        logger.error("Count must be at least 1")
        sys.exit(1)

    if args.count > 100:
        logger.warning(f"Large count ({args.count}) may take a while")

    # Run operation
    add_songs_by_query(
        query=args.query,
        count=args.count,
        skip_existing=not args.no_skip_existing
    )


if __name__ == "__main__":
    main()
