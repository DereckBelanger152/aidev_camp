import { Check, X, Music2 } from 'lucide-react';
import type { Track } from '../types/index';
import { AudioPlayer } from './AudioPlayer';

interface ConfirmationCardProps {
  track: Track;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const FALLBACK_COVER = 'https://via.placeholder.com/300x300.png?text=No+Cover';

export const ConfirmationCard = ({
  track,
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmationCardProps) => {
  const coverSrc = track.cover ?? FALLBACK_COVER;
  const previewUrl = track.preview_url ?? '';
  const hasPreview = Boolean(track.preview_url);

  return (
    <div className="w-full max-w-3xl mx-auto animate-[fadeIn_0.5s_ease-in-out]">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-pink-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Vous parlez bien de ce chef-d'œuvre ?
        </h2>
        <p className="text-gray-400 text-lg">
          Écoutez l'extrait et confirmez que c'est bien la chanson que vous recherchez
        </p>
      </div>

      <div className="glass rounded-3xl p-6 neon-glow">
        <div className="flex flex-col items-center gap-6">
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-neon-purple to-neon-cyan rounded-2xl blur-xl opacity-60 group-hover:opacity-80 transition-opacity" />
            {track.cover ? (
              <img
                src={coverSrc}
                alt={track.title}
                className="relative w-48 h-48 object-cover rounded-2xl shadow-2xl"
              />
            ) : (
              <div className="relative w-48 h-48 flex items-center justify-center rounded-2xl shadow-2xl bg-gradient-to-br from-slate-800 to-slate-900 text-slate-400">
                <Music2 size={48} />
              </div>
            )}
          </div>

          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-2">{track.title}</h3>
            <p className="text-xl text-gray-400">{track.artist}</p>
          </div>

          <div className="w-full">
            {hasPreview ? (
              <AudioPlayer url={previewUrl} />
            ) : (
              <p className="text-center text-sm text-gray-400">
                Aucun extrait audio disponible pour ce morceau.
              </p>
            )}
          </div>

          <div className="flex gap-4 w-full mt-4">
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-xl font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed border border-purple-500/30"
            >
              <X size={20} />
              Non, annuler
            </button>

            <button
              onClick={onConfirm}
              disabled={isLoading || !hasPreview}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-pink-500 to-purple-500 rounded-xl font-semibold text-white hover:from-pink-400 hover:to-purple-400 hover:shadow-lg hover:shadow-pink-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check size={20} />
              {isLoading ? 'Analyse en cours...' : hasPreview ? 'Oui, continuer' : 'Aucun extrait'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
