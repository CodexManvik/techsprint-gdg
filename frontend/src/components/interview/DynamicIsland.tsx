import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

interface DynamicIslandProps {
  message: string | null;
  type?: 'info' | 'warning' | 'success';
}

export const DynamicIsland = ({ message, type = 'info' }: DynamicIslandProps) => {
  const icons = {
    info: <Info size={18} />,
    warning: <AlertCircle size={18} />,
    success: <CheckCircle size={18} />,
  };

  const colors = {
    info: 'bg-primary-blue',
    warning: 'bg-accent-amber',
    success: 'bg-green-500',
  };

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.9 }}
          className={`fixed top-6 left-1/2 -translate-x-1/2 z-50 ${colors[type]} text-white px-6 py-3 rounded-full shadow-lg flex items-center gap-3 max-w-md`}
        >
          {icons[type]}
          <span className="font-medium">{message}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
