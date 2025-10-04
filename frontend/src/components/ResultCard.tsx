import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Music2 } from 'lucide-react';
import type { Track } from '../types/index';

interface ResultCardProps {
  track: Track;
}

export const ResultCard = ({ track }: ResultCardProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Create audio element
    const audio = new Audio(track.preview_url);
    audioRef.current = audio;

    // Handle audio end
    const handleEnded = () => setIsPlaying(false);
    audio.addEventListener('ended', handleEnded);

    // Cleanup
    return () => {
      audio.pause();
      audio.removeEventListener('ended', handleEnded);
      audioRef.current = null;
    };
  }, [track.preview_url]);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const similarityPercentage = track.similarity_score
    ? Math.round(track.similarity_score * 100)
    : 0;

  return (
    <div className="glass rounded-2xl overflow-hidden group hover:scale-105 transition-all duration-300 neon-glow">
      {/* Cover Image */}
      <div className="relative aspect-square overflow-hidden">
        <img
          src={track.cover}
          alt={track.title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />

        {/* Similarity Badge */}
        {track.similarity_score && (
          <div className="absolute top-3 right-3 bg-black/80 backdrop-blur-sm px-3 py-1 rounded-full border border-neon-cyan">
            <span className="text-neon-cyan font-bold text-sm">
              {similarityPercentage}% similaire
            </span>
          </div>
        )}

        {/* Play Button Overlay */}
        <button
          onClick={togglePlay}
          className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        >
          <div className="w-16 h-16 flex items-center justify-center rounded-full bg-neon-cyan text-black hover:bg-neon-green transition-all duration-300 hover:scale-110">
            {isPlaying ? <Pause size={28} /> : <Play size={28} className="ml-1" />}
          </div>
        </button>
      </div>

      {/* Track Info */}
      <div className="p-5">
        <h3 className="text-xl font-bold text-white mb-1 truncate">{track.title}</h3>
        <p className="text-gray-400 mb-4 truncate">{track.artist}</p>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={togglePlay}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-neon-purple to-neon-cyan rounded-lg font-semibold text-white hover:shadow-lg hover:shadow-neon-cyan/50 transition-all duration-300"
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            {isPlaying ? 'Pause' : 'Écouter'}
          </button>

          <button
            className="px-4 py-2 glass rounded-lg hover:bg-white/10 transition-all duration-300 border border-neon-green/30 text-neon-green font-semibold flex items-center gap-2"
            title="Sauvegarder sur Spotify (bientôt disponible)"
          >
            <Music2 size={16} />
            Spotify
          </button>
        </div>
      </div>
    </div>
  );
};
