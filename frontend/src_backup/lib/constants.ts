// API Configuration
const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  UPLOAD_RESUME: `${API_BASE_URL}/api/upload-resume`,
  SESSION: (id: string) => `${API_BASE_URL}/api/session/${id}`,
  REPORT: `${API_BASE_URL}/api/report`,
  START_INTERVIEW: `${API_BASE_URL}/api/start-interview`,
  CONFIG_OPTIONS: `${API_BASE_URL}/config/options`,
} as const;

export const WS_BASE_URL = 'ws://localhost:8000';

export const WS_ENDPOINTS = {
  INTERVIEW: (sessionId: string) => `${WS_BASE_URL}/ws/interview/${sessionId}`,
} as const;

// Application Constants
export const APP_NAME = 'Interview Mirror';
export const APP_VERSION = '1.0.0';

// MediaPipe Configuration
export const MEDIAPIPE_CONFIG = {
  FRAME_INTERVAL: 2000, // Send frame every 2 seconds
  MODEL_COMPLEXITY: 1,
  SMOOTH_LANDMARKS: true,
  MIN_DETECTION_CONFIDENCE: 0.5,
  MIN_TRACKING_CONFIDENCE: 0.5,
} as const;

// Audio Configuration
export const AUDIO_CONFIG = {
  SAMPLE_RATE: 16000,
  CHANNELS: 1,
  BITS_PER_SAMPLE: 16,
} as const;

// Interview Configuration
export const INTERVIEW_CONFIG = {
  MIN_DURATION: 60, // seconds
  MAX_DURATION: 3600, // seconds
  AUTO_SAVE_INTERVAL: 30000, // 30 seconds
} as const;
