import { useState } from 'react';

export const AudioWaves = () => {
  const [bars] = useState(() =>
    Array.from({ length: 40 }, (_, i) => ({
      id: i,
      delay: Math.random() * 2,
      duration: 1 + Math.random() * 1.5,
      baseHeight: 15 + Math.random() * 85,
    }))
  );

  return (
    <div className="absolute top-96 left-0 right-0 h-48 w-full pointer-events-none flex items-end justify-center opacity-20 z-0">
      <div className="flex items-end gap-1 sm:gap-2 md:gap-3 w-full px-4 h-full">
        {bars.map((bar) => (
          <div
            key={bar.id}
            className="flex-1 bg-gradient-to-t from-pink-500 via-purple-500 to-pink-400 rounded-full"
            style={{
              height: `${bar.baseHeight}%`,
              animation: `wave ${bar.duration}s ease-in-out infinite`,
              animationDelay: `${bar.delay}s`,
            }}
          />
        ))}
      </div>

      <style>{`
        @keyframes wave {
          0%, 100% {
            transform: scaleY(0.3);
            opacity: 0.4;
          }
          50% {
            transform: scaleY(1.5);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};
