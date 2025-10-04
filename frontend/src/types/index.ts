export interface Track {
  id: string;
  title: string;
  artist: string;
  preview_url?: string | null;
  cover?: string | null;
  similarity_score?: number;
  confidence?: number;
}

export interface SearchResponse {
  id: string;
  title: string;
  artist: string;
  preview_url: string;
  cover: string;
  message: string;
}

export interface LLMSummary {
  prompt: string;
  response: string;
}

export interface VoiceIdentificationResponse {
  identified_track: Track;
  similar_tracks: Track[];
  llm_summary: LLMSummary;
  transcription?: string;
  voice_confidence?: number;
}

export type AppState = 'search' | 'confirmation' | 'analyzing' | 'results' | 'about';
