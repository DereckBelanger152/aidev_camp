#!/usr/bin/env python3
"""
Script to initialize the vector database with top tracks from Deezer.

This script:
1. Fetches top N tracks from Deezer charts
2. Downloads preview audio for each track
3. Generates embeddings using OpenL3 model
4. Stores embeddings in ChromaDB

Usage:
    python scripts/init_vector_db.py [--count N] [--reset] [--resume]
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


def init_database(count: int = 1000, reset: bool = False, resume: bool = False):
    """
    Initialize the vector database with top tracks.

    Args:
        count: Number of tracks to index
        reset: If True, reset database before initializing
        resume: If True, skip already indexed tracks
    """
    logger.info("=" * 60)
    logger.info("Vector Database Initialization")
    logger.info("=" * 60)

    try:
        # Initialize services
        logger.info("Initializing services...")
        deezer_service = get_deezer_service()
        embedding_service = get_embedding_service()
        vector_db = get_vector_db_service()

        # Reset if requested
        if reset:
            logger.warning("Resetting database...")
            vector_db.reset_database()
            logger.info("✓ Database reset complete")

        # Check existing tracks
        existing_count = vector_db.count_tracks()
        logger.info(f"Current database size: {existing_count} tracks")

        if existing_count >= count and not reset:
            logger.info(f"Database already has {existing_count} tracks (target: {count})")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                logger.info("Initialization cancelled")
                return

        # Step 1: Fetch top tracks from Deezer
        logger.info(f"\nStep 1/3: Fetching top {count} tracks from Deezer...")
        tracks = deezer_service.get_top_tracks(total_count=count)
        logger.info(f"✓ Fetched {len(tracks)} tracks")

        if not tracks:
            logger.error("No tracks fetched from Deezer. Aborting.")
            return

        # Step 2: Process each track
        logger.info(f"\nStep 2/3: Processing {len(tracks)} tracks...")
        logger.info("This may take 30-60 minutes depending on your connection\n")

        success_count = 0
        skip_count = 0
        error_count = 0

        start_time = time.time()

        for idx, track in enumerate(tracks, 1):
            track_id = track['id']

            try:
                # Check if already exists (for resume functionality)
                if resume and vector_db.track_exists(track_id):
                    logger.info(f"[{idx}/{len(tracks)}] Track {track_id} already exists, skipping")
                    skip_count += 1
                    continue

                # Check if preview available
                if not track.get('preview_url'):
                    logger.warning(f"[{idx}/{len(tracks)}] Track {track_id} has no preview, skipping")
                    skip_count += 1
                    continue

                # Download preview
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

                    # Progress logging
                    if success_count % 10 == 0:
                        elapsed = time.time() - start_time
                        avg_time = elapsed / success_count
                        remaining = (len(tracks) - idx) * avg_time

                        logger.info(
                            f"[{idx}/{len(tracks)}] Progress: {success_count} indexed, "
                            f"{skip_count} skipped, {error_count} errors | "
                            f"ETA: {remaining/60:.1f} min"
                        )

                finally:
                    # Cleanup audio file
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

                # Rate limiting: small delay between requests
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[{idx}/{len(tracks)}] Error processing track {track_id}: {e}")
                error_count += 1
                continue

        # Step 3: Summary
        total_time = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("Initialization Complete!")
        logger.info("=" * 60)
        logger.info(f"✓ Successfully indexed: {success_count} tracks")
        logger.info(f"⊘ Skipped: {skip_count} tracks")
        logger.info(f"✗ Errors: {error_count} tracks")
        logger.info(f"Total time: {total_time/60:.1f} minutes")
        logger.info(f"Average time per track: {total_time/success_count:.1f}s")
        logger.info(f"\nFinal database size: {vector_db.count_tracks()} tracks")
        logger.info("=" * 60)

        if success_count < count * 0.8:
            logger.warning(
                f"\n⚠️  Warning: Only {success_count}/{count} tracks indexed successfully. "
                "This may affect recommendation quality."
            )

    except KeyboardInterrupt:
        logger.warning("\n\nInitialization interrupted by user")
        logger.info(f"Current database size: {vector_db.count_tracks()} tracks")
        logger.info("Run with --resume to continue from where you left off")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Fatal error during initialization: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize vector database with Deezer top tracks"
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1000,
        help='Number of tracks to index (default: 1000)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database before initializing'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume initialization, skip existing tracks'
    )

    args = parser.parse_args()

    # Validate count
    if args.count < 1:
        logger.error("Count must be at least 1")
        sys.exit(1)

    if args.count > 2000:
        logger.warning(f"Large count ({args.count}) may take several hours")

    # Run initialization
    init_database(
        count=args.count,
        reset=args.reset,
        resume=args.resume
    )


if __name__ == "__main__":
    main()
