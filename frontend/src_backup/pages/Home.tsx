import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { AuroraBackground } from '../components/ui/aurora-background';
import { BackgroundBeams } from '../components/ui/background-beams';
import { CardSpotlight } from '../components/ui/spotlight';
import { FlipWords, TextGenerateEffect } from '../components/ui/text-effects';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { useSessionStore } from '../stores/sessionStore';
import { API_ENDPOINTS } from '../lib/constants';

export const Home = () => {
  const [sessionId, setSessionId] = useState('');
  const navigate = useNavigate();
  const { setSessionId: setStoreSessionId } = useSessionStore();

  const handleNewInterview = () => {
    navigate('/lobby');
  };

  const handleContinue = async () => {
    if (!sessionId.trim()) return;

    try {
      const response = await fetch(API_ENDPOINTS.SESSION(sessionId));
      if (response.ok) {
        await response.json();
        setStoreSessionId(sessionId);
        navigate('/lobby');
      } else {
        alert('Session not found. Please check your Session ID.');
      }
    } catch (error) {
      alert('Failed to connect to server. Please try again.');
    }
  };

  const flipWords = ['interviews', 'confidence', 'communication', 'career'];



  return (
    <AuroraBackground className="min-h-screen">
      <BackgroundBeams className="opacity-30" />

      {/* Theme Toggle */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="max-w-6xl w-full px-6 py-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
          className="text-center mb-16"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border-glow mb-6"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-foreground">AI Interview Coach</span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="text-foreground">Master your</span>
            <br />
            <span className="inline-block mt-2">
              <FlipWords words={flipWords} className="text-gradient" duration={2500} />
            </span>
          </h1>

          <TextGenerateEffect
            words="Practice with AI-powered feedback. Analyze your body language, speech patterns, and confidence in real-time."
            className="text-xl text-foreground-muted max-w-2xl mx-auto"
            duration={0.3}
          />
        </motion.div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <CardSpotlight
              className="h-full cursor-pointer group"
              onClick={handleNewInterview}
            >
              <div className="text-center space-y-6 py-4">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center glow"
                >
                  <Sparkles className="w-10 h-10 text-white" />
                </motion.div>
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">
                    Start New Interview
                  </h2>
                  <p className="text-foreground-muted">
                    Begin a fresh interview session with AI coaching and real-time feedback
                  </p>
                </div>
                <Button variant="gradient" size="lg" className="w-full group-hover:scale-[1.02] transition-transform">
                  Get Started
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </CardSpotlight>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <CardSpotlight className="h-full">
              <div className="space-y-6 py-4">
                <div className="flex justify-center">
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    className="w-20 h-20 rounded-2xl bg-surface-elevated flex items-center justify-center"
                  >
                    <ArrowRight className="w-10 h-10 text-foreground-muted" />
                  </motion.div>
                </div>
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-foreground mb-2">
                    Continue Session
                  </h2>
                  <p className="text-foreground-muted">
                    Resume a previous interview using your Session ID
                  </p>
                </div>

                <div className="glass rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2 text-primary text-sm font-medium">
                    <span>💡</span>
                    <span>Where to find your Session ID</span>
                  </div>
                  <p className="text-sm text-foreground-muted">
                    Your Session ID is displayed at the top of your interview report.
                  </p>
                </div>

                <div className="space-y-4">
                  <Input
                    variant="glow"
                    placeholder="Enter Session ID (e.g., session_1234567890)"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleContinue()}
                  />
                  <Button
                    variant="secondary"
                    size="lg"
                    className="w-full"
                    onClick={handleContinue}
                    disabled={!sessionId.trim()}
                  >
                    Continue
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </div>
              </div>
            </CardSpotlight>
          </motion.div>
        </div>



        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="text-center text-foreground-muted text-sm mt-12"
        >
          Powered by MediaPipe, FastAPI, and Gemini AI
        </motion.p>
      </div>
    </AuroraBackground>
  );
};
