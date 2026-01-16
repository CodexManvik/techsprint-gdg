import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Maximize2, Minimize2 } from 'lucide-react';

interface VideoFeedProps {
  stream: MediaStream | null;
}

export const VideoFeed = ({ stream }: VideoFeedProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const position = { x: 20, y: 20 };

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
        top: 0,
        left: 0,
        right: window.innerWidth - (isExpanded ? 400 : 200),
        bottom: window.innerHeight - (isExpanded ? 300 : 150),
      }}
      initial={{ x: position.x, y: position.y }}
      className={`fixed z-40 rounded-xl overflow-hidden shadow-lg border-2 border-white ${
        isExpanded ? 'w-96 h-72' : 'w-48 h-36'
      }`}
      style={{ cursor: isExpanded ? 'default' : 'move' }}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 rounded-lg text-white transition-colors"
      >
        {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
      </button>
    </motion.div>
  );
};
