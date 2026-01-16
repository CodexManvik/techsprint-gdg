import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
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

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-5xl w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 mb-4">
            <Sparkles className="text-primary-blue" size={32} />
            <h1 className="text-5xl font-bold text-slate-dark">Interview Mirror</h1>
          </div>
          <p className="text-xl text-gray-600">
            AI-powered interview coaching that helps you shine
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer" onClick={handleNewInterview}>
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-primary-blue rounded-full flex items-center justify-center mx-auto">
                  <Sparkles className="text-white" size={32} />
                </div>
                <h2 className="text-2xl font-semibold text-slate-dark">Start New Interview</h2>
                <p className="text-gray-600">
                  Begin a fresh interview session with AI coaching and real-time feedback
                </p>
                <Button className="w-full" size="lg">
                  Get Started
                  <ArrowRight className="ml-2" size={20} />
                </Button>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="h-full">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto">
                  <ArrowRight className="text-slate-dark" size={32} />
                </div>
                <h2 className="text-2xl font-semibold text-slate-dark text-center">Continue Session</h2>
                <p className="text-gray-600 text-center">
                  Resume a previous interview using your Session ID
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-gray-700">
                  <p className="font-semibold text-primary-blue mb-1">💡 Where to find your Session ID:</p>
                  <p>Your Session ID is displayed at the top of your interview report. You can also download the report as a PDF to save it.</p>
                </div>
                <div className="space-y-3">
                  <Input
                    placeholder="Enter Session ID (e.g., session_1234567890_abc123)"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleContinue()}
                  />
                  <Button
                    variant="secondary"
                    className="w-full"
                    size="lg"
                    onClick={handleContinue}
                    disabled={!sessionId.trim()}
                  >
                    Continue
                    <ArrowRight className="ml-2" size={20} />
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 text-center text-gray-500 text-sm"
        >
          <p>Powered by MediaPipe, FastAPI, and Gemini AI</p>
        </motion.div>
      </div>
    </div>
  );
};
