#!/usr/bin/env python3
"""
Script to test Deezer API service independently.

This script allows testing the Deezer service without requiring
the CLAP model or vector database.

Usage:
    python scripts/test_deezer.py                    # Interactive mode
    python scripts/test_deezer.py search "Queen"     # Search command
    python scripts/test_deezer.py metadata 3135556   # Get metadata
    python scripts/test_deezer.py top 10             # Get top 10 tracks
"""

import sys
import logging
from pathlib import Path
import argparse
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.deezer_service import get_deezer_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_search(query: str):
    """Test search functionality."""
    print("\n" + "=" * 60)
    print(f"Testing Search: '{query}'")
    print("=" * 60)

    try:
        deezer = get_deezer_service()
        result = deezer.search_tracks(query, limit=1)

        if result:
            print("\n✓ Search successful!")
            print("\nTrack details:")
            print(f"  ID: {result['id']}")
            print(f"  Title: {result['title']}")
            print(f"  Artist: {result['artist']}")
            print(f"  Rank: {result['rank']}")
            print(f"  Preview URL: {result['preview_url']}")
            print(f"  Cover: {result['cover']}")
            return True
        else:
            print("\n✗ No results found")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def test_metadata(track_id: str):
    """Test metadata retrieval."""
    print("\n" + "=" * 60)
    print(f"Testing Metadata Retrieval: Track ID {track_id}")
    print("=" * 60)

    try:
        deezer = get_deezer_service()
        result = deezer.get_track_metadata(track_id)

        if result:
            print("\n✓ Metadata retrieved successfully!")
            print("\nTrack details:")
            print(f"  ID: {result['id']}")
            print(f"  Title: {result['title']}")
            print(f"  Artist: {result['artist']}")
            print(f"  Duration: {result['duration']}s")
            print(f"  Rank: {result['rank']}")
            print(f"  Preview URL: {result['preview_url']}")
            print(f"  Cover: {result['cover']}")
            return True
        else:
            print("\n✗ Track not found")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def test_download_preview(track_id: str):
    """Test preview download."""
    print("\n" + "=" * 60)
    print(f"Testing Preview Download: Track ID {track_id}")
    print("=" * 60)

    try:
        deezer = get_deezer_service()

        # Get metadata first
        metadata = deezer.get_track_metadata(track_id)
        if not metadata or not metadata.get('preview_url'):
            print("\n✗ No preview available for this track")
            return False

        print(f"\nTrack: {metadata['title']} by {metadata['artist']}")
        print(f"Downloading from: {metadata['preview_url']}")

        # Download
        file_path = deezer.download_preview(metadata['preview_url'])

        # Check file
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            print(f"\n✓ Download successful!")
            print(f"  File: {file_path}")
            print(f"  Size: {file_size / 1024:.1f} KB")

            # Cleanup
            Path(file_path).unlink()
            print(f"  Cleaned up temporary file")
            return True
        else:
            print("\n✗ Download failed")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def test_top_tracks(count: int = 10):
    """Test fetching top tracks."""
    print("\n" + "=" * 60)
    print(f"Testing Top Tracks: Fetching {count} tracks")
    print("=" * 60)

    try:
        deezer = get_deezer_service()
        tracks = deezer.get_top_tracks(total_count=count)

        if tracks:
            print(f"\n✓ Fetched {len(tracks)} tracks successfully!")
            print("\nTop tracks:")

            for i, track in enumerate(tracks[:10], 1):  # Show first 10
                has_preview = "✓" if track.get('preview_url') else "✗"
                print(f"  {i:2d}. {track['title']:<30} by {track['artist']:<20} [Preview: {has_preview}]")

            # Statistics
            with_preview = sum(1 for t in tracks if t.get('preview_url'))
            print(f"\nStatistics:")
            print(f"  Total tracks: {len(tracks)}")
            print(f"  With preview: {with_preview} ({with_preview/len(tracks)*100:.1f}%)")
            print(f"  Without preview: {len(tracks) - with_preview}")

            return True
        else:
            print("\n✗ No tracks found")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def interactive_mode():
    """Interactive test mode."""
    print("\n" + "=" * 60)
    print("Deezer Service Test - Interactive Mode")
    print("=" * 60)

    while True:
        print("\nAvailable tests:")
        print("  1. Search for a track")
        print("  2. Get track metadata by ID")
        print("  3. Download preview")
        print("  4. Get top tracks")
        print("  5. Run all tests")
        print("  0. Exit")

        choice = input("\nSelect option (0-5): ").strip()

        if choice == '0':
            print("\nGoodbye!")
            break

        elif choice == '1':
            query = input("Enter search query: ").strip()
            if query:
                test_search(query)

        elif choice == '2':
            track_id = input("Enter track ID: ").strip()
            if track_id:
                test_metadata(track_id)

        elif choice == '3':
            track_id = input("Enter track ID: ").strip()
            if track_id:
                test_download_preview(track_id)

        elif choice == '4':
            count = input("Number of tracks (default 10): ").strip()
            count = int(count) if count else 10
            test_top_tracks(count)

        elif choice == '5':
            print("\n" + "=" * 60)
            print("Running All Tests")
            print("=" * 60)

            results = []
            results.append(("Search", test_search("Bohemian Rhapsody")))
            results.append(("Metadata", test_metadata("3135556")))
            results.append(("Download", test_download_preview("3135556")))
            results.append(("Top Tracks", test_top_tracks(10)))

            print("\n" + "=" * 60)
            print("Test Summary")
            print("=" * 60)
            for name, result in results:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"  {name:<15} {status}")

            passed = sum(1 for _, r in results if r)
            print(f"\nTotal: {passed}/{len(results)} tests passed")

        else:
            print("Invalid option, please try again")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Deezer API service"
    )
    parser.add_argument(
        'command',
        nargs='?',
        choices=['search', 'metadata', 'download', 'top', 'all'],
        help='Test command to run'
    )
    parser.add_argument(
        'arg',
        nargs='?',
        help='Argument for the command (query/track_id/count)'
    )

    args = parser.parse_args()

    # Interactive mode if no command
    if args.command is None:
        interactive_mode()
        return

    # Run specific command
    if args.command == 'search':
        if not args.arg:
            print("Error: search requires a query")
            sys.exit(1)
        success = test_search(args.arg)

    elif args.command == 'metadata':
        if not args.arg:
            print("Error: metadata requires a track ID")
            sys.exit(1)
        success = test_metadata(args.arg)

    elif args.command == 'download':
        if not args.arg:
            print("Error: download requires a track ID")
            sys.exit(1)
        success = test_download_preview(args.arg)

    elif args.command == 'top':
        count = int(args.arg) if args.arg else 10
        success = test_top_tracks(count)

    elif args.command == 'all':
        print("\n" + "=" * 60)
        print("Running All Tests")
        print("=" * 60)

        results = []
        results.append(("Search", test_search("Bohemian Rhapsody")))
        results.append(("Metadata", test_metadata("3135556")))
        results.append(("Download", test_download_preview("3135556")))
        results.append(("Top Tracks", test_top_tracks(10)))

        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {name:<15} {status}")

        passed = sum(1 for _, r in results if r)
        print(f"\nTotal: {passed}/{len(results)} tests passed")
        success = passed == len(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
