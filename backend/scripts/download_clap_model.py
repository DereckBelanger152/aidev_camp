#!/usr/bin/env python3
"""
Script to download the CLAP model locally.

This script downloads the CLAP model checkpoint from HuggingFace
and saves it to backend/models/clap/ directory.

Usage:
    python scripts/download_clap_model.py
"""

import sys
import requests
import logging
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_URL = "https://huggingface.co/lukewys/laion_clap/resolve/main/music_audioset_epoch_15_esc_90.14.pt"
MODEL_FILENAME = "music_audioset_epoch_15_esc_90.14.pt"


def download_file(url: str, destination: Path) -> bool:
    """
    Download a file with progress bar.

    Args:
        url: URL to download from
        destination: Path to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading from: {url}")
        logger.info(f"Saving to: {destination}")

        # Make request
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get total size
        total_size = int(response.headers.get('content-length', 0))
        logger.info(f"File size: {total_size / (1024*1024):.1f} MB")

        # Download with progress bar
        with open(destination, 'wb') as f:
            with tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=MODEL_FILENAME
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        logger.info("✓ Download complete")
        return True

    except Exception as e:
        logger.error(f"✗ Error downloading file: {e}")
        return False


def download_clap_model():
    """Download the CLAP model to local directory."""
    logger.info("=" * 60)
    logger.info("CLAP Model Download")
    logger.info("=" * 60)

    # Define paths
    backend_dir = Path(__file__).parent.parent
    models_dir = backend_dir / "models" / "clap"
    model_path = models_dir / MODEL_FILENAME

    # Check if already exists
    if model_path.exists():
        logger.info(f"\n✓ Model already exists at: {model_path}")
        logger.info(f"  File size: {model_path.stat().st_size / (1024*1024):.1f} MB")

        response = input("\nDo you want to re-download? (y/n): ")
        if response.lower() != 'y':
            logger.info("Keeping existing model.")
            return True

    # Create directory
    models_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"\nCreated directory: {models_dir}")

    # Download the model
    logger.info("\nDownloading CLAP model...")
    logger.info("This will download ~600 MB and may take 2-5 minutes\n")

    success = download_file(MODEL_URL, model_path)

    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✓ CLAP model downloaded successfully!")
        logger.info("=" * 60)
        logger.info(f"\nModel location: {model_path}")
        logger.info(f"File size: {model_path.stat().st_size / (1024*1024):.1f} MB")
        logger.info("\nYou can now run: python scripts/init_vector_db.py")
        return True
    else:
        logger.error("\n" + "=" * 60)
        logger.error("✗ Failed to download model")
        logger.error("=" * 60)
        logger.error("\nPossible solutions:")
        logger.error("1. Check your internet connection")
        logger.error("2. Check firewall/proxy settings")
        logger.error("3. Try manual download:")
        logger.error(f"   wget {MODEL_URL}")
        logger.error(f"   mv {MODEL_FILENAME} {model_path}")
        return False


def main():
    """Main entry point."""
    try:
        success = download_clap_model()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("\n\nDownload interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
