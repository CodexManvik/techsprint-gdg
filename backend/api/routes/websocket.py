"""
WebSocket Routes for Real-Time Interview Sessions

Handles video tracking, audio processing, and LLM conversation flow.
"""
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.core.interview.engine import InterviewEngine
from backend.core.interview.analyzer import CheatingDetector
from backend.core.cache import redis_cache
from database import Database

# Legacy imports (to be migrated)
from engine.vision_engine import VisionEngine
from engine.audio_engine import AudioEngine
from engine.tts_engine import TTSEngine
from engine.session_manager import InterviewSession

router = APIRouter()

# Global instances (TODO: Move to dependency injection)
db = Database()
vision = VisionEngine()
audio_processor = AudioEngine()
tts = TTSEngine()
sessions = {}  # In-memory fallback (Redis preferred)


async def get_interview_engine() -> InterviewEngine:
    """Dependency: Get interview engine instance"""
    from backend.main import interview_engine
    return interview_engine


@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
    engine: InterviewEngine = Depends(get_interview_engine)
):
    """
    Real-time interview WebSocket handler.
    
    Handles:
    - Vision tracking (landmarks, metrics)
    - Audio processing (STT)
    - LLM conversation (via InterviewEngine)
    - Session state management
    """
    await websocket.accept()
    
    # Initialize cheating detector
    cheating_detector = CheatingDetector()
    
    # 1. Session Reconnect Logic
    if session_id not in sessions:
        # Try to restore from Redis
        cached_session = await redis_cache.get_session(session_id)
        
        if cached_session:
            print(f"🔄 Restored session from Redis: {session_id}")
        else:
            # Try DB
            db_session = db.get_session(session_id)
            if db_session:
                sessions[session_id] = InterviewSession(
                    session_id,
                    company_focus=db_session.get('persona', 'General'),
                    difficulty=db_session.get('difficulty', 'Medium'),
                    topic=db_session.get('topic', 'General')
                )
                print(f"🔄 Restored session from DB: {session_id}")
            else:
                # New session (waiting for initialization)
                sessions[session_id] = InterviewSession(session_id)
                print(f"📝 Created new session: {session_id}")
    else:
        print(f"🔄 Reconnecting to existing session: {session_id}")
    
    current_session = sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # --- VISION TRACKING ---
            if payload.get("type") == "tracking":
                try:
                    metrics = vision.analyze_frame(payload['landmarks'])
                    current_session.log_vision_metrics(metrics)
                    
                    # Check for cheating violations
                    elapsed = 5.0  # TODO: Track actual elapsed time
                    violation = cheating_detector.check_violations(metrics, elapsed)
                    
                    response = {
                        "type": "metrics_update",
                        "metrics": metrics
                    }
                    
                    if violation["alert"]:
                        response["alert"] = violation["alert"]
                        response["severity"] = violation["severity"]
                    
                    await websocket.send_text(json.dumps(response))
                    
                except Exception as e:
                    print(f"Vision Error: {e}")
            
            # --- AUDIO CONVERSATION ---
            elif payload.get("type") == "conversation":
                print("🎤 Processing audio...")
                
                try:
                    # 1. Process Audio → Text
                    audio_data = base64.b64decode(payload['audio_data'])
                    analysis = audio_processor.process_audio(audio_data)
                    user_text = analysis['text']
                    
                    if analysis.get('error'):
                        print(f"Audio Error: {analysis['error']}")
                    
                    if not user_text:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "I didn't catch that. Could you speak up?"
                        }))
                        continue
                    
                    print(f"🗣️ User: {user_text}")
                    
                    # 2. Get current vision metrics for context
                    current_metrics = None
                    if payload.get('landmarks'):
                        current_metrics = vision.analyze_frame(payload['landmarks'])
                    
                    # 3. Get AI Response via NEW InterviewEngine
                    ai_reply = await engine.process_turn(
                        session_id=session_id,
                        user_input=user_text,
                        metrics=current_metrics
                    )
                    
                    print(f"🤖 AI: {ai_reply}")
                    
                    # 4. Log interaction
                    current_session.log_interaction(user_text, ai_reply)
                    
                    # 5. Save to DB
                    db.add_message(session_id, "user", user_text)
                    db.add_message(session_id, "ai", ai_reply)
                    
                    # 6. Generate TTS audio
                    print("🔊 Generating TTS audio...")
                    audio_b64 = tts.generate_audio(ai_reply)
                    
                    if audio_b64:
                        print(f"✅ Audio generated: {len(audio_b64)} chars (base64)")
                    else:
                        print("⚠️ Audio generation returned None")
                    
                    # 7. Send response
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "reply": ai_reply,
                        "transcript": user_text,
                        "audio": audio_b64
                    }))
                    
                    print("📤 Response sent to frontend")
                    
                    # 8. Update Redis cache
                    session_state = {
                        "session_id": session_id,
                        "history": engine.sessions.get(session_id, []),
                        "analytics": current_session.get_analytics()
                    }
                    await redis_cache.set_session(session_id, session_state)
                
                except Exception as e:
                    print(f"Processing Error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "System error processing audio."
                    }))
    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"CRITICAL Error: {e}")
