import { motion } from 'framer-motion';
import { Building2, Check } from 'lucide-react';
import { useSessionStore, type Persona } from '../../stores/sessionStore';
import { Card } from '../ui/Card';

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

export const PersonaSelector = () => {
  const { selectedPersona, setSelectedPersona } = useSessionStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {PERSONAS.map((persona) => (
        <motion.div
          key={persona.id}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Card
            className={`cursor-pointer transition-all relative ${
              selectedPersona?.id === persona.id
                ? 'ring-2 ring-primary-blue bg-blue-50'
                : 'hover:shadow-lg'
            }`}
            onClick={() => setSelectedPersona(persona)}
          >
            {selectedPersona?.id === persona.id && (
              <div className="absolute top-3 right-3 bg-primary-blue text-white rounded-full p-1">
                <Check size={16} />
              </div>
            )}
            <div className="flex items-start gap-3">
              <div className="text-3xl">{persona.icon}</div>
              <div className="flex-1">
                <h4 className="font-semibold text-slate-dark mb-1">{persona.name}</h4>
                <div className="flex items-center gap-1 text-sm text-gray-600 mb-2">
                  <Building2 size={14} />
                  <span>{persona.company}</span>
                </div>
                <p className="text-sm text-gray-500">{persona.description}</p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};
