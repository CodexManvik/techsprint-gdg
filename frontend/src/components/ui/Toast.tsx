import { useEffect } from 'react';
import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

interface ToastProps {
  message: string;
  type?: 'info' | 'error' | 'success' | 'warning';
  onClose: () => void;
  duration?: number;
}

export const Toast = ({ message, type = 'info', onClose, duration = 5000 }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const typeStyles = {
    info: 'bg-primary-blue text-white',
    error: 'bg-accent-red text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-accent-amber text-white',
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={cn(
          'fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 max-w-md',
          typeStyles[type]
        )}
      >
        <p className="flex-1">{message}</p>
        <button onClick={onClose} className="hover:opacity-80 transition-opacity">
          <X size={18} />
        </button>
      </motion.div>
    </AnimatePresence>
  );
};
