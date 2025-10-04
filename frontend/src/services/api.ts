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

export const getRecommendations = async (trackId: string): Promise<Track[]> => {
  const response = await api.post<Track[]>(`/api/recommendations/${trackId}`);
  return response.data.tracks;
};

export const getTrendingTracks = async (limit: number = 8): Promise<Track[]> => {
  const response = await api.get<Track[]>(`/api/trending?limit=${limit}`);
  return response.data;
};

export default api;
