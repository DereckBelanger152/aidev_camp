import { useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { ConfirmationCard } from "./components/ConfirmationCard";
import { ResultsGrid } from "./components/ResultsGrid";
import type { Track, AppState } from "./types/index";
import { searchTrack, analyzeTrack, getRecommendations } from "./services/api";
import { Music2, Loader2 } from "lucide-react";

// Données placeholder pour visualiser l'interface
const PLACEHOLDER_TRACK: Track = {
  id: "1",
  title: "Bohemian Rhapsody",
  artist: "Queen",
  preview_url:
    "https://cdns-preview-e.dzcdn.net/stream/c-e77d23e0c8ed7567a507a6d1b6a9ca1b-2.mp3",
  cover:
    "https://e-cdns-images.dzcdn.net/images/cover/b84fb43f2f7cec18245b23b96e5c46f4/500x500-000000-80-0-0.jpg",
};

const PLACEHOLDER_RECOMMENDATIONS: Track[] = [
  {
    id: "2",
    title: "Stairway to Heaven",
    artist: "Led Zeppelin",
    preview_url:
      "https://cdns-preview-d.dzcdn.net/stream/c-d0b5abac9e581fc1f1a12f5ea7b21e2e-2.mp3",
    cover:
      "https://e-cdns-images.dzcdn.net/images/cover/53addd47f8e8bcf8b77e1c795c93c3a3/500x500-000000-80-0-0.jpg",
    similarity_score: 0.92,
  },
  {
    id: "3",
    title: "Hotel California",
    artist: "Eagles",
    preview_url:
      "https://cdns-preview-b.dzcdn.net/stream/c-b3e5cb26d7a5aaee5e94c58e55a1fbfc-2.mp3",
    cover:
      "https://e-cdns-images.dzcdn.net/images/cover/2fb3e4cc3a0a629e0e6bd16ea7f64c5a/500x500-000000-80-0-0.jpg",
    similarity_score: 0.89,
  },
  {
    id: "4",
    title: "Comfortably Numb",
    artist: "Pink Floyd",
    preview_url:
      "https://cdns-preview-f.dzcdn.net/stream/c-f8f86ee0b5c3c0fa4b43b9b8e8c5e5f8-2.mp3",
    cover:
      "https://e-cdns-images.dzcdn.net/images/cover/991e0dbc62b1a04b62f3a5c2c1e1bff1/500x500-000000-80-0-0.jpg",
    similarity_score: 0.85,
  },
];

function App() {
  // PLACEHOLDER MODE: Décommentez pour voir toute l'interface
  const [appState, setAppState] = useState<AppState>("search"); // Change de 'search' à 'results' à 'confirmation' à 'analyzing'
  const [confirmedTrack, setConfirmedTrack] = useState<Track | null>(
    PLACEHOLDER_TRACK
  );
  const [recommendations, setRecommendations] = useState<Track[]>(
    PLACEHOLDER_RECOMMENDATIONS
  );
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
      setAppState("confirmation");
    } catch (err) {
      setError("Impossible de trouver ce morceau. Vérifiez l'orthographe.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!confirmedTrack) return;

    setIsLoading(true);
    setAppState("analyzing");
    setError(null);

    try {
      await analyzeTrack(confirmedTrack.id);
      const results = await getRecommendations(confirmedTrack.id);
      setRecommendations(results);
      setAppState("results");
    } catch (err) {
      setError("Erreur lors de l'analyse. Veuillez réessayer.");
      setAppState("confirmation");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setConfirmedTrack(null);
    setAppState("search");
    setError(null);
  };

  const handleNewSearch = () => {
    setConfirmedTrack(null);
    setRecommendations([]);
    setAppState("search");
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
        {appState === "search" && (
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        )}

        {appState === "confirmation" && confirmedTrack && (
          <ConfirmationCard
            track={confirmedTrack}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
            isLoading={isLoading}
          />
        )}

        {appState === "analyzing" && (
          <div className="flex flex-col items-center justify-center gap-6 py-20">
            <Loader2 className="text-neon-cyan animate-spin" size={64} />
            <p className="text-2xl text-gray-300">Analyse en cours...</p>
            <p className="text-gray-500">
              Nous recherchons des morceaux similaires mélodiquement
            </p>
          </div>
        )}

        {appState === "results" && (
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
