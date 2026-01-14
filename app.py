from dotenv import load_dotenv
import os
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from engine.vision_engine import VisionEngine 
from engine.ai_engine import AIEngine
from engine.audio_engine import AudioEngine
from engine.session_manager import InterviewSession 
from pypdf import PdfReader
import io
import uuid

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL INSTANCES ---
vision = VisionEngine() 
ai = AIEngine()
audio_processor = AudioEngine()
sessions = {}

@app.get("/")
async def root():
    return {"status": "Online", "version": "2.0-Live"}

@app.post("/start_interview")
async def start_interview_session():
    """Creates a new session ID and resets AI memory."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = InterviewSession(session_id)
    
    # Reset AI memory for the new candidate
    ai.reset_session()
    
    print(f"✅ Created Session: {session_id}")
    return {"session_id": session_id}

@app.get("/interview_report/{session_id}")
async def get_report(session_id: str):
    if session_id not in sessions:
        return {"error": "Session not found"}
    return sessions[session_id].get_report_card()

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        intro_question = ai.load_resume(text)
        return {"status": "success", "intro": intro_question}
    except Exception as e:
        print(f"Resume Error: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/interview/{session_id}")
async def interview_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"🔌 WebSocket Connected: {session_id}")
    
    if session_id not in sessions:
        sessions[session_id] = InterviewSession(session_id)
    
    current_session = sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # --- VISION LOGIC ---
            if payload.get("type") == "tracking":
                metrics = vision.analyze_frame(payload['landmarks'])
                current_session.log_vision_metrics(metrics)
                
                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    "metrics": metrics
                }))

            # --- AUDIO LOGIC ---
            elif payload.get("type") == "conversation":
                print("🎤 Receiving Audio...")
                # 1. Process Audio
                audio_data = base64.b64decode(payload['audio_data'])
                analysis = audio_processor.process_audio(audio_data)
                user_text = analysis['text']
                
                # IF SPEECH DETECTED
                if user_text:
                    print(f"🗣️ User: {user_text}")
                    # 2. Get AI Response
                    current_metrics = vision.analyze_frame(payload['landmarks']) if payload.get('landmarks') else {}
                    ai_reply = ai.get_response(user_text, current_metrics)
                    
                    # 3. Log Interaction
                    current_session.log_interaction(user_text, ai_reply)
                    
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "reply": ai_reply,
                        "transcript": user_text
                    }))
                
                # ELSE: NO SPEECH DETECTED (Fix for "Stuck" issue)
                else:
                    print("⚠️ No speech detected.")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "I didn't catch that. Could you speak up?"
                    }))
                    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"Error: {e}")