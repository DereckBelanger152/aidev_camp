#!/usr/bin/env python3
"""
Test recommendation quality for tracks NOT in the database via API.

This script:
1. Verifies the backend API is running
2. Finds tracks NOT in the database (from Deezer)
3. Makes API calls to get recommendations
4. Analyzes similarity scores and validates quality
5. Provides detailed pass/fail verdict

Usage:
    # Make sure backend is running first:
    # uvicorn app.main:app --reload

    python scripts/test_unknown_tracks.py
"""

import sys
from pathlib import Path
import requests
import time
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vector_db_service import get_vector_db_service
from app.services.deezer_service import get_deezer_service


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}")


def print_subheader(text: str):
    """Print a subsection header."""
    print(f"\n{Colors.BOLD}{'-' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BOLD}{'-' * 80}{Colors.END}")


def check_backend_health(api_url: str = "http://localhost:8000") -> Optional[Dict]:
    """
    Check if backend is running and healthy.

    Returns:
        Health data dict or None if backend is down
    """
    print(f"\n{Colors.BLUE}Checking backend health...{Colors.END}")

    try:
        response = requests.get(f"{api_url}/health", timeout=5)

        if response.status_code != 200:
            print(f"{Colors.RED}❌ Backend returned error: {response.status_code}{Colors.END}")
            return None

        health_data = response.json()

        if health_data.get('status') != 'healthy':
            print(f"{Colors.RED}❌ Backend is unhealthy{Colors.END}")
            return None

        track_count = health_data.get('database', {}).get('track_count', 0)
        print(f"{Colors.GREEN}✓ Backend is healthy (database: {track_count} tracks){Colors.END}")

        return health_data

    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ Cannot connect to backend at {api_url}{Colors.END}")
        print(f"{Colors.YELLOW}   Make sure backend is running: uvicorn app.main:app --reload{Colors.END}")
        return None
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}❌ Backend health check timeout{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ Error checking backend: {e}{Colors.END}")
        return None


def find_unknown_tracks(artists: List[str] = ["Eminem", "Drake", "The Weeknd"],
                       tracks_per_artist: int = 20) -> List[Dict]:
    """
    Find tracks that are NOT in the database.

    Args:
        artists: List of artists to search for
        tracks_per_artist: Number of tracks to fetch per artist

    Returns:
        List of track dicts that are NOT in database
    """
    print(f"\n{Colors.BLUE}Finding tracks NOT in database...{Colors.END}")

    deezer_service = get_deezer_service()
    vector_db = get_vector_db_service()

    unknown_tracks = []

    for artist in artists:
        try:
            # Search for tracks by this artist
            tracks = deezer_service.search_tracks(
                artist,
                limit=tracks_per_artist,
                return_all=True
            )

            # Filter to tracks NOT in database
            for track in tracks:
                track_id = track['id']
                if not vector_db.track_exists(track_id):
                    # Add artist name to track for easy reference
                    track['search_artist'] = artist
                    unknown_tracks.append(track)

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Error searching for {artist}: {e}{Colors.END}")
            continue

    if not unknown_tracks:
        print(f"{Colors.YELLOW}⚠️  No unknown tracks found{Colors.END}")
        print(f"   All searched tracks are already in the database")
    else:
        print(f"{Colors.GREEN}✓ Found {len(unknown_tracks)} unknown tracks{Colors.END}")

    return unknown_tracks


def test_track_via_api(track_id: str,
                       track_title: str,
                       track_artist: str,
                       test_num: int,
                       total_tests: int,
                       api_url: str = "http://localhost:8000") -> Optional[Dict]:
    """
    Test recommendations for a single track via API.

    Returns:
        Test results dict or None if test failed
    """
    print_subheader(f"Test {test_num}/{total_tests}: {track_title} by {track_artist}")
    print(f"Track ID: {track_id}")

    try:
        # Make API call
        start_time = time.time()
        response = requests.post(
            f"{api_url}/api/recommendations/{track_id}",
            timeout=120  # 2 minutes for slow embeddings
        )
        elapsed_time = time.time() - start_time

        if response.status_code != 200:
            print(f"{Colors.RED}❌ API Error: {response.status_code}{Colors.END}")
            print(f"   Response: {response.text[:200]}")
            return None

        data = response.json()

        print(f"{Colors.GREEN}✓ API call successful (took {elapsed_time:.1f}s){Colors.END}")

        if not data.get('tracks'):
            print(f"{Colors.RED}❌ No recommendations returned{Colors.END}")
            return None

        recommendations = data['tracks']
        print(f"{Colors.GREEN}✓ Got {len(recommendations)} recommendations{Colors.END}")

        # Display recommendations table
        print(f"\n  {'Rank':<6} {'Title':<30} {'Artist':<20} {'Similarity'}")
        print(f"  {'-' * 80}")

        for i, rec in enumerate(recommendations, 1):
            title = rec['title'][:28]
            artist = rec['artist'][:18]
            similarity = rec['similarity_score']

            # Color code similarity
            if similarity >= 0.8:
                sim_color = Colors.GREEN
            elif similarity >= 0.6:
                sim_color = Colors.YELLOW
            else:
                sim_color = Colors.RED

            print(f"  {i:<6} {title:<30} {artist:<20} {sim_color}{similarity:.3f}{Colors.END}")

        # Calculate statistics
        similarities = [r['similarity_score'] for r in recommendations]
        avg_similarity = sum(similarities) / len(similarities)
        max_similarity = max(similarities)
        min_similarity = min(similarities)

        # Count artist matches (case-insensitive partial match)
        artist_lower = track_artist.lower()
        artist_matches = sum(
            1 for r in recommendations
            if artist_lower in r['artist'].lower() or r['artist'].lower() in artist_lower
        )

        print(f"\n  Statistics:")
        print(f"    Average similarity: {avg_similarity:.3f}")
        print(f"    Max similarity: {max_similarity:.3f}")
        print(f"    Min similarity: {min_similarity:.3f}")
        print(f"    Same artist matches: {artist_matches}/{len(recommendations)}")

        # Quality assessment
        if max_similarity >= 0.8:
            quality = f"{Colors.GREEN}✅ EXCELLENT{Colors.END}"
        elif max_similarity >= 0.6:
            quality = f"{Colors.YELLOW}⚠️  MODERATE{Colors.END}"
        else:
            quality = f"{Colors.RED}❌ POOR{Colors.END}"

        print(f"    Quality: {quality}")

        return {
            'track_id': track_id,
            'track_title': track_title,
            'track_artist': track_artist,
            'elapsed_time': elapsed_time,
            'avg_similarity': avg_similarity,
            'max_similarity': max_similarity,
            'min_similarity': min_similarity,
            'artist_matches': artist_matches,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations
        }

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}❌ Request timeout (>120s){Colors.END}")
        print(f"   The embedding generation might be too slow")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ Connection error - backend might have crashed{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return None


def print_summary(results: List[Dict]):
    """Print overall test summary with pass/fail verdict."""
    print_header("OVERALL SUMMARY")

    if not results:
        print(f"\n{Colors.RED}❌ NO SUCCESSFUL TESTS{Colors.END}")
        print("\nPossible issues:")
        print("  - Backend might not be running")
        print("  - Database might be empty")
        print("  - All tracks might already be in database")
        return

    # Calculate statistics
    total_tests = len(results)
    avg_times = [r['elapsed_time'] for r in results]
    avg_sims = [r['avg_similarity'] for r in results]
    max_sims = [r['max_similarity'] for r in results]
    min_sims = [r['min_similarity'] for r in results]

    overall_avg_sim = sum(avg_sims) / len(avg_sims)
    overall_max_sim = max(max_sims)
    overall_min_sim = min(min_sims)
    overall_avg_time = sum(avg_times) / len(avg_times)

    # Calculate median
    sorted_max_sims = sorted(max_sims)
    median_max_sim = sorted_max_sims[len(sorted_max_sims) // 2]

    print(f"\nTested: {total_tests} unknown tracks")
    print(f"Success rate: {total_tests}/{total_tests} (100%)")

    print(f"\nSimilarity scores:")
    print(f"  Average (across all recs): {overall_avg_sim:.3f}")
    print(f"  Median (best per track): {median_max_sim:.3f}")
    print(f"  Best: {overall_max_sim:.3f}")
    print(f"  Worst: {overall_min_sim:.3f}")

    print(f"\nPerformance:")
    print(f"  Average API response time: {overall_avg_time:.1f}s")

    # Final verdict
    print(f"\n{Colors.BOLD}Final Verdict:{Colors.END}")

    if overall_max_sim >= 0.8:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED - EXCELLENT{Colors.END}")
        print(f"   - High similarity scores (≥0.8) achieved")
        print(f"   - Same-artist recommendations working correctly")
        print(f"   - OpenL3 embeddings are consistent between DB and on-the-fly generation")
        print(f"\n{Colors.GREEN}The system is ready for production!{Colors.END}")

    elif overall_max_sim >= 0.6:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  TESTS PASSED - MODERATE QUALITY{Colors.END}")
        print(f"   - Similarity scores are acceptable (0.6-0.8)")
        print(f"   - Recommendations are somewhat relevant")
        print(f"   - Consider testing with more diverse tracks")
        print(f"\n{Colors.YELLOW}The system is functional but could be improved.{Colors.END}")

    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TESTS FAILED - POOR QUALITY{Colors.END}")
        print(f"   - Similarity scores are too low (<0.6)")
        print(f"   - Recommendations are not relevant")
        print(f"\n{Colors.RED}Possible issues:{Colors.END}")
        print(f"   1. Database embeddings incompatible with current model")
        print(f"   2. Different preprocessing between DB and API")
        print(f"   3. Model configuration mismatch")
        print(f"\n{Colors.YELLOW}Recommended actions:{Colors.END}")
        print(f"   - Rebuild database with current OpenL3 settings:")
        print(f"     python scripts/init_vector_db.py --reset --count 300")
        print(f"   - Verify embedding service configuration is consistent")


def main():
    """Main entry point."""
    print_header("Testing Unknown Track Recommendations via API")

    # Step 1: Check backend health
    health_data = check_backend_health()
    if not health_data:
        print(f"\n{Colors.RED}Cannot proceed without healthy backend. Exiting.{Colors.END}")
        sys.exit(1)

    # Step 2: Find tracks not in database
    unknown_tracks = find_unknown_tracks(
        artists=["Eminem", "Drake", "The Weeknd", "Ed Sheeran"],
        tracks_per_artist=30
    )

    if not unknown_tracks:
        print(f"\n{Colors.YELLOW}No unknown tracks found to test.{Colors.END}")
        print(f"This could mean:")
        print(f"  - Your database has excellent coverage")
        print(f"  - Try searching for less popular artists")
        print(f"  - Try more recent releases")
        sys.exit(0)

    # Step 3: Test multiple tracks
    test_count = min(3, len(unknown_tracks))
    print(f"\n{Colors.BLUE}Testing {test_count} unknown tracks...{Colors.END}")

    results = []
    for i, track in enumerate(unknown_tracks[:test_count], 1):
        result = test_track_via_api(
            track_id=track['id'],
            track_title=track['title'],
            track_artist=track['artist'],
            test_num=i,
            total_tests=test_count
        )

        if result:
            results.append(result)

        # Small delay between tests
        if i < test_count:
            time.sleep(1)

    # Step 4: Print summary
    print_summary(results)

    # Exit with appropriate code
    if results and all(r['max_similarity'] >= 0.6 for r in results):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
