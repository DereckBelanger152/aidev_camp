"""
Pydantic schemas for API request/response models.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# Search endpoint schemas
class SearchRequest(BaseModel):
    """Request model for track search."""
    query: str = Field(..., min_length=1, description="Search query for track name")


class TrackInfo(BaseModel):
    """Response model for track information."""
    id: str = Field(..., description="Deezer track ID")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    preview_url: Optional[str] = Field(None, description="URL to 30s preview audio")
    cover: Optional[str] = Field(None, description="URL to album cover image")
    rank: Optional[int] = Field(None, description="Deezer popularity rank")
    duration: Optional[int] = Field(None, description="Track duration in seconds")
    message: Optional[str] = Field(None, description="Confirmation message")


# Recommendation endpoint schemas
class RecommendationTrack(BaseModel):
    """Model for a recommended track."""
    id: str = Field(..., description="Deezer track ID")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    similarity_score: float = Field(..., ge=0, le=1, description="Audio similarity score (0-1)")
    popularity: int = Field(..., description="Deezer popularity rank")
    preview_url: Optional[str] = Field(None, description="URL to 30s preview audio")
    cover: Optional[str] = Field(None, description="URL to album cover image")


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""
    tracks: List[RecommendationTrack] = Field(..., description="List of recommended tracks")
    source_track_id: str = Field(..., description="ID of the source track used for recommendations")


# Admin endpoint schemas
class AddTracksRequest(BaseModel):
    """Request model for adding tracks to database."""
    track_ids: List[str] = Field(..., min_length=1, description="List of Deezer track IDs to add")


class AddTracksResponse(BaseModel):
    """Response model for add tracks operation."""
    status: str = Field(..., description="Operation status")
    added_count: int = Field(..., description="Number of tracks successfully added")
    message: str = Field(..., description="Status message")
