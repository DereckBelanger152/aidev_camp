import { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { ConfirmationCard } from './components/ConfirmationCard';
import { ResultsGrid } from './components/ResultsGrid';
import { TrendingGrid } from './components/TrendingGrid';
import { AudioWaves } from './components/AudioWaves';
import { About } from './components/About';
import type { Track, AppState } from './types/index';
import {
  searchTrack,
  getRecommendations,
  getTrendingTracks,
  identifySongFromVoice,
} from './services/api';
import { Music2, Loader2 } from 'lucide-react';

function App() {
  const [appState, setAppState] = useState<AppState>('search');
  const [confirmedTrack, setConfirmedTrack] = useState<Track | null>(null);
  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [trendingTracks, setTrendingTracks] = useState<Track[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const [isTrendingLoading, setIsTrendingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [llmSummary, setLlmSummary] = useState<string | null>(null);
  const [voiceTranscription, setVoiceTranscription] = useState<string | null>(null);
  const [voiceConfidence, setVoiceConfidence] = useState<number | null>(null);

  const resetInsights = () => {
    setLlmSummary(null);
    setVoiceTranscription(null);
    setVoiceConfidence(null);
  };

  useEffect(() => {
    const fetchTrending = async () => {
      setIsTrendingLoading(true);
      try {
        const tracks = await getTrendingTracks(9);
        setTrendingTracks(tracks);
      } catch (err) {
        console.error('Failed to fetch trending tracks:', err);
      } finally {
        setIsTrendingLoading(false);
      }
    };

    fetchTrending();
  }, []);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    resetInsights();

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
      setError("Impossible de trouver ce morceau. Vérifiez l'orthographe.");
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
    resetInsights();

    try {
      const results = await getRecommendations(confirmedTrack.id);
      setRecommendations(results);
      setAppState('results');
    } catch (err) {
      setError("Erreur lors de l'analyse. Veuillez réessayer.");
      setAppState('confirmation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setConfirmedTrack(null);
    setRecommendations([]);
    setAppState('search');
    setError(null);
    resetInsights();
  };

  const handleNewSearch = () => {
    setConfirmedTrack(null);
    setRecommendations([]);
    setAppState('search');
    setError(null);
    resetInsights();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTrendingTrackClick = async (_trackId: string, title: string) => {
    await handleSearch(title);
  };

  const blobToBase64 = (blob: Blob) =>
    new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          const base64 = reader.result.split(',')[1] ?? reader.result;
          resolve(base64);
        } else {
          reject(new Error('Impossible de lire le fichier audio.'));
        }
      };
      reader.onerror = () => reject(reader.error ?? new Error('Erreur de lecture audio'));
      reader.readAsDataURL(blob);
    });

  const handleVoiceIdentify = async (audio: Blob, filename: string) => {
    setIsVoiceProcessing(true);
    setError(null);

    try {
      const audioBase64 = await blobToBase64(audio);
      const response = await identifySongFromVoice({
        audioBase64,
        filename,
        similarCount: 3,
        candidateLimit: 30,
      });

      const identified = response.identified_track;
      setConfirmedTrack({
        id: identified.id,
        title: identified.title,
        artist: identified.artist,
        preview_url: identified.preview_url ?? undefined,
        cover: identified.cover ?? undefined,
        similarity_score: identified.similarity_score,
        confidence: identified.confidence,
      });
      setRecommendations(
        response.similar_tracks.map((track) => ({
          id: track.id,
          title: track.title,
          artist: track.artist,
          preview_url: track.preview_url ?? undefined,
          cover: track.cover ?? undefined,
          similarity_score: track.similarity_score,
        })),
      );
      setLlmSummary(response.llm_summary?.response ?? null);
      setVoiceTranscription(response.transcription ?? null);
      setVoiceConfidence(response.voice_confidence ?? identified.confidence ?? null);
      setAppState('results');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error(err);
      setError("Impossible d'identifier ce morceau. Veuillez réessayer.");
    } finally {
      setIsVoiceProcessing(false);
    }
  };

  const handleNavigation = (page: 'home' | 'about') => {
    if (page === 'home') {
      handleNewSearch();
    } else {
      setAppState('about');
    }
  };

  return (
    <>
      <Navbar onNavigate={handleNavigation} />
      <AudioWaves />

      <div className="min-h-screen flex flex-col items-center justify-center p-6 pt-28">
        {appState === 'search' && (
          <div className="mb-8 text-center animate-float">
            <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-pink-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              SoundTwin
            </h1>
            <p className="text-gray-400 text-lg">
              Trouvez le jumeau sonore de votre chanson préférée 🎵
            </p>
          </div>
        )}

        {error && (
          <div className="mb-6 px-6 py-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 max-w-2xl">
            {error}
          </div>
        )}

        <div className="w-full max-w-7xl">
          {appState === 'search' && (
            <>
              <SearchBar
                onSearch={handleSearch}
                onVoiceIdentify={handleVoiceIdentify}
                isLoading={isLoading}
                isVoiceLoading={isVoiceProcessing}
              />
              <TrendingGrid
                tracks={trendingTracks}
                onTrackClick={handleTrendingTrackClick}
                isLoading={isTrendingLoading}
              />
            </>
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
              {llmSummary && (
                <div className="max-w-4xl mx-auto mb-10 glass rounded-2xl p-6 border border-neon-cyan/40">
                  <h3 className="text-xl font-semibold text-white mb-3 flex items-center gap-2">
                    <Music2 size={18} className="text-neon-cyan" />
                    Analyse IA
                  </h3>
                  <p className="text-gray-300 leading-relaxed whitespace-pre-line">{llmSummary}</p>
                  {(voiceTranscription || voiceConfidence !== null) && (
                    <div className="mt-4 text-sm text-gray-400 space-y-2">
                      {voiceTranscription && (
                        <p>
                          <span className="text-gray-500">Transcription :</span>{' '}
                          {voiceTranscription}
                        </p>
                      )}
                      {voiceConfidence !== null && (
                        <p>
                          <span className="text-gray-500">Confiance vocale :</span>{' '}
                          {(voiceConfidence * 100).toFixed(1)}%
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              <ResultsGrid tracks={recommendations} />
              <div className="text-center mt-8">
                <button
                  onClick={handleNewSearch}
                  className="px-10 py-3 bg-gradient-to-r from-pink-500 to-purple-500 rounded-xl font-semibold text-white hover:shadow-lg hover:shadow-pink-500/50 transition-all duration-300"
                >
                  Nouvelle recherche
                </button>
              </div>
            </>
          )}

          {appState === 'about' && <About />}
        </div>

        <div className="mt-auto pt-12 text-center text-gray-600 text-sm">
          <p>AI Dev Camp Mirego – Powered by Deezer API & HuggingFace</p>
        </div>
      </div>
    </>
  );
}

export default App;
