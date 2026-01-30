import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

interface DynamicIslandProps {
  message: string | null;
  type?: 'info' | 'warning' | 'success';
}

export const DynamicIsland = ({ message, type = 'info' }: DynamicIslandProps) => {
  const icons = {
    info: <Info className="w-4 h-4" />,
    warning: <AlertCircle className="w-4 h-4" />,
    success: <CheckCircle className="w-4 h-4" />,
  };

  const styles = {
    info: 'bg-primary/20 border-primary/50 text-primary',
    warning: 'bg-warning/20 border-warning/50 text-warning',
    success: 'bg-success/20 border-success/50 text-success',
  };

  const glowStyles = {
    info: 'shadow-[0_0_20px_rgba(58,12,163,0.4)]',
    warning: 'shadow-[0_0_20px_rgba(245,158,11,0.4)]',
    success: 'shadow-[0_0_20px_rgba(34,197,94,0.4)]',
  };

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -30, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -30, scale: 0.8 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className={cn(
            'fixed top-6 left-1/2 -translate-x-1/2 z-50',
            'px-5 py-2.5 rounded-full',
            'border backdrop-blur-md',
            'flex items-center gap-2.5 max-w-md',
            styles[type],
            glowStyles[type]
          )}
        >
          {icons[type]}
          <span className="font-medium text-sm text-foreground">{message}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
