import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface AudioVisualizerProps {
  audioLevel: number;
  isActive: boolean;
}

export const AudioVisualizer = ({ audioLevel, isActive }: AudioVisualizerProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      ctx.clearRect(0, 0, width, height);

      const baseRadius = 90;
      const maxRadius = 140;
      const radius = baseRadius + (audioLevel * (maxRadius - baseRadius));

      // Outer glow gradient (purple theme)
      const outerGlow = ctx.createRadialGradient(centerX, centerY, radius - 20, centerX, centerY, radius + 60);
      outerGlow.addColorStop(0, 'rgba(58, 12, 163, 0.4)');
      outerGlow.addColorStop(0.5, 'rgba(124, 58, 237, 0.2)');
      outerGlow.addColorStop(1, 'rgba(58, 12, 163, 0)');

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius + 40, 0, Math.PI * 2);
      ctx.fillStyle = outerGlow;
      ctx.fill();

      // Main gradient circle
      const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
      gradient.addColorStop(0, 'rgba(124, 58, 237, 0.9)');
      gradient.addColorStop(0.5, 'rgba(58, 12, 163, 0.6)');
      gradient.addColorStop(1, 'rgba(58, 12, 163, 0.2)');

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

      // Animated wave points
      for (let i = 0; i < 12; i++) {
        const angle = (Math.PI * 2 * i) / 12;
        const waveOffset = Math.sin(Date.now() / 300 + i) * 15 * audioLevel;
        const waveRadius = radius + waveOffset;
        const x = centerX + Math.cos(angle) * waveRadius;
        const y = centerY + Math.sin(angle) * waveRadius;

        ctx.beginPath();
        ctx.arc(x, y, 4 + audioLevel * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(124, 58, 237, ${0.6 + audioLevel * 0.4})`;
        ctx.fill();

        // Connecting lines
        if (i > 0) {
          const prevAngle = (Math.PI * 2 * (i - 1)) / 12;
          const prevOffset = Math.sin(Date.now() / 300 + i - 1) * 15 * audioLevel;
          const prevRadius = radius + prevOffset;
          const prevX = centerX + Math.cos(prevAngle) * prevRadius;
          const prevY = centerY + Math.sin(prevAngle) * prevRadius;

          ctx.beginPath();
          ctx.moveTo(prevX, prevY);
          ctx.lineTo(x, y);
          ctx.strokeStyle = `rgba(124, 58, 237, ${0.3 + audioLevel * 0.3})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    };

    let animationId: number;
    const animate = () => {
      draw();
      animationId = requestAnimationFrame(animate);
    };

    if (isActive) {
      animate();
    }

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [audioLevel, isActive]);

  return (
    <div className="relative flex items-center justify-center">
      <canvas
        ref={canvasRef}
        width={350}
        height={350}
        className="absolute"
      />
      <motion.div
        animate={{
          scale: isActive ? [1, 1.08, 1] : 1,
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className={cn(
          "relative z-10 w-36 h-36 rounded-full flex items-center justify-center",
          "bg-gradient-to-br from-primary to-accent-purple",
          "shadow-[0_0_40px_rgba(58,12,163,0.5)]"
        )}
      >
        <div className="text-5xl">🤖</div>

        {/* Avatar placeholder text - hint for future */}
        <div className="absolute -bottom-8 text-xs text-foreground-muted whitespace-nowrap">
          AI Interviewer
        </div>
      </motion.div>
    </div>
  );
};
