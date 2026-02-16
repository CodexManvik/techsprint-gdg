"""
WebSocket Routes for Real-Time Interview Sessions

Handles video tracking, audio processing, and LLM conversation flow.
"""
import json
import base64
import asyncio
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.core.interview.engine import InterviewEngine
from backend.core.interview.analyzer import CheatingDetector
from backend.core.cache import redis_cache
from backend.db.repository import get_db, DatabaseRepository

# Legacy imports (to be migrated)
from engine.vision_engine import VisionEngine
from engine.audio_engine import AudioEngine
from engine.tts_engine import TTSEngine
from engine.session_manager import InterviewSession

router = APIRouter()
logger = logging.getLogger(__name__)

# Global instances (TODO: Move to dependency injection)
vision = VisionEngine()
audio_processor = AudioEngine()
tts = TTSEngine()
sessions = {}  # In-memory fallback (Redis preferred)
sessions_lock = asyncio.Lock()  # Protect concurrent access to sessions dict


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
    
    # Track connection start time for accurate elapsed calculation
    connection_start_time = time.time()
    
    # Initialize cheating detector
    cheating_detector = CheatingDetector()
    
    # Initialize database dependency
    # Note: WebSocket cannot use Depends(get_db), so we get it manually
    from backend.db.repository import db_repository
    db = db_repository
    
    # 1. Session Reconnect Logic (with lock protection)
    async with sessions_lock:
        if session_id not in sessions:
            # Try to restore from Redis
            cached_session = await redis_cache.get_session(session_id)
            
            if cached_session:
                # Deserialize cached session into in-memory object
                sessions[session_id] = InterviewSession(
                    session_id,
                    company_focus=cached_session.get('persona', 'General'),
                    difficulty=cached_session.get('difficulty', 'Medium'),
                    topic=cached_session.get('topic', 'General')
                )
                logger.info(f"Restored session from Redis: {session_id}")
            else:
                # Try DB
                db_session = await db.get_session(session_id) if db else None
                if db_session:
                    sessions[session_id] = InterviewSession(
                        session_id,
                        company_focus=db_session.get('persona', 'General'),
                        difficulty=db_session.get('difficulty', 'Medium'),
                        topic=db_session.get('topic', 'General')
                    )
                    logger.info(f"Restored session from DB: {session_id}")
                else:
                    # New session (waiting for initialization)
                    sessions[session_id] = InterviewSession(session_id)
                    logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Reconnecting to existing session: {session_id}")
    
    current_session = sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse JSON with error handling
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                continue
            
            # --- VISION TRACKING ---
            if payload.get("type") == "tracking":
                # Validate landmarks key exists
                if 'landmarks' not in payload or not payload.get('landmarks'):
                    logger.warning("Missing landmarks in tracking payload")
                    continue
                
                try:
                    metrics = vision.analyze_frame(payload['landmarks'])
                    current_session.log_vision_metrics(metrics)
                    
                    # Check for cheating violations with actual elapsed time
                    elapsed = time.time() - connection_start_time
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
                logger.info("Processing audio...")
                
                # Validate audio_data key exists
                if 'audio_data' not in payload or not payload.get('audio_data'):
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing audio data"
                    }))
                    continue
                
                try:
                    # 1. Process Audio → Text
                    audio_data = base64.b64decode(payload['audio_data'])
                    analysis = audio_processor.process_audio(audio_data)
                    user_text = analysis['text']
                    
                    if analysis.get('error'):
                        logger.error(f"Audio error: {analysis['error']}")
                    
                    if not user_text:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "I didn't catch that. Could you speak up?"
                        }))
                        continue
                    
                    # Redact PII from logs - log only metadata
                    logger.info(f"User message length: {len(user_text)} chars")
                    
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
                    
                    # Redact PII from logs - log only length
                    logger.info(f"AI reply length: {len(ai_reply)} chars")
                    
                    # 4. Log interaction
                    current_session.log_interaction(user_text, ai_reply)
                    
                    # 5. Save to DB asynchronously (non-blocking)
                    await asyncio.to_thread(db.add_message, session_id, "user", user_text)
                    await asyncio.to_thread(db.add_message, session_id, "ai", ai_reply)
                    
                    # 6. Generate TTS audio
                    logger.info("Generating TTS audio...")
                    audio_b64 = tts.generate_audio(ai_reply)
                    
                    if audio_b64:
                        logger.info(f"Audio generated: {len(audio_b64)} chars (base64)")
                    else:
                        logger.warning("Audio generation returned None")
                    
                    # 7. Send response
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "reply": ai_reply,
                        "transcript": user_text,
                        "audio": audio_b64
                    }))
                    
                    logger.info("Response sent to frontend")
                    
                    # 8. Update Redis cache
                    session_state = {
                        "session_id": session_id,
                        "history": engine.sessions.get(session_id, []),
                        "analytics": current_session.get_analytics()
                    }
                    await redis_cache.set_session(session_id, session_state)
                
                except Exception as e:
                    logger.error(f"Processing error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "System error processing audio."
                    }))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        
        # Session cleanup on disconnect
        async with sessions_lock:
            # Remove from in-memory sessions
            if session_id in sessions:
                del sessions[session_id]
                logger.info(f"Cleaned up in-memory session: {session_id}")
            
            # Clear Redis cache (optional: keep for session persistence)
            # Uncomment if you want to clear Redis on disconnect:
            # await redis_cache.delete_session(session_id)
            # logger.info(f"Cleared Redis cache for session: {session_id}")
        
        logger.info(f"Session {session_id} cleanup complete")
        
    except Exception as e:
        logger.error(f"CRITICAL Error in session {session_id}: {e}")
        
        # Cleanup on error as well
        async with sessions_lock:
            if session_id in sessions:
                del sessions[session_id]
                logger.info(f"Cleaned up session after error: {session_id}")
