import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ResumeUploader } from '../components/lobby/ResumeUploader';
import { PersonaSelector } from '../components/lobby/PersonaSelector';
import { DifficultySlider } from '../components/lobby/DifficultySlider';
import { TopicSelector } from '../components/lobby/TopicSelector';
import { AudioModeSelector } from '../components/lobby/AudioModeSelector';
import { TechCheck } from '../components/lobby/TechCheck';
import { useSessionStore } from '../stores/sessionStore';
import { Toast } from '../components/ui/Toast';

const STEPS = ['Identity', 'Context', 'Tech Check'];

export const Lobby = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { resumeFile, selectedPersona, topics } = useSessionStore();

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
        setError('I need to know who you are first! Please drop your resume so I can ask relevant questions.');
      } else if (currentStep === 1) {
        setError('Please select an interviewer persona and at least one topic to continue.');
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
    // Generate a unique session ID
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    useSessionStore.getState().setSessionId(sessionId);
    console.log('Starting interview with session ID:', sessionId);
    
    navigate('/interview');
  };

  return (
    <div className="min-h-screen p-6">
      {error && <Toast message={error} type="error" onClose={() => setError(null)} />}
      
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-slate-dark mb-2">Setup Your Interview</h1>
          <p className="text-gray-600">Let's get everything ready for your practice session</p>
        </motion.div>

        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step} className="flex items-center flex-1">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                      index < currentStep
                        ? 'bg-green-500 text-white'
                        : index === currentStep
                        ? 'bg-primary-blue text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {index < currentStep ? <Check size={20} /> : index + 1}
                  </div>
                  <span
                    className={`font-medium ${
                      index <= currentStep ? 'text-slate-dark' : 'text-gray-400'
                    }`}
                  >
                    {step}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-4 rounded ${
                      index < currentStep ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {currentStep === 0 && (
              <div className="space-y-6">
                <div className="bg-white rounded-xl shadow-soft p-8">
                  <h2 className="text-2xl font-semibold text-slate-dark mb-4">Upload Your Resume</h2>
                  <p className="text-gray-600 mb-6">
                    I'll analyze your background to ask personalized questions
                  </p>
                  <ResumeUploader />
                </div>
              </div>
            )}

            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="bg-white rounded-xl shadow-soft p-8">
                  <h2 className="text-2xl font-semibold text-slate-dark mb-4">Choose Your Interviewer</h2>
                  <p className="text-gray-600 mb-6">
                    Select the type of interviewer you want to practice with
                  </p>
                  <PersonaSelector />
                </div>

                <div className="bg-white rounded-xl shadow-soft p-8">
                  <h2 className="text-2xl font-semibold text-slate-dark mb-6">Configure Interview</h2>
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

        {currentStep < 2 && (
          <div className="flex items-center justify-between mt-8">
            <Button
              variant="ghost"
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="mr-2" size={20} />
              Back
            </Button>

            <Button
              onClick={handleNext}
              disabled={!canProceedFromStep(currentStep)}
              size="lg"
            >
              Next
              <ArrowRight className="ml-2" size={20} />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
