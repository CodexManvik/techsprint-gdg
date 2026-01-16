import { Mic, Cloud } from 'lucide-react';
import { motion } from 'framer-motion';
import { useEffect } from 'react';
import { useSessionStore, type AudioMode } from '../../stores/sessionStore';

export const AudioModeSelector = () => {
  const { audioMode, setAudioMode } = useSessionStore();

  // Check if browser supports speech recognition
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const isBrowserSpeechSupported = !!SpeechRecognition;

  // Auto-switch to backend if browser speech not supported
  useEffect(() => {
    if (!isBrowserSpeechSupported && audioMode === 'browser') {
      setAudioMode('backend');
    }
  }, [isBrowserSpeechSupported, audioMode, setAudioMode]);

  const modes: { value: AudioMode; label: string; icon: any; description: string; disabled?: boolean }[] = [
    {
      value: 'browser',
      label: 'Browser Speech',
      icon: Mic,
      description: isBrowserSpeechSupported 
        ? 'Fast, free, works offline (Chrome/Edge/Safari only)' 
        : 'Not supported in your browser (Firefox)',
      disabled: !isBrowserSpeechSupported,
    },
    {
      value: 'backend',
      label: 'Server Processing',
      icon: Cloud,
      description: 'Works on all browsers, requires Google Cloud',
    },
  ];

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-slate-dark">Audio Processing Mode</label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {modes.map((mode) => {
          const isSelected = audioMode === mode.value;
          const Icon = mode.icon;
          const isDisabled = mode.disabled;

          return (
            <motion.button
              key={mode.value}
              onClick={() => !isDisabled && setAudioMode(mode.value)}
              whileHover={!isDisabled ? { scale: 1.02 } : {}}
              whileTap={!isDisabled ? { scale: 0.98 } : {}}
              disabled={isDisabled}
              className={`relative px-4 py-4 rounded-lg border-2 transition-all text-left ${
                isDisabled
                  ? 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed'
                  : isSelected
                  ? 'border-primary-blue bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    isDisabled
                      ? 'bg-gray-200 text-gray-400'
                      : isSelected 
                      ? 'bg-primary-blue text-white' 
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  <Icon size={20} />
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-slate-dark mb-1">{mode.label}</div>
                  <div className="text-xs text-gray-600">{mode.description}</div>
                </div>
              </div>
              {isSelected && !isDisabled && (
                <div className="absolute top-2 right-2 w-3 h-3 bg-primary-blue rounded-full" />
              )}
            </motion.button>
          );
        })}
      </div>
      
      {audioMode === 'backend' && (
        <div className="mt-3 p-3 bg-amber-50 border border-accent-amber rounded-lg text-sm text-gray-700">
          ⚠️ Backend mode requires Google Cloud credentials. Make sure your backend is configured with Speech-to-Text API.
        </div>
      )}
      
      {!isBrowserSpeechSupported && (
        <div className="mt-3 p-3 bg-blue-50 border border-primary-blue rounded-lg text-sm text-gray-700">
          ℹ️ Your browser doesn't support Web Speech API. Using server processing mode. For browser speech, use Chrome, Edge, or Safari.
        </div>
      )}
    </div>
  );
};
