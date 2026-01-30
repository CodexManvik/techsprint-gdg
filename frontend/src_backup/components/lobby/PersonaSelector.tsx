import { motion } from 'framer-motion';
import { Building2, Check, Plus } from 'lucide-react';
import { useSessionStore, type Persona } from '../../stores/sessionStore';
import { cn } from '../../lib/utils';

const PERSONAS: Persona[] = [
  { id: 'google-sre', name: 'Site Reliability Engineer', company: 'Google', icon: '🔧', description: 'Focus on system design and scalability' },
  { id: 'amazon-bar', name: 'Bar Raiser', company: 'Amazon', icon: '📊', description: 'Leadership principles and behavioral' },
  { id: 'meta-e5', name: 'E5 Engineer', company: 'Meta', icon: '⚡', description: 'Product thinking and impact' },
  { id: 'microsoft-senior', name: 'Senior SDE', company: 'Microsoft', icon: '💻', description: 'Technical depth and architecture' },
  { id: 'apple-ict', name: 'ICT4', company: 'Apple', icon: '🍎', description: 'Design and user experience focus' },
  { id: 'netflix-senior', name: 'Senior Engineer', company: 'Netflix', icon: '🎬', description: 'High performance systems' },
  { id: 'uber-staff', name: 'Staff Engineer', company: 'Uber', icon: '🚗', description: 'Real-time systems expertise' },
  { id: 'airbnb-l5', name: 'L5 Engineer', company: 'Airbnb', icon: '🏠', description: 'Full-stack and product sense' },
  { id: 'stripe-l3', name: 'L3 Engineer', company: 'Stripe', icon: '💳', description: 'API design and payments' },
  { id: 'twitter-senior', name: 'Senior Engineer', company: 'Twitter', icon: '🐦', description: 'Distributed systems' },
  { id: 'linkedin-staff', name: 'Staff Engineer', company: 'LinkedIn', icon: '💼', description: 'Data and ML systems' },
  { id: 'startup-founding', name: 'Founding Engineer', company: 'Startup', icon: '🚀', description: 'Generalist with ownership' },
];

interface PersonaSelectorProps {
  onCustomPersonaClick?: () => void;
}

export const PersonaSelector = ({ onCustomPersonaClick }: PersonaSelectorProps) => {
  const { selectedPersona, setSelectedPersona } = useSessionStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Custom Persona Card */}
      <motion.div
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={onCustomPersonaClick}
        className={cn(
          'relative rounded-xl p-5 cursor-pointer transition-all duration-300',
          'border-2 border-dashed border-primary/30 hover:border-primary/60',
          'bg-primary/5 hover:bg-primary/10'
        )}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
            <Plus className="w-6 h-6 text-primary" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-foreground mb-1">Custom Persona</h4>
            <p className="text-sm text-foreground-muted">Create from job description</p>
          </div>
        </div>
      </motion.div>

      {/* Preset Personas */}
      {PERSONAS.map((persona, index) => {
        const isSelected = selectedPersona?.id === persona.id;

        return (
          <motion.div
            key={persona.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            <div
              className={cn(
                'relative rounded-xl p-5 cursor-pointer transition-all duration-300',
                'border border-border hover:border-primary/50',
                isSelected
                  ? 'bg-primary/10 border-primary glow'
                  : 'glass hover:bg-surface-light'
              )}
              onClick={() => setSelectedPersona(persona)}
            >
              {/* Selection indicator */}
              {isSelected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary flex items-center justify-center"
                >
                  <Check className="w-4 h-4 text-white" />
                </motion.div>
              )}

              <div className="flex items-start gap-4">
                <motion.div
                  className={cn(
                    'text-3xl w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
                    isSelected ? 'bg-primary/20' : 'bg-surface-elevated'
                  )}
                  whileHover={{ scale: 1.1, rotate: 5 }}
                >
                  {persona.icon}
                </motion.div>
                <div className="flex-1 min-w-0">
                  <h4 className={cn(
                    'font-semibold mb-1 transition-colors',
                    isSelected ? 'text-primary' : 'text-foreground'
                  )}>
                    {persona.name}
                  </h4>
                  <div className="flex items-center gap-1.5 text-sm text-foreground-muted mb-2">
                    <Building2 className="w-3.5 h-3.5" />
                    <span>{persona.company}</span>
                  </div>
                  <p className="text-sm text-foreground-muted line-clamp-2">
                    {persona.description}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
