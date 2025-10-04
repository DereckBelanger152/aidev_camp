#!/usr/bin/env python3
"""
Test recommendation quality by checking similarity scores.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vector_db_service import get_vector_db_service

def test_recommendations():
    db = get_vector_db_service()

    # Get a few sample tracks
    result = db.collection.get(limit=5, include=['embeddings', 'metadatas'])

    print("Testing recommendation quality...\n")
    print("=" * 80)

    for i, (track_id, embedding, metadata) in enumerate(zip(
        result['ids'], result['embeddings'], result['metadatas']
    )):
        print(f"\nTest {i+1}: {metadata.get('title')} by {metadata.get('artist')}")
        print("-" * 80)

        # Query similar tracks
        similar = db.query_similar(embedding, n_results=6)

        print(f"{'Rank':<6} {'Title':<30} {'Artist':<20} {'Distance':<10} {'Similarity'}")
        print("-" * 80)

        for rank, (sim_id, distance, sim_meta) in enumerate(zip(
            similar['ids'], similar['distances'], similar['metadatas']
        ), 1):
            similarity = max(0.0, min(1.0, 1 - distance))
            is_same = "★ SAME" if sim_id == track_id else ""
            print(f"{rank:<6} {sim_meta.get('title', 'Unknown')[:30]:<30} "
                  f"{sim_meta.get('artist', 'Unknown')[:20]:<20} "
                  f"{distance:<10.4f} {similarity:.4f} {is_same}")

        print()

if __name__ == "__main__":
    test_recommendations()
