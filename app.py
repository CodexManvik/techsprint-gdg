from dotenv import load_dotenv
import os
import json
import base64
import numpy as np
import cv2
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.vision_engine import VisionEngine 
from engine.ai_engine import AIEngine
from engine.audio_engine import AudioEngine
from engine.session_manager import InterviewSession 
from engine.personas import get_persona_list
from engine.difficulty import get_difficulty_list, get_topics_list
from pypdf import PdfReader
import io
import uuid
from engine.tts_engine import TTSEngine

load_dotenv()
app = FastAPI()
tts = TTSEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instances
vision = VisionEngine() 
ai = AIEngine()
audio_processor = AudioEngine()
sessions = {}
if os.path.exists("google_credentials.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("google_credentials.json")
    print("✅ Loaded Google Cloud Credentials from file")
else:
    print("⚠️  Warning: google_credentials.json not found")

# --- Pydantic Models ---
class StartSessionRequest(BaseModel):
    session_id: str = None  # Optional: frontend can provide session_id
    persona: str
    difficulty: str
    topic: str
    resume_text: str = None
    resume_text: str = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "Online", "version": "3.0-StateOfTheArt"}

@app.get("/config/options")
async def get_config_options():
    """Returns available personas, difficulties, and topics for frontend"""
    return {
        "personas": get_persona_list(),
        "difficulties": get_difficulty_list(),
        "topics": get_topics_list()
    }

@app.post("/check_session/{session_id}")
@app.get("/api/session/{session_id}")
async def check_session(session_id: str):
    """Verifies if a session ID is valid and active."""
    if session_id in sessions:
        return {"valid": True, "details": {
            "topic": sessions[session_id].topic,
            "persona": sessions[session_id].company_focus
        }}
    return {"valid": False}

@app.post("/start_interview")
@app.post("/api/start-interview")
async def start_interview_session(req: StartSessionRequest = None):
    """Start a new interview session with optional parameters."""
    # Use provided session_id or generate new one
    session_id = req.session_id if req and req.session_id else str(uuid.uuid4())
    
    # Use defaults if no request body provided
    persona = req.persona if req else "FAANG_Architect"
    difficulty = req.difficulty if req else "Intermediate"
    topic = req.topic if req else "System Design"
    resume_text = req.resume_text if req else None
    
    print(f"🚀 Starting interview session:")
    print(f"   - Session ID: {session_id}")
    print(f"   - Persona: {persona}")
    print(f"   - Difficulty: {difficulty}")
    print(f"   - Topic: {topic}")
    
    # Initialize Session (or reuse existing)
    if session_id not in sessions:
        sessions[session_id] = InterviewSession(
            session_id, 
            company_focus=persona, 
            difficulty=difficulty, 
            topic=topic
        )
    
    # Set TTS voice based on persona
    tts.set_persona(persona)
    
    # Initialize AI with specific context
    opening_question = ai.reset_session(
        style=persona, 
        difficulty=difficulty, 
        topic=topic,
        resume_context=resume_text
    )
    
    print(f"✅ Session initialized with opening question: {opening_question[:100]}...")
    
    return {"session_id": session_id, "opening_question": opening_question}

@app.post("/upload-resume")
@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() for page in reader.pages])
        return {"status": "success", "text": text[:5000]} # Limit text size
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/interview_report/{session_id}")
@app.get("/api/report")
async def get_report(session_id: str = None):
    # If no session_id provided, return mock data for testing
    if not session_id or session_id not in sessions:
        return {
            "summary": "Mock interview report. Start an interview to see real data.",
            "radarData": [
                {"category": "Technical", "user": 75, "ideal": 85},
                {"category": "Communication", "user": 70, "ideal": 80},
                {"category": "Confidence", "user": 65, "ideal": 85},
                {"category": "Body Language", "user": 60, "ideal": 80},
                {"category": "Problem Solving", "user": 80, "ideal": 90}
            ],
            "metrics": [
                {"label": "Words Per Minute", "value": 0, "unit": "WPM", "status": "moderate", "description": "No data yet"},
                {"label": "Stress Level", "value": 0, "unit": "%", "status": "good", "description": "No data yet"},
                {"label": "Eye Contact", "value": 0, "unit": "%", "status": "moderate", "description": "No data yet"},
                {"label": "Posture Score", "value": 0, "unit": "%", "status": "moderate", "description": "No data yet"}
            ],
            "integrityEvents": [],
            "totalDuration": 0
        }
        
    session = sessions[session_id]
    analytics = session.get_analytics()
    
    # Generate AI Feedback based on the full transcript
    ai_report = ai.generate_feedback_report(analytics["transcript_text"])
    
    return {
        "analytics": analytics,
        "ai_report": ai_report
    }

