import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { useSessionStore } from '../../stores/sessionStore';
import { cn } from '../../lib/utils';

const TOPICS = [
  { id: 'system-design', label: 'System Design', icon: '🏗️' },
  { id: 'dsa', label: 'Data Structures & Algorithms', icon: '🧮' },
  { id: 'behavioral', label: 'Behavioral', icon: '💬' },
  { id: 'frontend', label: 'Frontend', icon: '🎨' },
  { id: 'backend', label: 'Backend', icon: '⚙️' },
  { id: 'database', label: 'Database', icon: '🗄️' },
  { id: 'devops', label: 'DevOps', icon: '🔧' },
  { id: 'security', label: 'Security', icon: '🔒' },
];

export const TopicSelector = () => {
  const { topics, toggleTopic } = useSessionStore();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">Interview Topics</label>
        <span className="text-xs text-foreground-muted">
          {topics.length} selected
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOPICS.map((topic, index) => {
          const isSelected = topics.includes(topic.id);

          return (
            <motion.button
              key={topic.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => toggleTopic(topic.id)}
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              className={cn(
                'relative px-4 py-4 rounded-xl transition-all duration-300 text-left',
                'border overflow-hidden',
                isSelected
                  ? 'border-primary bg-primary/10 glow'
                  : 'border-border glass hover:border-primary/50'
              )}
            >
              {/* Selected check */}
              {isSelected && (
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  exit={{ scale: 0, rotate: 180 }}
                  className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center"
                >
                  <Check className="w-3 h-3 text-white" />
                </motion.div>
              )}

              {/* Background glow on selected */}
              {isSelected && (
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent" />
              )}

              <motion.div
                className="text-2xl mb-2"
                animate={{ scale: isSelected ? 1.1 : 1 }}
              >
                {topic.icon}
              </motion.div>
              <div className={cn(
                'text-sm font-medium transition-colors',
                isSelected ? 'text-primary' : 'text-foreground'
              )}>
                {topic.label}
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Selection hint */}
      {topics.length === 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm text-warning text-center py-2"
        >
          Select at least one topic to continue
        </motion.p>
      )}
    </div>
  );
};
