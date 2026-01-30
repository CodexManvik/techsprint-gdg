import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  onClose?: () => void;
}

export const Toast = ({ message, type = 'info', duration = 4000, onClose }: ToastProps) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onClose?.(), 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onClose?.(), 300);
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const styles = {
    success: 'bg-success/10 border-success/30 text-success',
    error: 'bg-error/10 border-error/30 text-error',
    warning: 'bg-warning/10 border-warning/30 text-warning',
    info: 'bg-primary/10 border-primary/30 text-primary',
  };

  const glowStyles = {
    success: 'shadow-[0_0_20px_rgba(34,197,94,0.3)]',
    error: 'shadow-[0_0_20px_rgba(239,68,68,0.3)]',
    warning: 'shadow-[0_0_20px_rgba(245,158,11,0.3)]',
    info: 'shadow-[0_0_20px_rgba(58,12,163,0.3)]',
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          className={cn(
            'fixed top-6 left-1/2 -translate-x-1/2 z-50',
            'flex items-center gap-3 px-4 py-3 rounded-xl',
            'border backdrop-blur-md',
            styles[type],
            glowStyles[type]
          )}
        >
          {icons[type]}
          <span className="text-sm font-medium text-foreground">{message}</span>
          <button
            onClick={handleClose}
            className="ml-2 p-1 rounded-lg hover:bg-surface-light transition-colors"
          >
            <X className="w-4 h-4 text-foreground-muted" />
          </button>

          {/* Progress bar */}
          <motion.div
            className="absolute bottom-0 left-0 h-0.5 bg-current rounded-full"
            initial={{ width: '100%' }}
            animate={{ width: '0%' }}
            transition={{ duration: duration / 1000, ease: 'linear' }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Toast;
