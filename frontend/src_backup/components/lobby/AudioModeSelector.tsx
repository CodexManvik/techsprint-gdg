import { Mic, Cloud, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { useEffect } from 'react';
import { useSessionStore, type AudioMode } from '../../stores/sessionStore';
import { cn } from '../../lib/utils';

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
        ? 'Fast, free, works offline'
        : 'Not supported in this browser',
      disabled: !isBrowserSpeechSupported,
    },
    {
      value: 'backend',
      label: 'Server Processing',
      icon: Cloud,
      description: 'Higher accuracy, all browsers',
    },
  ];

  return (
    <div className="space-y-4">
      <label className="text-sm font-medium text-foreground">Audio Processing Mode</label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {modes.map((mode, index) => {
          const isSelected = audioMode === mode.value;
          const Icon = mode.icon;
          const isDisabled = mode.disabled;

          return (
            <motion.button
              key={mode.value}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => setAudioMode(mode.value)}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                'relative px-5 py-5 rounded-xl transition-all duration-300 text-left',
                'border overflow-hidden',
                isSelected
                  ? 'border-primary bg-primary/10 glow'
                  : 'border-border glass hover:border-primary/50',
                isDisabled && 'opacity-60 grayscale'
              )}
            >
              {/* Selection indicator */}
              {isSelected && !isDisabled && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-3 right-3 w-5 h-5 rounded-full bg-primary flex items-center justify-center"
                >
                  <Check className="w-3 h-3 text-white" />
                </motion.div>
              )}

              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
                    isDisabled
                      ? 'bg-surface-elevated text-foreground-muted'
                      : isSelected
                        ? 'bg-primary/20 text-primary'
                        : 'bg-surface-elevated text-foreground-muted'
                  )}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className={cn(
                    'font-semibold mb-1 transition-colors',
                    isSelected && !isDisabled ? 'text-primary' : 'text-foreground'
                  )}>
                    {mode.label}
                  </div>
                  <div className="text-sm text-foreground-muted">{mode.description}</div>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Info messages */}
      {audioMode === 'backend' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-warning/10 border border-warning/30 text-sm"
        >
          <span className="text-warning font-medium">⚠️ Note:</span>
          <span className="text-foreground-muted ml-1">
            Backend mode requires Google Cloud credentials configured on the server.
          </span>
        </motion.div>
      )}

      {!isBrowserSpeechSupported && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-info/10 border border-info/30 text-sm"
        >
          <span className="text-info font-medium">ℹ️ Info:</span>
          <span className="text-foreground-muted ml-1">
            Your browser doesn't support Web Speech API. Use Chrome, Edge, or Safari for browser speech.
          </span>
        </motion.div>
      )}
    </div>
  );
};
