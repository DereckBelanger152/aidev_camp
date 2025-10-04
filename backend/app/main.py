from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import search, recommendations
from app.services.embedding_service import get_embedding_service
from app.services.vector_db_service import get_vector_db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize services
    logger.info("Starting up application...")

    try:
        # Initialize embedding service (loads CLAP model)
        logger.info("Loading embedding service...")
        embedding_service = get_embedding_service()
        logger.info(f"Embedding service ready on device: {embedding_service.device}")

        # Initialize vector database
        logger.info("Connecting to vector database...")
        vector_db = get_vector_db_service()
        track_count = vector_db.count_tracks()
        logger.info(f"Vector database ready with {track_count} tracks")

        if track_count == 0:
            logger.warning(
                "⚠️  Vector database is empty! "
                "Run 'python scripts/init_vector_db.py' to initialize."
            )

        logger.info("✓ Application startup complete")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Music Recommendation API",
    description="API for finding similar songs based on audio embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Music Recommendation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        vector_db = get_vector_db_service()
        track_count = vector_db.count_tracks()

        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "track_count": track_count
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
