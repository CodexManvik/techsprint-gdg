# Backend Migration Checklist

## ✅ Completed Migrations

### Routes Migrated to `backend/api/routes/`
- ✅ **Authentication** (`auth.py`)
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`

- ✅ **Sessions** (`sessions.py`)
  - `GET /api/config/options`
  - `POST /api/start-interview` (uses InterviewEngine)
  - `POST /api/upload-resume`
  - `GET /api/history`
  - `POST /api/check_session/{session_id}`
  - `GET /api/session/{session_id}/messages`
  - `GET /api/report`

- ✅ **WebSocket** (`websocket.py`)
  - `WS /ws/interview/{session_id}` (uses InterviewEngine)

### Core Components
- ✅ `backend/core/llm/ollama.py` - Ollama client
- ✅ `backend/core/llm/circuit_breaker.py` - Fault tolerance
- ✅ `backend/core/interview/engine.py` - Interview orchestration
- ✅ `backend/core/interview/analyzer.py` - Cheating detection
- ✅ `backend/core/cache.py` - Redis session manager
- ✅ `backend/config/settings.py` - Configuration

## 🚧 Partially Complete

### WebSocket Improvements Needed
- [ ] Add elapsed time tracking for cheating detector
- [ ] Implement session cleanup on disconnect
- [ ] Add WebSocket authentication middleware

### Database Migration
- [ ] Convert `database.py` to async (aiosqlite)
- [ ] Move to `backend/db/repository.py`
- [ ] Add connection pooling

## ❌ Not Started

### Testing
- [ ] Unit tests for core services
- [ ] Integration tests for API endpoints
- [ ] WebSocket testing
- [ ] Load testing

### Documentation
- [ ] API documentation (auto-generated from OpenAPI)
- [ ] Developer setup guide
- [ ] Deployment guide

## 📝 Old Code to Remove (After Verification)

Once new backend is fully tested:
- [ ] Delete `app.py` (old monolithic backend)
- [ ] Consolidate `engine/` modules into `backend/core/`
- [ ] Remove in-memory session fallback

## 🎯 Ready to Test

All routes are now in `backend/main.py` via routers.

**Test command:**
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```
