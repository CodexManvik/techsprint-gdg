import { useState, useEffect, useRef, useCallback } from 'react';

// Extend Window interface for webkit prefix
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  isSupported: boolean;
  error: string | null;
  finalTranscript: string;
}

export const useSpeechRecognition = (): UseSpeechRecognitionReturn => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const isStoppedManually = useRef(false);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSpeechTimeRef = useRef<number>(Date.now());

  // Check if browser supports Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const isSupported = !!SpeechRecognition;

  useEffect(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    // Initialize Speech Recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('Speech recognition started');
      setIsListening(true);
      setError(null);
      isStoppedManually.current = false;
      lastSpeechTimeRef.current = Date.now();
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let newFinalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          newFinalTranscript += transcriptPiece + ' ';
        } else {
          interimTranscript += transcriptPiece;
        }
      }

      // Update transcript with interim results for display
      if (interimTranscript) {
        setTranscript(prev => {
          const base = prev.split('[interim]')[0];
          return base + '[interim] ' + interimTranscript;
        });
      }

      // Update final transcript when we get final results
      if (newFinalTranscript) {
        setFinalTranscript(prev => prev + newFinalTranscript);
        setTranscript(prev => {
          const base = prev.split('[interim]')[0];
          return base + newFinalTranscript;
        });
        lastSpeechTimeRef.current = Date.now();
        
        // Clear any existing silence timer
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }
        
        // Start a new silence timer (2 seconds of silence = done speaking)
        silenceTimerRef.current = setTimeout(() => {
          const timeSinceLastSpeech = Date.now() - lastSpeechTimeRef.current;
          const currentFinal = finalTranscript + newFinalTranscript;
          if (timeSinceLastSpeech >= 2000 && currentFinal.trim()) {
            console.log('Detected end of speech, submitting transcript');
            // Trigger submission by setting a special flag
            setFinalTranscript(currentFinal + '[SUBMIT]');
          }
        }, 2000);
      }
    };

    recognition.onerror = (event: any) => {
      // Ignore aborted errors (happens when manually stopped)
      if (event.error === 'aborted' && isStoppedManually.current) {
        return;
      }
      
      // Ignore no-speech errors - they're normal when user pauses
      if (event.error === 'no-speech') {
        // Don't log or show error - this is expected behavior
        return;
      }
      
      console.error('Speech recognition error:', event.error);
      
      switch (event.error) {
        case 'audio-capture':
          setError('Microphone not accessible. Please check permissions.');
          setIsListening(false);
          break;
        case 'not-allowed':
          setError('Microphone permission denied. Please allow microphone access.');
          setIsListening(false);
          break;
        case 'network':
          setError('Network error. Please check your connection.');
          break;
        default:
          console.warn(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      console.log('Speech recognition ended');
      setIsListening(false);
      
      // Clear silence timer
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      
      // Auto-restart if not stopped manually and no critical error
      if (!isStoppedManually.current && !error) {
        setTimeout(() => {
          try {
            if (recognitionRef.current && !isStoppedManually.current) {
              recognitionRef.current.start();
            }
          } catch (e) {
            console.log('Could not restart recognition:', e);
          }
        }, 100); // Small delay to prevent rapid restart loops
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      if (recognitionRef.current) {
        isStoppedManually.current = true;
        recognitionRef.current.stop();
      }
    };
  }, [isSupported, error, finalTranscript]);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition not supported');
      return;
    }

    if (recognitionRef.current) {
      // Stop first if already running
      if (isListening) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          console.log('Recognition already stopped');
        }
      }
      
      // Start after a small delay
      setTimeout(() => {
        try {
          isStoppedManually.current = false;
          recognitionRef.current.start();
        } catch (error: any) {
          // Ignore if already started
          if (error.message && error.message.includes('already started')) {
            console.log('Recognition already running');
          } else {
            console.error('Failed to start recognition:', error);
            setError('Failed to start speech recognition');
          }
        }
      }, 100);
    }
  }, [isSupported, isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      isStoppedManually.current = true;
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      recognitionRef.current.stop();
    }
  }, [isListening]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setFinalTranscript('');
    setError(null);
  }, []);

  return {
    isListening,
    transcript,
    finalTranscript,
    startListening,
    stopListening,
    resetTranscript,
    isSupported,
    error,
  };
};
