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


# Admin endpoint schemas
class AddTracksRequest(BaseModel):
    """Request model for adding tracks to database."""
    track_ids: List[str] = Field(..., description="List of Deezer track IDs to add")


class AddTracksResponse(BaseModel):
    status: str
    added_count: int
    message: str


class SongIdentificationRequest(BaseModel):
    """Payload for LLM-assisted song identification and recommendation."""

    track_id: Optional[str] = Field(default=None, description="Known Deezer track ID to analyse")
    song_name: Optional[str] = Field(default=None, description="Song title hint for identification")
    artist: Optional[str] = Field(default=None, description="Artist hint for identification")
    preview_url: Optional[HttpUrl] = Field(
        default=None,
        description="Audio sample URL used when track is unknown (30s preview recommended)",
    )
    similar_count: int = Field(default=2, ge=1, le=5, description="Number of similar tracks to return")
    candidate_limit: int = Field(
        default=25,
        ge=5,
        le=100,
        description="Maximum number of candidate tracks considered during identification",
    )

    @model_validator(mode="after")
    def validate_sources(cls, values: "SongIdentificationRequest") -> "SongIdentificationRequest":  # type: ignore[override]
        if not any([values.track_id, values.song_name, values.preview_url]):
            raise ValueError("Provide at least one of track_id, song_name, or preview_url")
        return values

    @field_validator("song_name", "artist")
    @classmethod
    def strip_optional(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value


class IdentifiedTrack(TrackInfo):
    confidence: Optional[float] = Field(
        default=None,
        description="Similarity score used when identification relied on audio only",
    )


class LLMSummary(BaseModel):
    prompt: str
    response: str


class SongIdentificationResponse(BaseModel):
    identified_track: IdentifiedTrack
    similar_tracks: List[RecommendationTrack]
    llm_summary: LLMSummary


class VoiceIdentificationRequest(BaseModel):
    """Voice recording payload encoded as base64."""

    audio_base64: str = Field(..., description="Base64-encoded MP3/OGG/WEBM content")
    filename: Optional[str] = Field(
        default=None,
        description="Original filename (used to guess extension)",
    )
    similar_count: int = Field(default=2, ge=1, le=5)
    candidate_limit: int = Field(default=25, ge=5, le=100)
    hints: Optional[str] = Field(
        default=None,
        description="Optional context about the recording (language, gender, etc.)",
    )

    @field_validator("audio_base64")
    @classmethod
    def validate_base64(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("audio_base64 must be a non-empty string")
        return value.strip()


class VoiceIdentificationResponse(SongIdentificationResponse):
    transcription: Optional[str] = None
    voice_confidence: Optional[float] = Field(
        default=None,
        description="Confidence returned by the voice identification service",
    )


__all__ = [
    "SearchRequest",
    "TrackInfo",
    "RecommendationTrack",
    "RecommendationResponse",
    "AddTracksRequest",
    "AddTracksResponse",
    "SongIdentificationRequest",
    "SongIdentificationResponse",
    "IdentifiedTrack",
    "LLMSummary",
    "VoiceIdentificationRequest",
    "VoiceIdentificationResponse",
]
