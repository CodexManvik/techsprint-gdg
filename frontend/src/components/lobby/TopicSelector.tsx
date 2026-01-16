import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { useSessionStore } from '../../stores/sessionStore';

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
    <div className="space-y-3">
      <label className="text-sm font-medium text-slate-dark">Interview Topics</label>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TOPICS.map((topic) => {
          const isSelected = topics.includes(topic.id);
          
          return (
            <motion.button
              key={topic.id}
              onClick={() => toggleTopic(topic.id)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`relative px-4 py-3 rounded-lg border-2 transition-all text-left ${
                isSelected
                  ? 'border-primary-blue bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 bg-primary-blue text-white rounded-full p-0.5">
                  <Check size={12} />
                </div>
              )}
              <div className="text-2xl mb-1">{topic.icon}</div>
              <div className="text-sm font-medium text-slate-dark">{topic.label}</div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};
