import { Check, X } from 'lucide-react';
import type { Track } from '../types/index';
import { AudioPlayer } from './AudioPlayer';

interface ConfirmationCardProps {
  track: Track;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ConfirmationCard = ({
  track,
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmationCardProps) => {
  return (
    <div className="w-full max-w-2xl mx-auto animate-[fadeIn_0.5s_ease-in-out]">
      <div className="glass rounded-3xl p-8 neon-glow">
        <h2 className="text-2xl font-bold text-center mb-6 bg-gradient-to-r from-neon-cyan to-neon-purple bg-clip-text text-transparent">
          C'est bien ce morceau que vous voulez rechercher?
        </h2>

        <div className="flex flex-col items-center gap-6">
          {/* Album Cover */}
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-neon-purple to-neon-cyan rounded-2xl blur-xl opacity-60 group-hover:opacity-80 transition-opacity" />
            <img
              src={track.cover}
              alt={track.title}
              className="relative w-64 h-64 object-cover rounded-2xl shadow-2xl"
            />
          </div>

          {/* Track Info */}
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-2">{track.title}</h3>
            <p className="text-xl text-gray-400">{track.artist}</p>
          </div>

          {/* Audio Player */}
          <div className="w-full">
            <AudioPlayer url={track.preview_url} />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 w-full mt-4">
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-xl font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed border border-red-500/30"
            >
              <X size={20} />
              Non, annuler
            </button>

            <button
              onClick={onConfirm}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-neon-green to-neon-cyan rounded-xl font-semibold text-black hover:shadow-lg hover:shadow-neon-green/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check size={20} />
              {isLoading ? 'Analyse en cours...' : 'Oui, continuer'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
