from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class SearchRequest(BaseModel):
    """Request payload for textual track search."""

    query: str = Field(..., min_length=1, max_length=200)


class TrackInfo(BaseModel):
    """Minimal Deezer track representation for client-facing responses."""

    id: str
    title: str
    artist: str
    preview_url: Optional[HttpUrl] = None
    cover: Optional[HttpUrl] = None
    rank: Optional[int] = None
    message: Optional[str] = None
    duration: Optional[int] = None
    genre_id: Optional[int] = None
    genre: Optional[str] = None

    model_config = {"extra": "ignore"}


class RecommendationTrack(BaseModel):
    id: str
    title: str
    artist: str
    similarity_score: float
    popularity: Optional[int] = None
    preview_url: Optional[HttpUrl] = None
    cover: Optional[HttpUrl] = None


class RecommendationResponse(BaseModel):
    source_track_id: str
    tracks: List[RecommendationTrack]


class AddTracksRequest(BaseModel):
    track_ids: List[str] = Field(..., min_length=1, description="List of Deezer track IDs to index")


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
