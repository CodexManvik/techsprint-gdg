# Interview Mirror (MUJ TechSprint)

AI-powered interview practice platform with real-time conversation, webcam behavior feedback, audio transcription, and session reporting.

## Overview

This repository contains:

- Backend: FastAPI app in [backend/main.py](backend/main.py)
- Frontend: static/Vite-style app in [frontend/index.html](frontend/index.html) and [frontend/app.js](frontend/app.js)
- Legacy compatibility engines in [engine](engine)

The backend runtime is centered on:

- Interview orchestration: [backend/core/interview/engine.py](backend/core/interview/engine.py)
- Turn scoring worker: [backend/core/interview/scorer.py](backend/core/interview/scorer.py)
- Redis session cache: [backend/core/cache.py](backend/core/cache.py)
- SQLite repository: [backend/db/repository.py](backend/db/repository.py)
- Auth/session routes: [backend/api/routes/auth.py](backend/api/routes/auth.py), [backend/api/routes/sessions.py](backend/api/routes/sessions.py), [backend/api/routes/websocket.py](backend/api/routes/websocket.py)

## Actual Architecture

### Request paths

- REST API requests go through route modules under [backend/api/routes](backend/api/routes)
- Realtime interview exchange uses WebSocket at [backend/api/routes/websocket.py](backend/api/routes/websocket.py)
- Business logic and model calls are orchestrated by [backend/core/interview/engine.py](backend/core/interview/engine.py)

### LLM layer

- Active provider: Ollama via [backend/core/llm/ollama.py](backend/core/llm/ollama.py)
- Circuit breaker: [backend/core/llm/circuit_breaker.py](backend/core/llm/circuit_breaker.py)
- No Google Cloud Speech/Text-to-Speech integration in the current backend runtime

### Audio and vision

- STT: local SpeechRecognition in [engine/audio_engine.py](engine/audio_engine.py)
- Vision metrics: [engine/vision_engine.py](engine/vision_engine.py)
- TTS generation: [engine/tts_engine.py](engine/tts_engine.py)

### Persistence

- Durable data: SQLite tables managed in [backend/db/repository.py](backend/db/repository.py)
- Cache and reconnect support: Redis in [backend/core/cache.py](backend/core/cache.py)
- Shared in-memory session maps: [backend/core/session_store.py](backend/core/session_store.py)

## API Endpoints (Current)

Base app and health:

- GET /
- GET /health

Authentication routes from [backend/api/routes/auth.py](backend/api/routes/auth.py):

- POST /auth/register
- POST /auth/login
- GET /auth/me

Session routes from [backend/api/routes/sessions.py](backend/api/routes/sessions.py):

- GET /api/config/options
- POST /api/start-interview
- POST /api/upload-resume
- GET /api/history
- GET /api/check_session/{session_id}
- GET /api/session/{session_id}/messages
- GET /api/report?session_id={session_id}

WebSocket route from [backend/api/routes/websocket.py](backend/api/routes/websocket.py):

- WS /ws/interview/{session_id}

Not implemented as REST in current code:

- POST /api/answer/{session_id}

## WebSocket Protocol (Current)

### Client -> server message types

- tracking
  - payload: landmarks
  - result: metrics updates and alerts
- conversation
  - payload: audio_data (base64), optional landmarks
  - result: ai_response with reply, transcript, and generated audio
- ping (optional)
  - server responds with pong
- pong
  - heartbeat acknowledgement

### Server -> client message types

- connected
- metrics_update
- ai_response
- error
- ping (heartbeat keepalive)
- pong

### Heartbeat behavior

Configured in [backend/config/settings.py](backend/config/settings.py):

- WS_HEARTBEAT_INTERVAL_SEC
- WS_HEARTBEAT_TIMEOUT_SEC

Behavior in [backend/api/routes/websocket.py](backend/api/routes/websocket.py):

- If no inbound frame arrives within interval, server sends ping
- If client stays idle beyond timeout, server sends heartbeat_timeout error and closes socket

## Environment Variables

Key settings are defined in [backend/config/settings.py](backend/config/settings.py).

Common variables:

- ENV
- DEBUG
- CORS_ORIGINS
- DB_PATH
- REDIS_ENABLED
- REDIS_URL
- REDIS_TTL
- JWT_SECRET
- JWT_ALGORITHM
- JWT_EXPIRE_MINUTES
- WS_AUTH_REQUIRED
- MAX_USER_INPUT_CHARS
- WS_HEARTBEAT_INTERVAL_SEC
- WS_HEARTBEAT_TIMEOUT_SEC
- AUTH_RATE_LIMIT_WINDOW_SEC
- AUTH_LOGIN_RATE_LIMIT
- AUTH_REGISTER_RATE_LIMIT
- OLLAMA_BASE_URL
- OLLAMA_MODEL

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

4. Open docs:

- http://localhost:8000/docs

## Notes for Contributors

- The runtime backend entrypoint is [backend/main.py](backend/main.py).
- Realtime interview answers are processed over WebSocket, not REST answer endpoints.
- Redis is optional; if unavailable, backend falls back to DB and in-memory structures.