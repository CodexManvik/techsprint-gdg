# Running the New Backend

## Quick Start

```powershell
# Option 1: Run new backend directly
python -m uvicorn backend.main:app --reload --port 8000

# Option 2: Run old app.py (still works)
uvicorn app:app --reload --port 8000
```

## What Works With New Backend

### ✅ Fully Migrated Endpoints
- `POST /api/start-interview` - **USES NEW InterviewEngine with Ollama/Circuit Breaker**

### ⚙️ Legacy Compatibility (Temporarily kept)
- `GET /config/options`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /api/history`

### 🚧 TODO: Need Migration
- `POST /upload-resume`
- `GET /api/report`
- `POST /check_session/{session_id}`
- `GET /api/session/{session_id}/messages`
- `WS /ws/interview/{session_id}` - **High Priority**

## Testing the NEW Backend

```powershell
# Start Ollama first
ollama serve

# Start backend
python -m uvicorn backend.main:app --reload

# Test endpoint (requires authentication)
curl http://localhost:8000/
```

Expected response:
```json
{
  "status": "Online",
  "version": "4.0-Refactored",
  "llm_provider": "ollama",
  "llm_model": "phi3.5:latest"
}
```
