import { useEffect, useRef, useCallback, useState } from 'react';
import { useSessionStore } from '../stores/sessionStore';

interface WebSocketMessage {
  type: 'audio' | 'metrics' | 'feedback' | 'question' | 'summary' | 'ai_response' | 'interview_ended' | 'error';
  data?: any;
  reply?: string;
  audio?: string;
  message?: string;
}

export const useWebSocket = (baseUrl: string, enabled: boolean = true) => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { setConnected, setStatusHalo, setCurrentFeedback, updateMetrics, sessionId } = useSessionStore();
  const speechSynthesis = window.speechSynthesis;
  const [lastAiMessage, setLastAiMessage] = useState<string>('');

  const connect = useCallback(() => {
    if (!enabled) return;

    try {
      // Use session ID from store to connect to proper WebSocket endpoint
      const url = sessionId ? `${baseUrl}/interview/${sessionId}` : baseUrl;
      console.log('Connecting to WebSocket:', url);
      
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'ai_response':
              // Use browser TTS to speak the AI response
              if (message.reply) {
                console.log('🤖 AI:', message.reply);
                setLastAiMessage(message.reply);
                speakText(message.reply);
                
                // Dispatch custom event for Interview page to catch
                window.dispatchEvent(new CustomEvent('ai-message', { 
                  detail: { text: message.reply } 
                }));
              }
              break;
            case 'interview_ended':
              console.log('Interview ended by server');
              // Stop speech and disconnect
              speechSynthesis.cancel();
              if (ws.current) {
                ws.current.close();
              }
              break;
            case 'audio':
              // Fallback: play base64 audio if provided
              if (message.data) {
                playAudio(message.data);
              }
              break;
            case 'metrics':
              handleMetrics(message.data);
              break;
            case 'feedback':
              setCurrentFeedback(message.data?.message || message.data);
              setTimeout(() => setCurrentFeedback(null), 5000);
              break;
            case 'question':
              console.log('New question:', message.data);
              break;
            case 'summary':
              console.log('Interview summary:', message.data);
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [baseUrl, enabled, setConnected, setCurrentFeedback, sessionId]);

  const speakText = (text: string) => {
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.1; // Slightly higher pitch for more feminine sound
    utterance.volume = 1.0;
    
    // Load voices if not already loaded
    let voices = speechSynthesis.getVoices();
    if (voices.length === 0) {
      // Wait for voices to load
      speechSynthesis.onvoiceschanged = () => {
        voices = speechSynthesis.getVoices();
        selectVoice(voices, utterance);
        speechSynthesis.speak(utterance);
      };
    } else {
      selectVoice(voices, utterance);
      speechSynthesis.speak(utterance);
    }
  };

  const selectVoice = (voices: SpeechSynthesisVoice[], utterance: SpeechSynthesisUtterance) => {
    // Prefer female voices
    const femaleVoice = voices.find(voice => 
      (voice.name.includes('Female') || 
       voice.name.includes('Samantha') ||
       voice.name.includes('Victoria') ||
       voice.name.includes('Karen') ||
       voice.name.includes('Moira') ||
       voice.name.includes('Fiona') ||
       voice.name.includes('Google US English') && voice.name.includes('Female')) &&
      voice.lang.startsWith('en')
    );

    // Fallback to any English female voice
    const anyFemaleVoice = voices.find(voice => 
      voice.lang.startsWith('en') && 
      (voice.name.toLowerCase().includes('female') || 
       voice.name.toLowerCase().includes('woman'))
    );

    // Use Microsoft Zira (Windows) or Google Female voices
    const preferredVoice = voices.find(voice =>
      (voice.name.includes('Zira') || 
       voice.name.includes('Google UK English Female') ||
       voice.name.includes('Microsoft Zira')) &&
      voice.lang.startsWith('en')
    );

    if (preferredVoice) {
      utterance.voice = preferredVoice;
      console.log('Using voice:', preferredVoice.name);
    } else if (femaleVoice) {
      utterance.voice = femaleVoice;
      console.log('Using voice:', femaleVoice.name);
    } else if (anyFemaleVoice) {
      utterance.voice = anyFemaleVoice;
      console.log('Using voice:', anyFemaleVoice.name);
    } else {
      // Fallback to any English voice
      const englishVoice = voices.find(voice => voice.lang.startsWith('en'));
      if (englishVoice) {
        utterance.voice = englishVoice;
        console.log('Using fallback voice:', englishVoice.name);
      }
    }
  };

  const handleMetrics = (data: any) => {
    updateMetrics({
      posture: data.posture || 0,
      stress: data.stress || 0,
      eyeContact: data.eye_contact || 0,
      wpm: data.wpm || 0,
    });

    if (data.stress > 0.7) {
      setStatusHalo('red');
    } else if (data.posture < 0.5 || data.eye_contact < 0.5) {
      setStatusHalo('amber');
    } else {
      setStatusHalo('blue');
    }
  };

  const playAudio = async (audioData: string) => {
    try {
      const audioContext = new AudioContext();
      const audioBuffer = await audioContext.decodeAudioData(
        Uint8Array.from(atob(audioData), c => c.charCodeAt(0)).buffer
      );
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start(0);
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };

  const sendMessage = useCallback((message: any) => {
    console.log('WebSocket sendMessage called');
    console.log('WebSocket state:', ws.current?.readyState);
    console.log('Message:', message);
    
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('✅ Sending message via WebSocket');
      ws.current.send(JSON.stringify(message));
    } else {
      console.error('❌ WebSocket not open. State:', ws.current?.readyState);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    // Stop any ongoing speech
    speechSynthesis.cancel();
  }, [speechSynthesis]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { sendMessage, disconnect, lastAiMessage };
};
