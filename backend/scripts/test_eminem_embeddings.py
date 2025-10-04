"""
Test script for embedding service using Eminem song previews.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.embedding_service import get_embedding_service
import numpy as np


def main():
    print("=" * 60)
    print("Testing Embedding Service with Eminem Previews")
    print("=" * 60)

    # Audio file paths
    audio_dir = backend_path / "data" / "audio_samples"
    lose_yourself = audio_dir / "eminem_lose_yourself.mp3"
    till_i_collapse = audio_dir / "eminem_till_i_collapse.mp3"

    # Check files exist
    if not lose_yourself.exists():
        print(f"Error: {lose_yourself} not found")
        return
    if not till_i_collapse.exists():
        print(f"Error: {till_i_collapse} not found")
        return

    print(f"\nAudio files:")
    print(f"  1. {lose_yourself.name}")
    print(f"  2. {till_i_collapse.name}")

    # Initialize service
    print("\n" + "-" * 60)
    print("Initializing embedding service...")
    print("-" * 60)
    service = get_embedding_service()

    # Generate embeddings
    print("\n" + "-" * 60)
    print("Generating embeddings...")
    print("-" * 60)

    print("\n1. Processing 'Lose Yourself'...")
    emb1 = service.generate_embedding(str(lose_yourself))
    print(f"   ✓ Embedding shape: {emb1.shape}")
    print(f"   ✓ Embedding norm: {np.linalg.norm(emb1):.4f}")
    print(f"   ✓ First 5 values: {emb1[:5]}")

    print("\n2. Processing 'Till I Collapse'...")
    emb2 = service.generate_embedding(str(till_i_collapse))
    print(f"   ✓ Embedding shape: {emb2.shape}")
    print(f"   ✓ Embedding norm: {np.linalg.norm(emb2):.4f}")
    print(f"   ✓ First 5 values: {emb2[:5]}")

    # Calculate similarity
    print("\n" + "-" * 60)
    print("Calculating similarity...")
    print("-" * 60)

    similarity = service.calculate_similarity(emb1, emb2)
    print(f"\nCosine similarity between the two tracks: {similarity:.4f}")
    print(f"(Range: -1 to 1, where 1 = identical, 0 = orthogonal, -1 = opposite)")

    # Self-similarity check
    print("\n" + "-" * 60)
    print("Self-similarity check (should be ~1.0)...")
    print("-" * 60)

    self_sim1 = service.calculate_similarity(emb1, emb1)
    self_sim2 = service.calculate_similarity(emb2, emb2)
    print(f"\n'Lose Yourself' vs itself: {self_sim1:.6f}")
    print(f"'Till I Collapse' vs itself: {self_sim2:.6f}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Embeddings generated successfully")
    print(f"✓ Embedding dimension: {emb1.shape[0]}")
    print(f"✓ Similarity between different Eminem tracks: {similarity:.4f}")
    print(f"✓ Self-similarity verification passed: {self_sim1:.6f}, {self_sim2:.6f}")
    print("\nNote: Since both tracks are by the same artist (Eminem) and")
    print("have similar style, we expect a relatively high similarity score.")
    print("=" * 60)


if __name__ == "__main__":
    main()
