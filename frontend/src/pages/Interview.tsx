import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionStore } from '../stores/sessionStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useAudio } from '../hooks/useAudio';
import { useMediaPipe } from '../hooks/useMediaPipe';
import { AudioVisualizer } from '../components/interview/AudioVisualizer';
import { VideoFeed } from '../components/interview/VideoFeed';
import { DynamicIsland } from '../components/interview/DynamicIsland';
import { ControlBar } from '../components/interview/ControlBar';
import { WS_URL } from '../lib/constants';

export const Interview = () => {
  const navigate = useNavigate();
  const { statusHalo, currentFeedback, isConnected, audioMode, sessionId } = useSessionStore();
  const { sendMessage, disconnect, lastAiMessage } = useWebSocket(WS_URL, true);
  
  // Browser speech mode
  const { 
    isListening: isBrowserListening, 
    transcript, 
    startListening, 
    stopListening, 
    resetTranscript,
    isSupported: isSpeechSupported,
    error: speechError 
  } = useSpeechRecognition();
  
  // Backend audio mode
  const { 
    isMuted, 
    audioLevel: backendAudioLevel, 
    stopRecording, 
    toggleMute 
  } = useAudio();
  
  const { startCamera, stopCamera } = useMediaPipe();
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [aiQuestion, setAiQuestion] = useState<string>('Connecting...');
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Update AI question when we get a new message
  useEffect(() => {
    if (lastAiMessage) {
      setAiQuestion(lastAiMessage);
    }
  }, [lastAiMessage]);

  // Listen for AI messages via custom event
  useEffect(() => {
    const handleAiMessage = (event: any) => {
      if (event.detail?.text) {
        setAiQuestion(event.detail.text);
      }
    };

    window.addEventListener('ai-message', handleAiMessage);
    return () => window.removeEventListener('ai-message', handleAiMessage);
  }, []);

  useEffect(() => {
    // Prevent double initialization in React Strict Mode
    if (isInitialized) return;
    
    setIsInitialized(true);
    initializeInterview();
    return () => cleanup();
  }, []);

  // Send periodic tracking updates with actual video frames to backend
  useEffect(() => {
    if (!isConnected || !stream) return;

    console.log('📹 Starting vision tracking with camera frames...');
    
    // Create a video element to capture frames
    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const captureAndSendFrame = () => {
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw current video frame to canvas
        ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to base64 JPEG (smaller than PNG)
        const frameData = canvas.toDataURL('image/jpeg', 0.7);
        
        console.log('📤 Sending frame for vision analysis');
        
        // Send frame to backend for MediaPipe processing
        sendMessage({
          type: 'tracking',
          frame_data: frameData, // Base64 encoded frame
          landmarks: {}, // Will be populated by backend
          posture_metrics: null
        });
      }
    };

    // Capture and send frame every 2 seconds (30 frames/min)
    const trackingInterval = setInterval(captureAndSendFrame, 2000);

    return () => {
      console.log('📹 Stopping vision tracking');
      clearInterval(trackingInterval);
      video.pause();
      video.srcObject = null;
    };
  }, [isConnected, sendMessage, stream]);

  // Auto-start listening in browser mode (only once when connected)
  useEffect(() => {
    if (isConnected && audioMode === 'browser' && isSpeechSupported && !isBrowserListening) {
      console.log('Auto-starting speech recognition...');
      setTimeout(() => {
        startListening();
      }, 1000); // Wait for opening question to finish speaking
    }
  }, [isConnected, audioMode, isSpeechSupported]);

  // Update text box with transcript as user speaks
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (audioMode === 'browser' && transcript) {
      // Remove [interim] and [SUBMIT] markers for clean display
      const cleanTranscript = transcript.replace('[interim]', '').replace('[SUBMIT]', '').trim();
      setUserAnswer(cleanTranscript);
    }
  }, [audioMode, transcript]);

  // Auto-submit is now removed - user must click send button
  // This gives them time to review and edit their answer

  const initializeInterview = async () => {
    try {
      // Get session data from store
      const { sessionId, selectedPersona, difficulty, topics, resumeText } = useSessionStore.getState();
      
      // Call start-interview endpoint to initialize backend session
      if (sessionId) {
        try {
          const response = await fetch('http://localhost:8000/api/start-interview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              persona: selectedPersona?.id || 'google-sre',
              difficulty: difficulty || 'mid',
              topic: topics.join(', ') || 'System Design',
              resume_text: resumeText
            })
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('Interview session initialized:', data);
            
            // Display and speak the opening question
            if (data.opening_question) {
              setAiQuestion(data.opening_question);
              
              // Speak the opening question
              const speakOpeningQuestion = () => {
                const utterance = new SpeechSynthesisUtterance(data.opening_question);
                utterance.rate = 1.0;
                utterance.pitch = 1.1;
                utterance.volume = 1.0;
                
                // Select voice
                const voices = window.speechSynthesis.getVoices();
                if (voices.length > 0) {
                  const femaleVoice = voices.find(voice => 
                    (voice.name.includes('Zira') || 
                     voice.name.includes('Google UK English Female') ||
                     voice.name.includes('Female')) &&
                    voice.lang.startsWith('en')
                  );
                  if (femaleVoice) {
                    utterance.voice = femaleVoice;
                    console.log('Using voice:', femaleVoice.name);
                  }
                }
                
                window.speechSynthesis.speak(utterance);
              };
              
              // Wait for voices to load if needed
              if (window.speechSynthesis.getVoices().length === 0) {
                window.speechSynthesis.onvoiceschanged = () => {
                  speakOpeningQuestion();
                };
              } else {
                setTimeout(speakOpeningQuestion, 500);
              }
              
              // Dispatch event for other components
              window.dispatchEvent(new CustomEvent('ai-message', { 
                detail: { text: data.opening_question } 
              }));
            }
          }
        } catch (error) {
          console.error('Failed to initialize interview session:', error);
        }
      }
      
      const cameraStream = await startCamera();
      setStream(cameraStream);
      
      // Start recording in backend mode
      if (audioMode === 'backend') {
        await startBackendRecording(cameraStream);
      }
    } catch (error) {
      console.error('Failed to initialize interview:', error);
      alert('Failed to access camera. Please check your permissions.');
      navigate('/lobby');
    }
  };

  const startBackendRecording = async (_cameraStream: MediaStream) => {
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(audioStream);
      mediaRecorderRef.current = mediaRecorder;

      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const reader = new FileReader();
        
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1];
          sendMessage({
            type: 'conversation',
            mode: 'backend',
            audio_data: base64Audio,
            landmarks: {}
          });
        };
        
        reader.readAsDataURL(audioBlob);
        audioChunks.length = 0;
      };

      // Record in 5-second chunks
      mediaRecorder.start();
      setInterval(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
          mediaRecorder.start();
        }
      }, 5000);

    } catch (error) {
      console.error('Failed to start backend recording:', error);
    }
  };

  const cleanup = () => {
    stopCamera();
    if (audioMode === 'browser') {
      stopListening();
    } else {
      stopRecording();
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    }
  };

  const handleEndInterview = () => {
    if (confirm('Are you sure you want to end the interview?')) {
      // Stop all audio/video
      cleanup();
      
      // Stop any ongoing speech
      window.speechSynthesis.cancel();
      
      // Send end interview message
      sendMessage({ type: 'end_interview', session_id: sessionId });
      
      // Disconnect WebSocket
      disconnect();
      
      // Navigate to report with session ID
      setTimeout(() => {
        navigate(`/report?session=${sessionId || 'current'}`);
      }, 500); // Small delay to ensure message is sent
    }
  };

  const handleToggleMute = () => {
    if (audioMode === 'browser') {
      if (isBrowserListening) {
        stopListening();
      } else {
        startListening();
      }
    } else {
      toggleMute();
    }
  };

  const handleSendText = (text: string) => {
    if (!text.trim() || isSubmitting) {
      console.log('Cannot send:', !text.trim() ? 'Empty text' : 'Already submitting');
      return;
    }
    
    console.log('📤 Sending message:', text.trim());
    console.log('WebSocket connected:', isConnected);
    console.log('Audio mode:', audioMode);
    
    setIsSubmitting(true);
    
    const message = { 
      type: 'conversation',
      mode: audioMode === 'browser' ? 'browser' : 'text',
      text: text.trim(),
      landmarks: {}
    };
    
    console.log('Message payload:', message);
    sendMessage(message);
    
    setAudioLevel(0.5);
    setTimeout(() => setAudioLevel(0), 1000);
    
    // Clear the answer box and reset transcript
    setUserAnswer('');
    resetTranscript();
    
    setTimeout(() => {
      setIsSubmitting(false);
    }, 1000);
  };

  const haloClass = `status-halo-${statusHalo}`;
  const isListening = audioMode === 'browser' ? isBrowserListening : !isMuted;
  const currentAudioLevel = audioMode === 'browser' ? audioLevel : backendAudioLevel;

  // Check browser support for browser mode
  if (audioMode === 'browser' && !isSpeechSupported) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <h2 className="text-2xl font-bold text-slate-dark mb-4">Browser Speech Not Supported</h2>
          <p className="text-gray-600 mb-4">
            Your browser (likely Firefox) doesn't support Web Speech API. Please switch to Backend mode in the lobby, or use Chrome, Edge, or Safari for browser speech.
          </p>
          <button
            onClick={() => navigate('/lobby')}
            className="px-6 py-3 bg-primary-blue text-white rounded-lg hover:bg-blue-600"
          >
            Go Back to Lobby
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex items-center justify-center transition-all duration-500 ${haloClass}`}>
      <DynamicIsland
        message={currentFeedback || (isListening ? 'Listening...' : null)}
        type={statusHalo === 'red' ? 'warning' : statusHalo === 'amber' ? 'warning' : 'info'}
      />

      {speechError && audioMode === 'browser' && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-accent-red text-white px-6 py-3 rounded-lg shadow-lg">
          {speechError}
        </div>
      )}

      <div className="text-center">
        <AudioVisualizer audioLevel={currentAudioLevel} isActive={isConnected} />
        
        {!isConnected && (
          <div className="mt-8 text-gray-600">
            <p>Connecting to interview session...</p>
          </div>
        )}

        {isConnected && (
          <div className="mt-8 space-y-4">
            {/* AI Question Display */}
            {aiQuestion && (
              <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-soft p-6 mb-4">
                <div className="flex items-start gap-3">
                  <div className="text-3xl">🤖</div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-primary-blue mb-1">Interviewer</p>
                    <p className="text-slate-dark">{aiQuestion}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* User Answer Input Box */}
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-xl shadow-soft p-4">
                <div className="flex items-start gap-3 mb-3">
                  <div className="text-2xl">👤</div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-700 mb-2">Your Answer</p>
                    <textarea
                      value={userAnswer}
                      onChange={(e) => setUserAnswer(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          handleSendText(userAnswer);
                        }
                      }}
                      placeholder={isBrowserListening ? "Speak your answer... (it will appear here)" : "Type your answer or click the microphone to speak..."}
                      className="w-full min-h-[100px] p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-blue resize-none"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    {isBrowserListening && (
                      <span className="flex items-center gap-1">
                        <span className="inline-block w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                        Listening... speak your answer
                      </span>
                    )}
                    {!isBrowserListening && audioMode === 'browser' && (
                      <span>Click microphone to speak or type your answer</span>
                    )}
                    {audioMode === 'backend' && (
                      <span>Type your answer below</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleSendText(userAnswer)}
                    disabled={!userAnswer.trim() || isSubmitting}
                    className="px-6 py-2 bg-primary-blue text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Sending...
                      </>
                    ) : (
                      <>
                        Send
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-2 text-right">
                  Press Ctrl+Enter to send
                </p>
              </div>
            </div>
            
            <div className="text-gray-600">
              <p className="text-xs text-gray-500 mt-1">
                Mode: {audioMode === 'browser' ? 'Browser Speech' : 'Server Processing'}
              </p>
            </div>
          </div>
        )}
      </div>

      <VideoFeed stream={stream} />
      
      <ControlBar
        isMuted={!isListening}
        onToggleMute={handleToggleMute}
        onEndInterview={handleEndInterview}
      />
    </div>
  );
};
