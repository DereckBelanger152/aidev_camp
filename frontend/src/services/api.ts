import axios from 'axios';
import type { SearchResponse, Track } from '../types/index';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchTrack = async (query: string): Promise<SearchResponse> => {
  const response = await api.post<SearchResponse>('/api/search', { query });
  return response.data;
};

export const analyzeTrack = async (trackId: string): Promise<void> => {
  await api.post('/api/analyze', { track_id: trackId });
};

export const getRecommendations = async (trackId: string): Promise<Track[]> => {
  const response = await api.get<Track[]>(`/api/recommendations/${trackId}`);
  return response.data;
};

export default api;
