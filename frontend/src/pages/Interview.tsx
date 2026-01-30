import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { useSessionStore } from '../stores/sessionStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useAudio } from '../hooks/useAudio';
import { useMediaPipe } from '../hooks/useMediaPipe';
import { OrbVisualizer } from '../components/interview/OrbVisualizer'; // NEW
import { ChatInterface } from '../components/interview/ChatInterface';
import { VideoFeed } from '../components/interview/VideoFeed';
import { ControlBar } from '../components/interview/ControlBar';
import { WS_ENDPOINTS } from '../lib/constants';

type InterviewState = 'connecting' | 'ready' | 'ai_speaking' | 'user_turn' | 'processing' | 'completed';

export const Interview = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { selectedPersona } = useSessionStore();

  const [interviewState, setInterviewState] = useState<InterviewState>('connecting');

  // NEW: Stream State and Timer
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

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
    resetTranscript
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

  // Timer Effect
  useEffect(() => {
    let interval: any;
    if (interviewState === 'ready' || interviewState === 'ai_speaking' || interviewState === 'user_turn' || interviewState === 'processing') {
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [interviewState]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle AI messages from WebSocket
  // Handle AI messages from WebSocket
  useEffect(() => {
    if (lastAiMessage) {
      setInterviewState('ai_speaking');
    }
  }, [lastAiMessage]);

  // Listen for AI message events (legacy support if hook isn't enough)
  useEffect(() => {
    const handleAiMessage = () => {
      setInterviewState('ai_speaking');
    };
    window.addEventListener('ai-message', handleAiMessage as EventListener);
    return () => window.removeEventListener('ai-message', handleAiMessage as EventListener);
  }, []);

  // Handle speech end detection (USER -> AI)
  useEffect(() => {
    if (finalTranscript.includes('[SUBMIT]')) {
      // "Submit" keyword logic
      submitResponse(finalTranscript.replace('[SUBMIT]', '').trim());
    }
  }, [finalTranscript]);

  const submitResponse = (text: string) => {
    if (text) {
      // Send as conversation text
      sendMessage({ type: 'conversation', mode: 'browser', text: text });

      // Add to local store for UI
      useSessionStore.getState().addMessage({
        id: Date.now().toString(),
        role: 'user',
        content: text,
        timestamp: Date.now()
      });

      resetTranscript();
      setInterviewState('processing');
    }
  };

  const handleSendMessage = (text: string) => {
    submitResponse(text);
  };

  // Setup & History
  useEffect(() => {
    const init = async () => {
      try {
        // Fetch history first
        const historyRes = await api.get(`/api/session/${sessionId}/messages`);
        if (historyRes.data && Array.isArray(historyRes.data)) {
          // Clear existing messages? 
          // useSessionStore.getState().resetSession(); // No, we might want to keep other state
          // Actually, we should probably check if store has messages to avoid duplicates if re-mounting
          // But since we navigate here, store might be fresh or stale.
          // Let's rely on store being reset on Lobby start?
          // Lobby.tsx calls setSessionId but doesn't explicitly clear messages.
          // We should probably clear messages when picking a new persona in Lobby.

          // For now, let's just add them if store is empty
          const currentMessages = useSessionStore.getState().messages;
          if (currentMessages.length === 0) {
            historyRes.data.forEach((msg: any) => {
              useSessionStore.getState().addMessage({
                id: msg.id || Date.now().toString() + Math.random(),
                role: msg.role as 'user' | 'ai',
                content: msg.content,
                timestamp: msg.timestamp * 1000 // DB timestamp is seconds (time.time()), JS needs ms
              });
            });
          }
        }

        const s = await startCamera();
        streamRef.current = s;
        setStream(s);
        await startRecording();
        setInterviewState('ready');
      } catch (error) {
        console.error("Setup failed", error);
      }
    };

    if (sessionId) init();

    return () => {
      stopCamera();
      stopRecording();
      stopListening();
      disconnect();
    };
  }, [sessionId]);

  // Auto-listen when AI stops
  useEffect(() => {
    const handleSpeechEnd = () => {
      if (interviewState === 'ai_speaking') {
        setInterviewState('user_turn');
        startListening();
      }
    };
    window.speechSynthesis.addEventListener('end', handleSpeechEnd);
    return () => window.speechSynthesis.removeEventListener('end', handleSpeechEnd);
  }, [interviewState, startListening]);

  const handleEndInterview = useCallback(() => {
    sendMessage({ type: 'end' });
    setInterviewState('completed');
    setTimeout(() => navigate(`/report/${sessionId}`), 1000);
  }, [sendMessage, navigate, sessionId]);

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden flex flex-col">
      {/* Top Bar */}
      <div className="bg-neutral-900/50 border-b border-neutral-800 p-4 flex justify-between items-center z-20 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="font-mono text-sm tracking-wider text-neutral-400">REC {formatTime(elapsedTime)}</span>
        </div>
        <div className="text-sm font-medium text-neutral-300">
          {selectedPersona?.name || 'AI Interviewer'}
        </div>
      </div>


      {/* Main Stage */}
      <div className="flex-1 flex flex-col md:flex-row p-6 gap-6 relative z-10">

        {/* Center: AI Interactions */}
        <div className="flex-1 flex flex-col items-center justify-center relative">

          {/* Orb Visualizer */}\n          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="mb-8"
          >
            <OrbVisualizer
              isActive={interviewState === 'ai_speaking' || window.speechSynthesis.speaking}
              audioLevel={audioLevel}
            />
          </motion.div>

          {/* Chat Interface */}
          <div className="w-full max-w-2xl px-4 z-20">
            <ChatInterface onSendMessage={handleSendMessage} disabled={interviewState === 'processing' || interviewState === 'ai_speaking'} />
          </div>

          {/* Transcript (Optional: show live transcript above input if needed, but ChatInterface handles history) */}
          <AnimatePresence>
            {isListening && transcript && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="absolute bottom-4 left-1/2 -translate-x-1/2 text-neutral-400 font-mono text-sm bg-black/60 px-4 py-2 rounded-full backdrop-blur-sm pointer-events-none"
              >
                {transcript}<span className="animate-pulse">_</span>
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* PIP Video Feed */}
        <div className="absolute bottom-6 right-6 w-48 aspect-video rounded-xl overflow-hidden border border-neutral-700 shadow-2xl bg-black">
          <VideoFeed stream={stream} />
        </div>
      </div>

      {/* Bottom Controls */}
      <ControlBar
        isMuted={isMuted}
        onToggleMute={toggleMute}
        onEndInterview={handleEndInterview}
      />
    </div>
  );
};
