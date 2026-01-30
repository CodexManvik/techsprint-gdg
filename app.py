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
from database import Database
db = Database()
from engine.auth import AuthEngine, Token, TokenData, oauth2_scheme
auth_engine = AuthEngine()
from fastapi import Depends, status 
from fastapi.security import OAuth2PasswordRequestForm

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
<<<<<<< Updated upstream
=======
    custom_instructions: str = None

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str
    resume_text: str = None
>>>>>>> Stashed changes

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

@app.post("/auth/register")
async def register(user: UserRegister):
    # Check if user exists
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash pwd
    hashed_pwd = auth_engine.get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    if db.create_user(user_id, user.email, hashed_pwd, user.full_name):
        return {"message": "User created successfully", "user_id": user_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user")

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user_by_email(form_data.username)
    if not user or not auth_engine.verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_engine.create_access_token(
        data={"sub": user['id'], "email": user['email']}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(auth_engine.get_current_user)):
    return current_user

@app.get("/api/history")
async def get_history(current_user: TokenData = Depends(auth_engine.get_current_user)):
    return db.get_user_sessions(current_user.user_id)

@app.post("/check_session/{session_id}")
async def check_session(session_id: str):
    """Verifies if a session ID is valid and active."""
    if session_id in sessions:
        return {"valid": True, "details": {
            "topic": sessions[session_id].topic,
            "persona": sessions[session_id].company_focus
        }}
    # Check DB
    session = db.get_session(session_id)
    if session:
        return {"valid": True, "details": {
            "topic": session['topic'],
            "persona": session['persona']
        }}
    return {"valid": False}

@app.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: TokenData = Depends(auth_engine.get_current_user)):
    """Retrieve chat history for a session."""
    # Verify session belongs to user (optional, but good practice)
    # session = db.get_session(session_id)
    # if not session or session['user_id'] != current_user.user_id:
    #     raise HTTPException(403, "Access denied")
    
    messages = db.get_messages(session_id)
    return messages

@app.post("/start_interview")
<<<<<<< Updated upstream
async def start_interview_session(req: StartSessionRequest):
    session_id = str(uuid.uuid4())
    
    # Initialize Session
    sessions[session_id] = InterviewSession(
        session_id, 
        company_focus=req.persona, 
        difficulty=req.difficulty, 
        topic=req.topic
    )
=======
@app.post("/api/start-interview")
async def start_interview_session(req: StartSessionRequest = None, current_user: TokenData = Depends(auth_engine.get_current_user)):
    """Start a new interview session with optional parameters."""
    # Use provided session_id or generate new one
    session_id = req.session_id if req and req.session_id else str(uuid.uuid4())
    
    # Use defaults if no request body provided
    persona = req.persona if req else "FAANG_Architect"
    difficulty = req.difficulty if req else "Intermediate"
    topic = req.topic if req else "System Design"
    resume_text = req.resume_text if req else None
    custom_instructions = req.custom_instructions if req else None
    
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
        # DB: Create session
        db.create_session(session_id, current_user.user_id, persona, topic, difficulty)
