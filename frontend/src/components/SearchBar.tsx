import { useEffect, useMemo, useRef, useState } from 'react';
import { Search, Mic, Square, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onVoiceIdentify?: (audio: Blob, filename: string) => Promise<void> | void;
  isLoading?: boolean;
  isVoiceLoading?: boolean;
}

export const SearchBar = ({
  onSearch,
  onVoiceIdentify,
  isLoading = false,
  isVoiceLoading = false,
}: SearchBarProps) => {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const supportsRecording = useMemo(
    () => typeof window !== 'undefined' && 'mediaDevices' in navigator && typeof MediaRecorder !== 'undefined',
    [],
  );

  useEffect(() => {
    return () => {
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== 'inactive') {
        recorder.stop();
      }
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading && !isVoiceLoading) {
      onSearch(query.trim());
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;
    if (recorder.state !== 'inactive') {
      recorder.stop();
    }
  };

  const startRecording = async () => {
    if (!supportsRecording || !onVoiceIdentify || isLoading || isVoiceLoading) {
      return;
    }

    try {
      setRecordingError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);

        const mimeType = recorder.mimeType || 'audio/webm';
        const extension = mimeType.includes('mpeg')
          ? 'mp3'
          : mimeType.includes('ogg')
          ? 'ogg'
          : mimeType.includes('wav')
          ? 'wav'
          : 'webm';

        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        audioChunksRef.current = [];

        try {
          await onVoiceIdentify?.(blob, `voice-recording.${extension}`);
        } catch (error) {
          console.error('Voice identification failed', error);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Audio recording error', error);
      setRecordingError("Impossible d'accéder au micro. Veuillez vérifier vos permissions.");
      setIsRecording(false);
    }
  };

  const handleRecordToggle = () => {
    if (!supportsRecording || isLoading || isVoiceLoading) {
      return;
    }

    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto mb-16">
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-neon-purple via-neon-cyan to-neon-pink rounded-2xl opacity-75 blur-md group-hover:opacity-100 transition-opacity duration-300" />

        <div className="relative glass rounded-2xl p-1">
          <div className="flex flex-col gap-2 bg-black/50 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <Search className="text-neon-cyan" size={24} />

              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Entrez le titre exact de la chanson..."
                disabled={isLoading || isVoiceLoading}
                className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-lg disabled:opacity-50"
              />

              <div className="flex items-center gap-2">
                {supportsRecording && (
                  <button
                    type="button"
                    onClick={handleRecordToggle}
                    disabled={isLoading || isVoiceLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={isRecording ? "Arrêter l'enregistrement" : "Enregistrer votre voix"}
                  >
                    {isVoiceLoading ? (
                      <Loader2 className="animate-spin" size={18} />
                    ) : isRecording ? (
                      <Square size={18} className="text-red-400" />
                    ) : (
                      <Mic size={18} className="text-neon-green" />
                    )}
                    <span className="hidden sm:inline">
                      {isVoiceLoading ? 'Analyse...' : isRecording ? 'Stop' : 'Voix'}
                    </span>
                  </button>
                )}

                <button
                  type="submit"
                  disabled={!query.trim() || isLoading || isVoiceLoading}
                  className="px-6 py-2 bg-gradient-to-r from-neon-purple to-neon-cyan rounded-lg font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-neon-cyan/50 transition-all duration-300"
                >
                  {isLoading ? 'Recherche...' : 'Rechercher'}
                </button>
              </div>
            </div>

            {recordingError && (
              <p className="text-sm text-red-400">{recordingError}</p>
            )}
          </div>
        </div>
      </div>
    </form>
  );
};
