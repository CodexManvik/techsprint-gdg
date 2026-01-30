import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionStore } from '../stores/sessionStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useAudio } from '../hooks/useAudio';
import { useMediaPipe } from '../hooks/useMediaPipe';
import { AudioVisualizer } from '../components/interview/AudioVisualizer';
import { VideoFeed } from '../components/interview/VideoFeed';
import { ControlBar } from '../components/interview/ControlBar';
import { DynamicIsland } from '../components/interview/DynamicIsland';
import { TextGenerateEffect } from '../components/ui/text-effects';
import { BackgroundBeams } from '../components/ui/background-beams';
import { WS_ENDPOINTS } from '../lib/constants';
import { cn } from '../lib/utils';

type InterviewState = 'connecting' | 'ready' | 'ai_speaking' | 'user_turn' | 'processing' | 'completed';

export const Interview = () => {
  const navigate = useNavigate();
  const { sessionId, selectedPersona } = useSessionStore();

  const [interviewState, setInterviewState] = useState<InterviewState>('connecting');
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [islandMessage, setIslandMessage] = useState<string | null>(null);
  const [islandType, setIslandType] = useState<'info' | 'warning' | 'success'>('info');

  const streamRef = useRef<MediaStream | null>(null);

  // WebSocket connection
  const wsUrl = sessionId ? WS_ENDPOINTS.INTERVIEW(sessionId) : '';
  const { sendMessage, disconnect, lastAiMessage } = useWebSocket(wsUrl, !!sessionId);

  // Speech recognition
  const {
    isListening,
    transcript,
    finalTranscript,
    startListening,
    stopListening,
    resetTranscript,
    isSupported: isSpeechSupported
  } = useSpeechRecognition();

  // Audio recording
  const {
    isMuted,
    audioLevel,
    startRecording,
    stopRecording,
    toggleMute
  } = useAudio();

  // Camera/MediaPipe
  const { startCamera, stopCamera } = useMediaPipe();

  const showIslandMessage = useCallback((message: string, type: 'info' | 'warning' | 'success' = 'info') => {
    setIslandMessage(message);
    setIslandType(type);
    setTimeout(() => setIslandMessage(null), 4000);
  }, []);

  // Handle AI messages from WebSocket
  useEffect(() => {
    if (lastAiMessage) {
      setCurrentQuestion(lastAiMessage);
      setInterviewState('ai_speaking');
    }
  }, [lastAiMessage]);

  // Listen for AI message events
  useEffect(() => {
    const handleAiMessage = (event: CustomEvent) => {
      setCurrentQuestion(event.detail.text);
      setInterviewState('ai_speaking');
    };

    window.addEventListener('ai-message', handleAiMessage as EventListener);
    return () => window.removeEventListener('ai-message', handleAiMessage as EventListener);
  }, []);

  // Handle speech end detection
  useEffect(() => {
    if (finalTranscript.includes('[SUBMIT]')) {
      const cleanTranscript = finalTranscript.replace('[SUBMIT]', '').trim();
      if (cleanTranscript) {
        sendMessage({ type: 'answer', text: cleanTranscript });
        resetTranscript();
        setInterviewState('processing');
      }
    }
  }, [finalTranscript, sendMessage, resetTranscript]);

  // Initialize interview
  useEffect(() => {
    const init = async () => {
      try {
        const stream = await startCamera();
        streamRef.current = stream;
        await startRecording();
        setInterviewState('ready');
        showIslandMessage('Interview ready. Speak when prompted.', 'info');
      } catch (error) {
        showIslandMessage('Failed to initialize camera or microphone', 'warning');
      }
    };

    if (sessionId) {
      init();
    }

    return () => {
      stopCamera();
      stopRecording();
      stopListening();
      disconnect();
    };
  }, [sessionId, startCamera, stopCamera, startRecording, stopRecording, stopListening, disconnect, showIslandMessage]);

  // Start listening when AI stops speaking
  useEffect(() => {
    if (interviewState === 'user_turn' && isSpeechSupported && !isMuted) {
      startListening();
    }
  }, [interviewState, isSpeechSupported, isMuted, startListening]);

  // Handle speech synthesis end to switch to user turn
  useEffect(() => {
    const handleSpeechEnd = () => {
      if (interviewState === 'ai_speaking') {
        setInterviewState('user_turn');
      }
    };

    window.speechSynthesis.addEventListener('end', handleSpeechEnd);
    return () => {
      window.speechSynthesis.removeEventListener('end', handleSpeechEnd);
    };
  }, [interviewState]);

  const handleEndInterview = useCallback(() => {
    sendMessage({ type: 'end' });
    setInterviewState('completed');
    showIslandMessage('Interview completed!', 'success');
    setTimeout(() => navigate(`/report/${sessionId}`), 2000);
  }, [sendMessage, navigate, sessionId, showIslandMessage]);

  const handleToggleMute = useCallback(() => {
    toggleMute();
    if (!isMuted) {
      stopListening();
    } else if (interviewState === 'user_turn') {
      startListening();
    }
  }, [isMuted, toggleMute, stopListening, startListening, interviewState]);

  // Clean display transcript (remove interim markers)
  const displayTranscript = transcript.replace('[interim]', '').trim();

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundBeams className="opacity-20" />

      <DynamicIsland message={islandMessage} type={islandType} />

      <VideoFeed stream={streamRef.current} />

      {/* Main content */}
      <div className="relative z-10 max-w-4xl mx-auto pt-20 pb-32 px-6">
        {/* AI Visualizer */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex justify-center mb-12"
        >
          <AudioVisualizer
            audioLevel={audioLevel}
            isActive={interviewState === 'ai_speaking' || window.speechSynthesis.speaking}
          />
        </motion.div>

        {/* Question Display */}
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="glass rounded-2xl p-8 mb-8"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <span className="text-sm font-medium text-foreground-muted">
                  {selectedPersona?.name || 'AI Interviewer'} • {selectedPersona?.company || 'Tech Company'}
                </span>
              </div>
              <TextGenerateEffect
                words={currentQuestion}
                className="text-xl text-foreground leading-relaxed"
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* User Transcript */}
        <AnimatePresence>
          {(interviewState === 'user_turn' || displayTranscript) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className={cn(
                'glass rounded-2xl p-6 border-2 transition-all',
                isListening ? 'border-success/50 shadow-[0_0_20px_rgba(34,197,94,0.3)]' : 'border-border'
              )}
            >
              <div className="flex items-center gap-2 mb-4">
                {isListening && (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 1 }}
                    className="w-3 h-3 rounded-full bg-success"
                  />
                )}
                <span className="text-sm font-medium text-foreground-muted">
                  {isListening ? 'Listening...' : 'Your response'}
                </span>
              </div>
              <p className={cn(
                'text-lg min-h-[60px]',
                displayTranscript ? 'text-foreground' : 'text-foreground-muted italic'
              )}>
                {displayTranscript || 'Start speaking...'}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Processing indicator */}
        <AnimatePresence>
          {interviewState === 'processing' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-8"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                className="w-8 h-8 mx-auto border-2 border-primary border-t-transparent rounded-full"
              />
              <p className="mt-4 text-foreground-muted">Analyzing your response...</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Control Bar */}
      <ControlBar
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        onEndInterview={handleEndInterview}
      />
    </div>
  );
};
