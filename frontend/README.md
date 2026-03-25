# Frontend - Interview Studio

A standalone frontend for the backend interview APIs.

## Features

- Register + login flow
- Manual token paste support
- Interview setup with:
  - Persona
  - Difficulty
  - Topic
  - Multiple job description presets
  - Custom JD textarea
  - Resume PDF upload and extraction
- Interview room with:
  - Live camera preview
  - Robot interviewer visual with talking state
  - Audio recording and websocket conversation submission
  - Synthetic tracking stream for metrics/integrity pipeline testing
- Scorer panel with report summary and metric bars
- Sessions panel to load existing sessions and pick one for report retrieval
- Performance Lab:
  - Health check timing
  - API latency timings (config, login, register, start interview, report, history)
  - Turn roundtrip latency (audio send -> ai_response)
  - P95 and average turn latency
  - Export performance events as JSON

## Run

Use any static server from this folder.

Option 1 (Python):

python -m http.server 5173

Then open:

http://localhost:5173

## Suggested End-to-End Perf Workflow

1. Register and login.
2. Upload resume PDF.
3. Choose preset JD or paste custom JD.
4. Start interview.
5. Connect websocket.
6. Start camera and metrics stream.
7. Record multiple turns.
8. Refresh report after 3-5 turns.
9. Open Performance Lab and export JSON.

## Backend assumptions

- Backend API running at http://localhost:8000
- Websocket auth supports token query parameter
- User is authenticated with JWT token
