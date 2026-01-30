import { create } from 'zustand';

export type DifficultyLevel = 'junior' | 'mid' | 'senior' | 'staff';
export type StatusHalo = 'blue' | 'amber' | 'red';
export type AudioMode = 'browser' | 'backend';

export interface Persona {
  id: string;
  name: string;
  company: string;
  icon: string;
  description: string;
}

export interface SessionState {
  sessionId: string | null;
  resumeFile: File | null;
  resumeText: string | null;
  selectedPersona: Persona | null;
  difficulty: DifficultyLevel;
  topics: string[];
  audioMode: AudioMode;
  isConnected: boolean;
  statusHalo: StatusHalo;
  currentFeedback: string | null;
  metrics: {
    posture: number;
    stress: number;
    eyeContact: number;
    wpm: number;
  };
  
  setSessionId: (id: string) => void;
  setResumeFile: (file: File | null) => void;
  setResumeText: (text: string | null) => void;
  setSelectedPersona: (persona: Persona) => void;
  setDifficulty: (level: DifficultyLevel) => void;
  toggleTopic: (topic: string) => void;
  setAudioMode: (mode: AudioMode) => void;
  setConnected: (connected: boolean) => void;
  setStatusHalo: (status: StatusHalo) => void;
  setCurrentFeedback: (feedback: string | null) => void;
  updateMetrics: (metrics: Partial<SessionState['metrics']>) => void;
  resetSession: () => void;
}

const initialState = {
  sessionId: null,
  resumeFile: null,
  resumeText: null,
  selectedPersona: null,
  difficulty: 'mid' as DifficultyLevel,
  topics: [],
  audioMode: 'backend' as AudioMode, // Default to backend for better browser compatibility
  isConnected: false,
  statusHalo: 'blue' as StatusHalo,
  currentFeedback: null,
  metrics: {
    posture: 0,
    stress: 0,
    eyeContact: 0,
    wpm: 0,
  },
};

export const useSessionStore = create<SessionState>((set) => ({
  ...initialState,
  
  setSessionId: (id) => set({ sessionId: id }),
  setResumeFile: (file) => set({ resumeFile: file }),
  setResumeText: (text) => set({ resumeText: text }),
  setSelectedPersona: (persona) => set({ selectedPersona: persona }),
  setDifficulty: (level) => set({ difficulty: level }),
  toggleTopic: (topic) => set((state) => ({
    topics: state.topics.includes(topic)
      ? state.topics.filter((t) => t !== topic)
      : [...state.topics, topic],
  })),
  setAudioMode: (mode) => set({ audioMode: mode }),
  setConnected: (connected) => set({ isConnected: connected }),
  setStatusHalo: (status) => set({ statusHalo: status }),
  setCurrentFeedback: (feedback) => set({ currentFeedback: feedback }),
  updateMetrics: (metrics) => set((state) => ({
    metrics: { ...state.metrics, ...metrics },
  })),
  resetSession: () => set(initialState),
}));
