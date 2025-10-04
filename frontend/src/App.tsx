import { useState } from 'react';
import { SearchBar } from './components/SearchBar';
import { ConfirmationCard } from './components/ConfirmationCard';
import { ResultsGrid } from './components/ResultsGrid';
import type { Track, AppState } from './types/index';
import { searchTrack, getRecommendations } from './services/api';
import { Music2, Loader2 } from 'lucide-react';

function App() {
  const [appState, setAppState] = useState<AppState>('search');
  const [confirmedTrack, setConfirmedTrack] = useState<Track | null>(null);
  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await searchTrack(query);
      setConfirmedTrack({
        id: result.id,
        title: result.title,
        artist: result.artist,
        preview_url: result.preview_url,
        cover: result.cover,
      });
      setAppState('confirmation');
    } catch (err) {
      setError('Impossible de trouver ce morceau. Vérifiez l\'orthographe.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!confirmedTrack) return;

    setIsLoading(true);
    setAppState('analyzing');
    setError(null);

    try {
      const results = await getRecommendations(confirmedTrack.id);
      setRecommendations(results);
      setAppState('results');
    } catch (err) {
      setError('Erreur lors de l\'analyse. Veuillez réessayer.');
      setAppState('confirmation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setConfirmedTrack(null);
    setAppState('search');
    setError(null);
  };

  const handleNewSearch = () => {
    setConfirmedTrack(null);
    setRecommendations([]);
    setAppState('search');
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      {/* Header */}
      <div className="mb-12 text-center animate-float">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Music2 className="text-neon-cyan" size={48} />
          <h1 className="text-5xl font-bold bg-gradient-to-r from-neon-cyan via-neon-purple to-neon-pink bg-clip-text text-transparent">
            SoundMatch
          </h1>
        </div>
        <p className="text-gray-400 text-lg">
          Découvrez des sons mélodiquement similaires
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 px-6 py-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 max-w-2xl">
          {error}
        </div>
      )}

      {/* Main Content */}
      <div className="w-full max-w-7xl">
        {appState === 'search' && (
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        )}

        {appState === 'confirmation' && confirmedTrack && (
          <ConfirmationCard
            track={confirmedTrack}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
            isLoading={isLoading}
          />
        )}

        {appState === 'analyzing' && (
          <div className="flex flex-col items-center justify-center gap-6 py-20">
            <Loader2 className="text-neon-cyan animate-spin" size={64} />
            <p className="text-2xl text-gray-300">Analyse en cours...</p>
            <p className="text-gray-500">
              Nous recherchons des morceaux similaires mélodiquement
            </p>
          </div>
        )}

        {appState === 'results' && (
          <>
            <ResultsGrid tracks={recommendations} />
            <div className="text-center mt-8">
              <button
                onClick={handleNewSearch}
                className="px-8 py-3 bg-gradient-to-r from-neon-purple to-neon-cyan rounded-xl font-semibold text-white hover:shadow-lg hover:shadow-neon-cyan/50 transition-all duration-300"
              >
                Nouvelle recherche
              </button>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="mt-auto pt-12 text-center text-gray-600 text-sm">
        <p>AI Dev Camp Mirego × Powered by Deezer API & HuggingFace</p>
      </div>
    </div>
  );
}

export default App;