#
@app.websocket("/ws")
@app.websocket("/ws/interview/{session_id}")
async def interview_endpoint(websocket: WebSocket, session_id: str = None):
    await websocket.accept()
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 1. Reconnect Logic
    if session_id not in sessions:
        # Create session but DON'T initialize AI yet
        # The start-interview endpoint will initialize it with proper settings
        sessions[session_id] = InterviewSession(session_id)
        print(f"📝 Created new session: {session_id} (waiting for initialization)")
    else:
        print(f"🔄 Reconnecting to existing session: {session_id}")
    
    current_session = sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # --- VISION LOGIC ---
            if payload.get("type") == "tracking":
                try:
                    # NEW: Check if we have a base64 frame from frontend
                    if payload.get('frame_data'):
                        print("📸 Received frame from frontend, processing with MediaPipe...")
                        
                        # Decode base64 frame
                        frame_data = payload['frame_data']
                        # Remove data URL prefix if present
                        if ',' in frame_data:
                            frame_data = frame_data.split(',')[1]
                        
                        # Decode base64 to bytes
                        frame_bytes = base64.b64decode(frame_data)
                        
                        # Convert to numpy array (OpenCV format)
                        nparr = np.frombuffer(frame_bytes, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Process frame with full MediaPipe holistic analysis
                            metrics = vision.analyze_frame(frame)
                            print(f"✅ Vision metrics: eye_contact={metrics.get('eye_contact_score', 0):.2f}, stress={metrics.get('is_stressed', False)}")
                        else:
                            print("⚠️ Failed to decode frame")
                            metrics = vision.analyze_frame({})  # Use defaults
                    
                    # Check if we have pre-computed posture metrics from frontend
                    elif payload.get('posture_metrics'):
                        # Frontend computed posture - just add legacy face analysis
                        posture_metrics = payload['posture_metrics']
                        
                        # Legacy face analysis
                        legacy_metrics = {}
                        if payload.get('landmarks'):
                            legacy_metrics = vision._analyze_legacy(payload['landmarks'])
                        
                        # Combine metrics
                        metrics = {
                            # Legacy metrics
                            "eye_contact_score": legacy_metrics.get("eye_contact_score", 0.5),
                            "fidget_score": legacy_metrics.get("fidget_score", 0.0),
                            "head_gesture": legacy_metrics.get("head_gesture", "neutral"),
                            "is_smiling": legacy_metrics.get("is_smiling", False),
                            "is_stressed": legacy_metrics.get("is_stressed", False),
                            "stress_detected": legacy_metrics.get("stress_detected", False),
                            
                            # Your posture metrics (from frontend)
                            "posture": posture_metrics,
                            
                            # Meta
                            "mode": "frontend_pose",
                            "timestamp": posture_metrics.get("timestamp", time.time())
                        }
                    else:
                        # Fallback to backend processing with empty landmarks
                        metrics = vision.analyze_frame(payload.get('landmarks', {}))
                    
                    current_session.log_vision_metrics(metrics)
                    await websocket.send_text(json.dumps({
                        "type": "metrics_update",
                        "metrics": metrics
                    }))
                except Exception as e:
                    print(f"Vision Error: {e}")
                    import traceback
                    traceback.print_exc()

            # --- CONVERSATION LOGIC (supports both text and audio) ---
            elif payload.get("type") == "conversation":
                mode = payload.get("mode", "browser")  # browser, backend, or text
                print(f"💬 Receiving message (mode: {mode})...")
                
                try:
                    user_text = None
                    
                    # MODE 1: Browser speech (text already transcribed)
                    if mode == "browser" or mode == "text":
                        user_text = payload.get('text', '').strip()
                        if user_text:
                            print(f"🗣️ User (browser): {user_text}")
                    
                    # MODE 2: Backend audio processing
                    elif mode == "backend":
                        audio_data = base64.b64decode(payload.get('audio_data', ''))
                        if audio_data:
                            print(f"🎤 Processing audio: {len(audio_data)} bytes")
                            analysis = audio_processor.process_audio(audio_data)
                            user_text = analysis.get('text', '').strip()
                            
                            if analysis.get('error'):
                                print(f"Audio Error: {analysis['error']}")
                            
                            if user_text:
                                print(f"🗣️ User (backend): {user_text}")
                    
                    # Process if we have text
                    if user_text:
                        # Calculate WPM (Words Per Minute)
                        word_count = len(user_text.split())
                        # Estimate speaking time (rough: 1 word = 0.4 seconds at normal pace)
                        estimated_duration_seconds = word_count * 0.4
                        wpm = (word_count / estimated_duration_seconds * 60) if estimated_duration_seconds > 0 else 0
                        
                        # Log audio metrics (WPM)
                        current_session.log_audio_metrics({"wpm": wpm})
                        
                        # Get AI Response
                        current_metrics = payload.get('landmarks', {})
                        ai_reply = ai.get_response(user_text, current_metrics)
                        print(f"🤖 AI: {ai_reply}")
                        
                        # Log Interaction
                        current_session.log_interaction(user_text, ai_reply)
                        
                        # Generate TTS audio for backend mode
                        audio_b64 = None
                        if mode == "backend":
                            print("🔊 Generating TTS audio...")
                            audio_b64 = tts.generate_audio(ai_reply)
                            if audio_b64:
                                print(f"✅ Audio generated: {len(audio_b64)} characters")
                        
                        # Send response
                        response = {
                            "type": "ai_response",
                            "reply": ai_reply,
                            "transcript": user_text
                        }
                        
                        if audio_b64:
                            response["audio"] = audio_b64
                        
                        await websocket.send_text(json.dumps(response))
                        print("📤 Response sent to frontend")
                    else:
                        print("⚠️ No text detected.")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "No speech detected. Please try again."
                        }))

                except Exception as inner_e:
                    print(f"Processing Error: {inner_e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "System error processing message."
                    }))
            
            # --- END INTERVIEW ---
            elif payload.get("type") == "end_interview":
                print(f"🛑 Ending interview for session {session_id}")
                await websocket.send_text(json.dumps({
                    "type": "interview_ended",
                    "session_id": session_id
                }))
                break  # Exit the loop to close WebSocket
                    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"CRITICAL Error: {e}")