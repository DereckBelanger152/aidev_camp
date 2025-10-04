import chromadb
from chromadb.config import Settings
import numpy as np
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "db" / "vector_store"


class VectorDBService:
    """Service for managing the vector database with ChromaDB."""

    def __init__(self, db_path: Optional[Path] = None, collection_name: str = "music_embeddings"):
        """
        Initialize the vector database service.

        Args:
            db_path: Path to store the database
            collection_name: Name of the collection
        """
        self.db_path = db_path or DB_PATH
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        logger.info(f"Initialized VectorDB at {self.db_path}, collection: {collection_name}")

    def add_track(
        self,
        track_id: str,
        embedding: np.ndarray,
        metadata: Dict
    ) -> None:
        """
        Add a single track to the database.

        Args:
            track_id: Unique track identifier
            embedding: Audio embedding vector
            metadata: Track metadata (title, artist, popularity, etc.)
        """
        try:
            # Convert embedding to list
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding

            # Add to collection
            self.collection.add(
                ids=[track_id],
                embeddings=[embedding_list],
                metadatas=[metadata]
            )

            logger.info(f"Added track {track_id} to database")

        except Exception as e:
            logger.error(f"Error adding track {track_id}: {e}")
            raise

    def bulk_add_tracks(
        self,
        track_ids: List[str],
        embeddings: List[np.ndarray],
        metadatas: List[Dict]
    ) -> None:
        """
        Add multiple tracks to the database in batch.

        Args:
            track_ids: List of track identifiers
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
        """
        try:
            # Convert embeddings to lists
            embedding_lists = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb
                for emb in embeddings
            ]

            # Add to collection
            self.collection.add(
                ids=track_ids,
                embeddings=embedding_lists,
                metadatas=metadatas
            )

            logger.info(f"Added {len(track_ids)} tracks to database")

        except Exception as e:
            logger.error(f"Error adding tracks in bulk: {e}")
            raise

    def query_similar(
        self,
        embedding: np.ndarray,
        n_results: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> Dict:
        """
        Query for similar tracks based on embedding.

        Args:
            embedding: Query embedding vector
            n_results: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            Dictionary with ids, distances, and metadatas
        """
        try:
            # Convert embedding to list
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding

            # Query collection
            results = self.collection.query(
                query_embeddings=[embedding_list],
                n_results=n_results,
                where=filter_dict
            )

            return {
                'ids': results['ids'][0] if results['ids'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else []
            }

        except Exception as e:
            logger.error(f"Error querying similar tracks: {e}")
            raise

    def get_track(self, track_id: str) -> Optional[Dict]:
        """
        Get a track by ID.

        Args:
            track_id: Track identifier

        Returns:
            Track data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[track_id],
                include=["embeddings", "metadatas"]
            )

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'embedding': np.array(result['embeddings'][0]),
                    'metadata': result['metadatas'][0]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting track {track_id}: {e}")
            raise

    def track_exists(self, track_id: str) -> bool:
        """
        Check if a track exists in the database.

        Args:
            track_id: Track identifier

        Returns:
            True if track exists, False otherwise
        """
        try:
            result = self.collection.get(ids=[track_id])
            return len(result['ids']) > 0

        except Exception as e:
            logger.error(f"Error checking track existence: {e}")
            return False

    def delete_track(self, track_id: str) -> None:
        """
        Delete a track from the database.

        Args:
            track_id: Track identifier
        """
        try:
            self.collection.delete(ids=[track_id])
            logger.info(f"Deleted track {track_id}")

        except Exception as e:
            logger.error(f"Error deleting track {track_id}: {e}")
            raise

    def count_tracks(self) -> int:
        """
        Get the total number of tracks in the database.

        Returns:
            Number of tracks
        """
        try:
            return self.collection.count()

        except Exception as e:
            logger.error(f"Error counting tracks: {e}")
            return 0

    def reset_database(self) -> None:
        """Reset the entire database (use with caution)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("Database has been reset")

        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise


# Global instance
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db_service() -> VectorDBService:
    """Get or create the global vector database service instance."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service
