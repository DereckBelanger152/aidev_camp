export interface Track {
  id: string;
  title: string;
  artist: string;
  preview_url: string;
  cover: string;
  similarity_score?: number;
}

export interface SearchResponse {
  id: string;
  title: string;
  artist: string;
  preview_url: string;
  cover: string;
  message: string;
}

export interface AnalysisResponse {
  status: string;
  message: string;
}

export interface RecommendationsResponse {
  recommendations: Track[];
}

export type AppState = 'search' | 'confirmation' | 'analyzing' | 'results' | 'about';
