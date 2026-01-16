export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const WS_URL = `${WS_BASE_URL}/ws`;

export const API_ENDPOINTS = {
  BASE: API_BASE_URL,
  UPLOAD_RESUME: `${API_BASE_URL}/upload-resume`,
  PERSONAS: `${API_BASE_URL}/personas`,
  DIFFICULTIES: `${API_BASE_URL}/difficulties`,
  TOPICS: `${API_BASE_URL}/topics`,
  START_SESSION: `${API_BASE_URL}/start_session`,
  REPORT: `${API_BASE_URL}/api/report`,
  WEBSOCKET: WS_URL,
};

export const WEBSOCKET_EVENTS = {
  START_SESSION: 'start_session',
  VIDEO_FRAME: 'video_frame',
  AUDIO_CHUNK: 'audio_chunk',
  END_SESSION: 'end_session',
  SESSION_STARTED: 'session_started',
  VISION_ANALYSIS: 'vision_analysis',
  AI_RESPONSE: 'ai_response',
  ERROR: 'error',
};
