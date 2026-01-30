import { motion } from 'framer-motion';

interface OrbVisualizerProps {
    isActive: boolean;
    audioLevel?: number; // 0 to 1 ideally, but might come as 0-255 or similar
}

export const OrbVisualizer = ({ isActive, audioLevel = 0 }: OrbVisualizerProps) => {
    // Normalize audio level for scaling (assuming 0-100 or small float)
    // If audioLevel is usually small (0-1), scale it up. If 0-255, scale down.
    // Let's assume it's normalized 0-1 for animation factors.

    const scale = isActive ? 1 + (audioLevel * 0.5) : 1;
    const glow = isActive ? 20 + (audioLevel * 50) : 20;

    return (
        <div className="relative w-64 h-64 flex items-center justify-center">
            {/* Core Orb */}
            <motion.div
                animate={{
                    scale: [1, 1.05, 1],
                    rotate: [0, 360],
                }}
                transition={{
                    rotate: { duration: 10, repeat: Infinity, ease: "linear" },
                    scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                }}
                className="relative z-10 w-32 h-32 rounded-full bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 blur-sm mix-blend-screen"
                style={{
                    boxShadow: `0 0 ${glow}px rgba(59, 130, 246, 0.6)`
                }}
            />

            {/* Outer Rings / Waves */}
            {isActive && (
                <>
                    <motion.div
                        animate={{ scale: [1, 1.5], opacity: [0.8, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                        className="absolute z-0 w-32 h-32 rounded-full border border-blue-400/30"
                    />
                    <motion.div
                        animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
                        className="absolute z-0 w-32 h-32 rounded-full border border-purple-400/30"
                    />
                </>
            )}

            {/* Reactive Scale Layer */}
            <motion.div
                animate={{ scale: scale }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className="absolute z-10 w-32 h-32 rounded-full bg-white/10 blur-xl"
            />
        </div>
    );
};
