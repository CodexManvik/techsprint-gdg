import { useState, useRef, useCallback, useEffect } from 'react';

export const useAudio = () => {
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const animationFrame = useRef<number | undefined>(undefined);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      
      audioContext.current = new AudioContext();
      analyser.current = audioContext.current.createAnalyser();
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      analyser.current.fftSize = 256;

      const dataArray = new Uint8Array(analyser.current.frequencyBinCount);
      
      const updateLevel = () => {
        if (analyser.current && !isMuted) {
          analyser.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255);
        }
        animationFrame.current = requestAnimationFrame(updateLevel);
      };
      
      updateLevel();
      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  }, [isMuted]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
    if (animationFrame.current) {
      cancelAnimationFrame(animationFrame.current);
    }
    if (audioContext.current) {
      audioContext.current.close();
    }
  }, [isRecording]);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
    if (mediaRecorder.current?.stream) {
      mediaRecorder.current.stream.getAudioTracks().forEach(track => {
        track.enabled = isMuted;
      });
    }
  }, [isMuted]);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  return {
    isMuted,
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    toggleMute,
  };
};
