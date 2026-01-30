import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check, Home } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { ResumeUploader } from '../components/lobby/ResumeUploader';
import { PersonaSelector } from '../components/lobby/PersonaSelector';
import { DifficultySlider } from '../components/lobby/DifficultySlider';
import { TopicSelector } from '../components/lobby/TopicSelector';
import { AudioModeSelector } from '../components/lobby/AudioModeSelector';
import { TechCheck } from '../components/lobby/TechCheck';
import { useSessionStore } from '../stores/sessionStore';
import { Toast } from '../components/ui/Toast';
import { DotBackground } from '../components/ui/grid-background';
import { cn } from '../lib/utils';

const STEPS = ['Identity', 'Context', 'Tech Check'];

export const Lobby = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigator = useNavigate();
  const { resumeFile, selectedPersona, topics, setSelectedPersona } = useSessionStore();
  const [showCustomPersona, setShowCustomPersona] = useState(false);
  const [customPersona, setCustomPersona] = useState({
    role: '',
    company: '',
    description: ''
  });

  const canProceedFromStep = (step: number): boolean => {
    switch (step) {
      case 0:
        return !!resumeFile;
      case 1:
        return !!selectedPersona && topics.length > 0;
      case 2:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (!canProceedFromStep(currentStep)) {
      if (currentStep === 0) {
        setError('Please upload your resume so I can ask relevant questions.');
      } else if (currentStep === 1) {
        setError('Please select an interviewer persona and at least one topic.');
      }
      return;
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStartInterview = () => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    useSessionStore.getState().setSessionId(sessionId);
    navigator('/interview');
  };

  const handleCreateCustomPersona = () => {
    if (!customPersona.role || !customPersona.company || !customPersona.description) {
      setError('Please fill in all fields for the custom persona');
      return;
    }

    const newPersona = {
      id: `custom-${Date.now()}`,
      name: customPersona.role,
      company: customPersona.company,
      description: customPersona.description,
      icon: '👤'
    };

    setSelectedPersona(newPersona);
    setShowCustomPersona(false);
  };

  return (
    <DotBackground containerClassName="min-h-screen">
      {error && <Toast message={error} type="error" onClose={() => setError(null)} />}

      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 glass border-b border-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigator('/')}
            className="flex items-center gap-2 text-foreground-muted hover:text-foreground transition-colors"
          >
            <Home className="w-5 h-5" />
            <span className="font-medium">Home</span>
          </motion.button>
          <ThemeToggle />
        </div>
      </div>

      <div className="max-w-6xl mx-auto pt-24 pb-12 px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <h1 className="text-3xl font-bold text-foreground mb-2">Setup Your Interview</h1>
          <p className="text-foreground-muted">Let's get everything ready for your practice session</p>
        </motion.div>

        {/* Step Indicator */}
        <div className="mb-10">
          <div className="flex items-center justify-between max-w-2xl mx-auto">
            {STEPS.map((step, index) => (
              <div key={step} className="flex items-center flex-1">
                <div className="flex items-center gap-3">
                  <motion.div
                    animate={{
                      scale: index === currentStep ? 1.1 : 1,
                    }}
                    className={cn(
                      'w-12 h-12 rounded-full flex items-center justify-center font-semibold transition-all duration-300',
                      index < currentStep
                        ? 'bg-success text-white'
                        : index === currentStep
                          ? 'bg-gradient-to-br from-primary to-accent-purple text-white glow'
                          : 'bg-surface-elevated text-foreground-muted'
                    )}
                  >
                    {index < currentStep ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      index + 1
                    )}
                  </motion.div>
                  <span
                    className={cn(
                      'font-medium hidden sm:block',
                      index <= currentStep ? 'text-foreground' : 'text-foreground-muted'
                    )}
                  >
                    {step}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div className="flex-1 mx-4 h-1 rounded-full bg-surface-elevated overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary to-success rounded-full"
                      initial={{ width: 0 }}
                      animate={{
                        width: index < currentStep ? '100%' : '0%'
                      }}
                      transition={{ duration: 0.4 }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.3 }}
          >
            {currentStep === 0 && (
              <div className="space-y-6">
                <div className="glass rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">Upload Your Resume</h2>
                  <p className="text-foreground-muted mb-6">
                    I'll analyze your background to ask personalized questions
                  </p>
                  <ResumeUploader />
                </div>
              </div>
            )}

            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="glass rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">Choose Your Interviewer</h2>
                  <p className="text-foreground-muted mb-6">
                    Select the type of interviewer you want to practice with
                  </p>
                  <PersonaSelector onCustomPersonaClick={() => setShowCustomPersona(true)} />
                </div>

                {/* Custom Persona Modal */}
                <AnimatePresence>
                  {showCustomPersona && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                    >
                      <div className="bg-surface border border-border rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
                        <button
                          onClick={() => setShowCustomPersona(false)}
                          className="absolute top-4 right-4 text-foreground-muted hover:text-foreground"
                        >
                          ✕
                        </button>
                        <h3 className="text-xl font-bold text-foreground mb-4">Create Custom Persona</h3>

                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-foreground-muted mb-1">Role / Job Title</label>
                            <input
                              type="text"
                              value={customPersona.role}
                              onChange={(e) => setCustomPersona({ ...customPersona, role: e.target.value })}
                              placeholder="e.g. Product Manager"
                              className="w-full bg-surface-elevated border border-border rounded-lg px-4 py-2 text-foreground focus:outline-none focus:border-primary transition-colors"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-foreground-muted mb-1">Company</label>
                            <input
                              type="text"
                              value={customPersona.company}
                              onChange={(e) => setCustomPersona({ ...customPersona, company: e.target.value })}
                              placeholder="e.g. Tech Corp"
                              className="w-full bg-surface-elevated border border-border rounded-lg px-4 py-2 text-foreground focus:outline-none focus:border-primary transition-colors"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-foreground-muted mb-1">Description / Focus</label>
                            <textarea
                              value={customPersona.description}
                              onChange={(e) => setCustomPersona({ ...customPersona, description: e.target.value })}
                              placeholder="What should this interviewer focus on?"
                              className="w-full bg-surface-elevated border border-border rounded-lg px-4 py-2 text-foreground focus:outline-none focus:border-primary transition-colors h-24 resize-none"
                            />
                          </div>
                          <Button
                            variant="gradient"
                            className="w-full"
                            onClick={handleCreateCustomPersona}
                          >
                            Create Persona
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="glass rounded-2xl p-8">
                  <h2 className="text-2xl font-bold text-foreground mb-6">Configure Interview</h2>
                  <div className="space-y-8">
                    <DifficultySlider />
                    <TopicSelector />
                    <AudioModeSelector />
                  </div>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <TechCheck onComplete={handleStartInterview} />
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        {currentStep < 2 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between mt-8"
          >
            <Button
              variant="ghost"
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back
            </Button>

            <Button
              variant="gradient"
              onClick={handleNext}
              disabled={!canProceedFromStep(currentStep)}
              size="lg"
            >
              Next
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </motion.div>
        )}
      </div>
    </DotBackground>
  );
};
