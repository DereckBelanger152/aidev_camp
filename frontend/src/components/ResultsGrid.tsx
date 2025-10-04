import type { Track } from '../types/index';
import { ResultCard } from './ResultCard';

interface ResultsGridProps {
  tracks: Track[];
}

export const ResultsGrid = ({ tracks }: ResultsGridProps) => {
  if (tracks.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400 text-lg">Aucun résultat trouvé</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto animate-[fadeIn_0.5s_ease-in-out]">
      <h2 className="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-neon-cyan via-neon-purple to-neon-pink bg-clip-text text-transparent">
        Morceaux similaires découverts
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tracks.map((track, index) => (
          <div
            key={track.id}
            className="animate-[fadeIn_0.5s_ease-in-out]"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <ResultCard track={track} />
          </div>
        ))}
      </div>

      <div className="text-center mt-8">
        <p className="text-gray-500 text-sm">
          Ces morceaux ont été sélectionnés en fonction de leur similarité mélodique
        </p>
      </div>
    </div>
  );
};
