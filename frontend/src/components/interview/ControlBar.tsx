import { Mic, MicOff, PhoneOff } from 'lucide-react';
import { motion } from 'framer-motion';

interface ControlBarProps {
  isMuted: boolean;
  onToggleMute: () => void;
  onEndInterview: () => void;
}

export const ControlBar = ({ isMuted, onToggleMute, onEndInterview }: ControlBarProps) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-30 bg-white/95 backdrop-blur-sm border-t border-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="flex items-center justify-center gap-4">
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onToggleMute}
              className={`p-4 rounded-full transition-colors ${
                isMuted ? 'bg-accent-red text-white' : 'bg-primary-blue text-white hover:bg-blue-600'
              }`}
            >
              {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
            </motion.button>
            {!isMuted && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"
              />
            )}
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onEndInterview}
            className="p-4 rounded-full bg-accent-red text-white hover:bg-red-600 transition-colors"
          >
            <PhoneOff size={24} />
          </motion.button>
        </div>
        
        <div className="text-center mt-3">
          <p className="text-xs text-gray-500">
            {isMuted ? '🔇 Microphone muted' : '🎤 Listening...'}
          </p>
        </div>
      </div>
    </div>
  );
};
