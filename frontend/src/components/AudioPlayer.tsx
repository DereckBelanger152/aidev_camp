import { useState, useRef, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

interface AudioPlayerProps {
  url: string;
  className?: string;
}

export const AudioPlayer = ({ url, className = '' }: AudioPlayerProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;

    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <audio ref={audioRef} src={url} preload="metadata" />

      <button
        onClick={togglePlay}
        className="w-10 h-10 flex items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-400 hover:to-pink-400 transition-all duration-300 shadow-lg shadow-purple-500/50"
      >
        {isPlaying ? <Pause size={20} /> : <Play size={20} className="ml-0.5" />}
      </button>

      <div className="flex-1 flex items-center gap-2">
        <span className="text-xs text-white font-medium w-10">{formatTime(currentTime)}</span>

        <div
          onClick={handleProgressClick}
          className="flex-1 h-2 bg-white/20 rounded-full cursor-pointer overflow-hidden group hover:bg-white/30 transition-colors"
        >
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>

        <span className="text-xs text-white font-medium w-10">{formatTime(duration)}</span>
      </div>
    </div>
  );
};