>>>>>>> Stashed changes
    
    # Set TTS voice based on persona
    tts.set_persona(req.persona)
    
    # Initialize AI with specific context
    opening_question = ai.reset_session(
<<<<<<< Updated upstream
        style=req.persona, 
        difficulty=req.difficulty, 
        topic=req.topic,
        resume_context=req.resume_text
=======
        style=persona, 
        difficulty=difficulty, 
        topic=topic,
        resume_context=resume_text,
        custom_instructions=custom_instructions
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
async def get_report(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
=======
@app.get("/api/report")
async def get_report(session_id: str = None):
    print(f"📊 Report requested for session: {session_id}")
    
    # If no session_id provided, return mock data for testing
    if not session_id:
        print(f"⚠️ Session ID missing, returning mock data")
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
>>>>>>> Stashed changes
        
    # Fetch Session & Analytics
    session = sessions.get(session_id)
    analytics = session.get_analytics() if session else {}
    
<<<<<<< Updated upstream
    # Generate AI Feedback based on the full transcript
    ai_report = ai.generate_feedback_report(analytics["transcript_text"])
    
    return {
        "analytics": analytics,
        "ai_report": ai_report
    }
=======
    if not analytics and session_id:
        # Try to load from DB if memory session is gone (reloaded server)
        db_session = db.get_session(session_id)
        if db_session and db_session['analytics']:
             analytics = json.loads(db_session['analytics'])

    # Fetch Chat History from DB
    chat_history = db.get_messages(session_id)
    
    # Generate AI Feedback based on the full chat history
    # Pass the structured chat history to the AI engine
    ai_report = ai.generate_feedback_report(chat_history)
    
    # Update DB with final report
    db.update_session_analytics(session_id, analytics, ai_report.get("summary", ""), ai_report.get("radar_chart", {}))
    
    # Update individual message ratings in DB
    for msg_analysis in ai_report.get("detailed_analysis", []):
        # Find matching message in DB (by index or content match, simplified here)
        # In a real app we'd map IDs. For now, we assume sequential order match or updated logic in AI engine.
        # AI Engine will return a list of {id, rating, feedback, improved_answer}
        if "id" in msg_analysis:
            db.update_message_analysis(
                msg_analysis["id"], 
                msg_analysis.get("rating"), 
                msg_analysis.get("feedback"), 
                msg_analysis.get("improved_answer")
            )
            
    # Re-fetch updated chat history
    updated_chat_history = db.get_messages(session_id)
    
    # Format for Frontend ReportData
    report_data = {
        "sessionId": session_id,
        "summary": ai_report.get("summary", "Interview completed."),
        "overallScore": ai_report.get("overall_score", 75),
        "metrics": [
             {"label": "Words Per Minute", "value": analytics.get("avg_wpm", 0), "unit": "WPM", "status": "moderate", "description": "Average speaking pace"},
             {"label": "Eye Contact", "value": int(analytics.get("avg_eye_contact", 0)*100), "unit": "%", "status": "good" if analytics.get("avg_eye_contact",0)>0.6 else "poor", "description": "Visual engagement"},
             {"label": "Posture Score", "value": int(analytics.get("posture_avg", 0)*100), "unit": "%", "status": "good", "description": "Body language stability"},
             {"label": "Stress Level", "value": int(analytics.get("avg_stress", 0)*100), "unit": "%", "status": "moderate", "description": "Detected stress indicators"}
        ],
        "radarData": [
            {"category": "Technical", "user": ai_report.get("radar_chart", {}).get("technical_accuracy", 0), "ideal": 90},
            {"category": "Communication", "user": ai_report.get("radar_chart", {}).get("communication_clarity", 0), "ideal": 90},
            {"category": "Confidence", "user": ai_report.get("radar_chart", {}).get("confidence_level", 0), "ideal": 85},
            {"category": "Problem Solving", "user": ai_report.get("radar_chart", {}).get("problem_solving", 0), "ideal": 90},
            {"category": "Body Language", "user": int(analytics.get("avg_eye_contact", 0)*100), "ideal": 85}
        ],
        "chatLog": updated_chat_history
    }

    print(f"📊 Returning analytics + AI report")
    
    return report_data
>>>>>>> Stashed changes

#
@app.websocket("/ws/interview/{session_id}")
async def interview_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # 1. Reconnect Logic
    if session_id not in sessions:
        sessions[session_id] = InterviewSession(session_id)
<<<<<<< Updated upstream
=======
        # DB: Ensure session exists (reconnect scenario)
        db.create_session(session_id, "Unknown", "General", "Medium") 
        print(f"📝 Created new session: {session_id} (waiting for initialization)")
    else:
        print(f"🔄 Reconnecting to existing session: {session_id}")
>>>>>>> Stashed changes
    
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
                        
<<<<<<< Updated upstream
                        # 4. Generate Audio
                        print("🔊 Generating TTS audio...")
                        audio_b64 = tts.generate_audio(ai_reply)
=======
                        # DB: Log messages
                        db.add_message(session_id, "user", user_text)
                        db.add_message(session_id, "ai", ai_reply)
                        
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
>>>>>>> Stashed changes
                        
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