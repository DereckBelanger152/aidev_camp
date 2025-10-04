#!/usr/bin/env python3
"""
Script to verify the integrity of the vector database.

This script checks:
- Database exists and is accessible
- Track count
- Embedding dimensions
- Metadata completeness
- Sample similarity search

Usage:
    python scripts/verify_db.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vector_db_service import get_vector_db_service
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_database():
    """Verify the vector database integrity."""
    logger.info("=" * 60)
    logger.info("Vector Database Verification")
    logger.info("=" * 60)

    checks_passed = 0
    checks_failed = 0

    try:
        # Initialize service
        logger.info("\n[1/6] Initializing vector database service...")
        vector_db = get_vector_db_service()
        logger.info("✓ Database service initialized")
        checks_passed += 1

    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return False

    # Check 2: Track count
    try:
        logger.info("\n[2/6] Checking track count...")
        track_count = vector_db.count_tracks()

        if track_count == 0:
            logger.warning("⚠  Database is empty (0 tracks)")
            logger.info("   Run 'python scripts/init_vector_db.py' to initialize")
            checks_failed += 1
        else:
            logger.info(f"✓ Database contains {track_count} tracks")
            checks_passed += 1

    except Exception as e:
        logger.error(f"✗ Failed to count tracks: {e}")
        checks_failed += 1
        track_count = 0

    if track_count == 0:
        logger.info("\n" + "=" * 60)
        logger.warning("Database is empty. Cannot perform further checks.")
        logger.info("=" * 60)
        return False

    # Check 3: Sample track data
    try:
        logger.info("\n[3/6] Checking sample track data...")

        # Get a sample track
        results = vector_db.collection.get(limit=1, include=["embeddings", "metadatas"])

        if not results['ids']:
            logger.error("✗ No tracks found in collection")
            checks_failed += 1
        else:
            sample_id = results['ids'][0]
            sample_embedding = results['embeddings'][0]
            sample_metadata = results['metadatas'][0]

            logger.info(f"   Sample track ID: {sample_id}")
            logger.info(f"   Title: {sample_metadata.get('title', 'N/A')}")
            logger.info(f"   Artist: {sample_metadata.get('artist', 'N/A')}")
            logger.info(f"✓ Sample track retrieved successfully")
            checks_passed += 1

    except Exception as e:
        logger.error(f"✗ Failed to retrieve sample track: {e}")
        checks_failed += 1
        sample_embedding = None

    # Check 4: Embedding dimensions
    try:
        logger.info("\n[4/6] Checking embedding dimensions...")

        if sample_embedding is None:
            logger.error("✗ No sample embedding available")
            checks_failed += 1
        else:
            embedding_dim = len(sample_embedding)
            expected_dim = 512  # CLAP embedding dimension

            if embedding_dim == expected_dim:
                logger.info(f"✓ Embedding dimension correct: {embedding_dim}")
                checks_passed += 1
            else:
                logger.error(
                    f"✗ Unexpected embedding dimension: {embedding_dim} "
                    f"(expected {expected_dim})"
                )
                checks_failed += 1

            # Check normalization
            embedding_norm = np.linalg.norm(sample_embedding)
            if 0.95 <= embedding_norm <= 1.05:
                logger.info(f"✓ Embedding is normalized (norm: {embedding_norm:.3f})")
                checks_passed += 1
            else:
                logger.warning(
                    f"⚠  Embedding may not be normalized (norm: {embedding_norm:.3f})"
                )
                checks_failed += 1

    except Exception as e:
        logger.error(f"✗ Failed to check embedding dimensions: {e}")
        checks_failed += 1

    # Check 5: Metadata completeness
    try:
        logger.info("\n[5/6] Checking metadata completeness...")

        required_fields = ['title', 'artist', 'rank', 'preview_url', 'cover']
        missing_fields = []

        for field in required_fields:
            if field not in sample_metadata:
                missing_fields.append(field)

        if missing_fields:
            logger.warning(f"⚠  Missing metadata fields: {', '.join(missing_fields)}")
            checks_failed += 1
        else:
            logger.info("✓ All required metadata fields present")
            checks_passed += 1

    except Exception as e:
        logger.error(f"✗ Failed to check metadata: {e}")
        checks_failed += 1

    # Check 6: Sample similarity search
    try:
        logger.info("\n[6/6] Testing similarity search...")

        if sample_embedding is None:
            logger.error("✗ No sample embedding for testing")
            checks_failed += 1
        else:
            # Query with sample embedding
            query_embedding = np.array(sample_embedding)
            results = vector_db.query_similar(query_embedding, n_results=5)

            if results['ids'] and len(results['ids']) > 0:
                logger.info(f"✓ Similarity search working (found {len(results['ids'])} results)")
                logger.info(f"   Top match: {results['metadatas'][0].get('title')} "
                          f"(distance: {results['distances'][0]:.4f})")
                checks_passed += 1
            else:
                logger.error("✗ Similarity search returned no results")
                checks_failed += 1

    except Exception as e:
        logger.error(f"✗ Failed to test similarity search: {e}")
        checks_failed += 1

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    logger.info(f"✓ Checks passed: {checks_passed}")
    logger.info(f"✗ Checks failed: {checks_failed}")

    total_checks = checks_passed + checks_failed
    success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

    logger.info(f"Success rate: {success_rate:.1f}%")

    if checks_failed == 0:
        logger.info("\n🎉 Database is ready to use!")
        logger.info("=" * 60)
        return True
    elif checks_passed > checks_failed:
        logger.warning("\n⚠️  Database has some issues but may still work")
        logger.info("=" * 60)
        return True
    else:
        logger.error("\n❌ Database has critical issues and needs attention")
        logger.info("=" * 60)
        return False


def main():
    """Main entry point."""
    success = verify_database()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
