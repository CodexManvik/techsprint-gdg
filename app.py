from dotenv import load_dotenv
import os
import json
import base64
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
    persona: str
    difficulty: str
    topic: str
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
async def check_session(session_id: str):
    """Verifies if a session ID is valid and active."""
    if session_id in sessions:
        return {"valid": True, "details": {
            "topic": sessions[session_id].topic,
            "persona": sessions[session_id].company_focus
        }}
    return {"valid": False}

@app.post("/start_interview")
async def start_interview_session(req: StartSessionRequest):
    session_id = str(uuid.uuid4())
    
    # Initialize Session
    sessions[session_id] = InterviewSession(
        session_id, 
        company_focus=req.persona, 
        difficulty=req.difficulty, 
        topic=req.topic
    )
    
    # Set TTS voice based on persona
    tts.set_persona(req.persona)
    
    # Initialize AI with specific context
    opening_question = ai.reset_session(
        style=req.persona, 
        difficulty=req.difficulty, 
        topic=req.topic,
        resume_context=req.resume_text
    )
    
    return {"session_id": session_id, "opening_question": opening_question}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() for page in reader.pages])
        return {"status": "success", "text": text[:5000]} # Limit text size
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/interview_report/{session_id}")
async def get_report(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    analytics = session.get_analytics()
    
    # Generate AI Feedback based on the full transcript
    ai_report = ai.generate_feedback_report(analytics["transcript_text"])
    
    return {
        "analytics": analytics,
        "ai_report": ai_report
    }

#
@app.websocket("/ws/interview/{session_id}")
async def interview_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # 1. Reconnect Logic
    if session_id not in sessions:
        sessions[session_id] = InterviewSession(session_id)
    
    current_session = sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # --- VISION LOGIC ---
            if payload.get("type") == "tracking":
                try:
                    metrics = vision.analyze_frame(payload['landmarks'])
                    current_session.log_vision_metrics(metrics)
                    await websocket.send_text(json.dumps({
                        "type": "metrics_update",
                        "metrics": metrics
                    }))
                except Exception as e:
                    # Ignore vision errors (don't crash the chat)
                    print(f"Vision Error: {e}")

            # --- AUDIO LOGIC ---
            elif payload.get("type") == "conversation":
                print("🎤 Receiving Audio...")
                
                try:
                    # 1. Process Audio
                    audio_data = base64.b64decode(payload['audio_data'])
                    print(f"   Audio data size: {len(audio_data)} bytes")
                    
                    analysis = audio_processor.process_audio(audio_data)
                    user_text = analysis['text']
                    
                    # Log if audio failed
                    if analysis.get('error'):
                        print(f"Audio Error: {analysis['error']}")

                    # IF SPEECH DETECTED
                    if user_text:
                        print(f"🗣️ User: {user_text}")
                        
                        # 2. Get AI Response
                        current_metrics = vision.analyze_frame(payload['landmarks']) if payload.get('landmarks') else {}
                        ai_reply = ai.get_response(user_text, current_metrics)
                        print(f"🤖 AI: {ai_reply}")
                        
                        # 3. Log Interaction
                        current_session.log_interaction(user_text, ai_reply)
                        
                        # 4. Generate Audio
                        print("🔊 Generating TTS audio...")
                        audio_b64 = tts.generate_audio(ai_reply)
                        
                        if audio_b64:
                            print(f"✅ Audio generated: {len(audio_b64)} characters (base64)")
                        else:
                            print("⚠️ Audio generation returned None")

                        await websocket.send_text(json.dumps({
                            "type": "ai_response",
                            "reply": ai_reply,
                            "transcript": user_text,
                            "audio": audio_b64  # Send the audio file
                        }))
                        print("📤 Response sent to frontend")

                    # ELSE: NO SPEECH DETECTED
                    else:
                        print("⚠️ No speech detected.")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "I didn't catch that. Could you speak up?"
                        }))

                except Exception as inner_e:
                    # Catch audio processing crashes
                    print(f"Processing Error: {inner_e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "System error processing audio."
                    }))
                    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"CRITICAL Error: {e}")