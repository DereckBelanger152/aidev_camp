from pydantic import BaseModel, Field
from typing import Optional, List


class SearchRequest(BaseModel):
    """Request model for track search."""
    query: str = Field(..., description="Track name to search for", min_length=1)


class TrackInfo(BaseModel):
    """Track information returned from search."""
    id: str = Field(..., description="Deezer track ID")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    preview_url: str = Field(..., description="URL to 30s preview MP3")
    cover: str = Field(..., description="URL to album cover image")
    message: Optional[str] = Field(None, description="Confirmation message for user")


class RecommendationTrack(BaseModel):
    """Recommended track with similarity score."""
    id: str = Field(..., description="Deezer track ID")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)", ge=0, le=1)
    popularity: int = Field(..., description="Deezer rank/popularity score")
    preview_url: str = Field(..., description="URL to 30s preview MP3")
    cover: str = Field(..., description="URL to album cover image")


class RecommendationResponse(BaseModel):
    """Response model for track recommendations."""
    tracks: List[RecommendationTrack] = Field(..., description="List of recommended tracks")
    source_track_id: str = Field(..., description="ID of the source track")


class AddTracksRequest(BaseModel):
    """Request model for adding tracks to database."""
    track_ids: List[str] = Field(..., description="List of Deezer track IDs to add")


class AddTracksResponse(BaseModel):
    """Response model for add tracks operation."""
    status: str = Field(..., description="Operation status")
    added_count: int = Field(..., description="Number of tracks successfully added")
    message: str = Field(..., description="Status message")
