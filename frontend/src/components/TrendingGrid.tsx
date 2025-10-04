import { useState, useRef, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';
import type { Track } from '../types/index';

interface TrendingGridProps {
  tracks: Track[];
  onTrackClick: (trackId: string, title: string) => void;
  isLoading?: boolean;
}

export const TrendingGrid = ({ tracks, onTrackClick, isLoading = false }: TrendingGridProps) => {
  const [playingTrackId, setPlayingTrackId] = useState<string | null>(null);
  const audioRefs = useRef<{ [key: string]: HTMLAudioElement }>({});

  useEffect(() => {
    // Create Audio objects for all tracks
    tracks.forEach((track) => {
      if (!audioRefs.current[track.id]) {
        const audio = new Audio(track.preview_url);
        audio.addEventListener('ended', () => setPlayingTrackId(null));
        audioRefs.current[track.id] = audio;
      }
    });

    // Cleanup on unmount
    return () => {
      Object.values(audioRefs.current).forEach((audio) => {
        audio.pause();
        audio.src = '';
      });
      audioRefs.current = {};
    };
  }, [tracks]);

  const handlePlayPause = async (e: React.MouseEvent, track: Track) => {
    e.stopPropagation();

    if (playingTrackId === track.id) {
      // Pause current track
      const audio = audioRefs.current[track.id];
      if (audio) {
        audio.pause();
        setPlayingTrackId(null);
      }
    } else {
      // Stop previous track if playing
      if (playingTrackId && audioRefs.current[playingTrackId]) {
        audioRefs.current[playingTrackId].pause();
        audioRefs.current[playingTrackId].currentTime = 0;
      }

      // Play new track
      const audioElement = audioRefs.current[track.id];
      if (audioElement) {
        try {
          await audioElement.play();
          setPlayingTrackId(track.id);
        } catch (error) {
          console.error('Error playing audio:', error);
          console.log('Track:', track.title, 'URL:', track.preview_url);
        }
      } else {
        console.error('Audio element not found for track:', track.id);
      }
    }
  };
  if (isLoading) {
    return (
      <div className="w-full px-4 sm:px-8 md:px-12">
        <h2 className="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-pink-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Essayez avec ces hits populaires
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 max-w-3xl mx-auto">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="aspect-square bg-gray-800 rounded-xl mb-3"></div>
              <div className="h-4 bg-gray-800 rounded mb-2"></div>
              <div className="h-3 bg-gray-800 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (tracks.length === 0) {
    return null;
  }

  return (
    <div className="w-full px-4 sm:px-8 md:px-12">
      <h2 className="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-pink-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
        Essayez avec ces hits populaires
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 max-w-3xl mx-auto">
        {tracks.map((track) => (
          <div
            key={track.id}
            className="group relative cursor-pointer transition-all duration-300 hover:scale-105"
          >
            {/* Album Cover */}
            <div
              className="relative aspect-square rounded-xl overflow-hidden shadow-lg"
              onClick={() => onTrackClick(track.id, track.title)}
            >
              <img
                src={track.cover}
                alt={track.title}
                className="w-full h-full object-cover"
              />

              {/* Overlay on hover */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <button
                  onClick={(e) => handlePlayPause(e, track)}
                  className="w-12 h-12 rounded-full bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center shadow-lg hover:scale-110 transition-transform z-10"
                >
                  {playingTrackId === track.id ? (
                    <Pause className="text-white" size={24} fill="white" />
                  ) : (
                    <Play className="text-white ml-1" size={24} fill="white" />
                  )}
                </button>
              </div>

              {/* Gradient overlay at bottom */}
              <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-black/80 to-transparent"></div>
            </div>

            {/* Track Info */}
            <div className="mt-3 text-left">
              <h3 className="text-sm font-semibold text-white truncate group-hover:text-pink-400 transition-colors">
                {track.title}
              </h3>
              <p className="text-xs text-gray-400 truncate">{track.artist}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
