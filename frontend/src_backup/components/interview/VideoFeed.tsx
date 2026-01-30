import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface VideoFeedProps {
  stream: MediaStream | null;
}

export const VideoFeed = ({ stream }: VideoFeedProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <motion.div
      drag={!isExpanded}
      dragMomentum={false}
      dragElastic={0}
      dragConstraints={{
        top: 80,
        left: 20,
        right: window.innerWidth - (isExpanded ? 420 : 220),
        bottom: window.innerHeight - (isExpanded ? 320 : 160),
      }}
      initial={{ x: 20, y: 80, opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
      className={cn(
        'fixed z-40 rounded-2xl overflow-hidden',
        'border-2 border-primary/30',
        'shadow-[0_0_30px_rgba(58,12,163,0.3)]',
        isExpanded ? 'w-[400px] h-[300px]' : 'w-[200px] h-[150px]',
        'transition-all duration-300'
      )}
      style={{ cursor: isExpanded ? 'default' : 'grab' }}
      whileDrag={{ cursor: 'grabbing' }}
    >
      {/* Gradient border effect */}
      <div className="absolute inset-0 rounded-2xl p-[2px] bg-gradient-to-br from-primary via-accent-purple to-primary/50 z-0">
        <div className="absolute inset-[2px] rounded-2xl bg-background" />
      </div>

      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="relative z-10 w-full h-full object-cover rounded-2xl"
      />

      {/* Overlay gradient */}
      <div className="absolute inset-0 z-20 bg-gradient-to-t from-black/30 to-transparent pointer-events-none rounded-2xl" />

      {/* Controls */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'absolute top-3 right-3 z-30 p-2 rounded-lg',
          'bg-black/40 backdrop-blur-sm hover:bg-black/60',
          'text-white transition-colors'
        )}
      >
        {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
      </motion.button>

      {/* Recording indicator */}
      <div className="absolute top-3 left-3 z-30 flex items-center gap-2 px-2 py-1 rounded-full bg-black/40 backdrop-blur-sm">
        <motion.div
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-2 h-2 rounded-full bg-error"
        />
        <span className="text-xs text-white font-medium">LIVE</span>
      </div>
    </motion.div>
  );
};
