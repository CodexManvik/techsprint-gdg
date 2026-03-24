# Backend Refactor Notes (v3)

## Summary
This refactor hardens the backend for production-grade local-LLM interview sessions while preserving existing route contracts.

## Behavior Changes

### 1) WebSocket auth is now enforced by default
- Endpoint: `/ws/interview/{session_id}`
- Token sources supported:
  - Query param: `?token=<jwt>`
  - Header: `Authorization: Bearer <jwt>`
- Authorization checks now verify session ownership before websocket processing.

If websocket auth needs temporary local bypass, set:

```env
WS_AUTH_REQUIRED=false
```

### 2) New health endpoint
- Endpoint: `/health`
- Returns:
  - app status/env/version
  - database connectivity
  - redis enabled/connected state
  - llm provider + health
  - circuit breaker state and counters
  - lightweight in-process telemetry counters

No secrets are returned by this endpoint.

### 3) LLM response shaping
- Interview engine now requests strict JSON fields from LLM:
  - `acknowledgement`
  - `feedback_short`
  - `next_question`
- Includes one repair attempt if JSON parsing fails.
- Final response returned to clients remains plain text (concise and professional).

### 4) Context and generation controls
New environment variables:

```env
MAX_CONTEXT_MESSAGES=8
LLM_TEMPERATURE=0.5
LLM_TOP_P=0.9
LLM_MAX_NEW_TOKENS=128
LLM_JSON_MODE=true
WS_AUTH_REQUIRED=true
```

## Manual Test Checklist

1. Start backend:
   - `python -m uvicorn backend.main:app --reload`
2. Start interview via existing HTTP route and verify `session_id` returned.
3. Connect websocket with valid JWT and same `session_id`:
   - Expect connection accepted and normal processing.
4. Connect websocket without token:
   - Expect structured error payload and close (`type="error"`, `code="unauthorized"`).
5. Send conversation payload with audio base64:
   - Expect AI response, transcript, and optional TTS audio.
6. Retrieve history/report using existing session routes:
   - Expect ownership-enforced responses.
7. Hit `/health`:
   - Verify diagnostics fields (`db`, `redis`, `llm`, `circuit_breaker`).
