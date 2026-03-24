"""
WebSocket Routes for Real-Time Interview Sessions

Handles video tracking, audio processing, and LLM conversation flow.
"""
import json
import base64
import asyncio
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from backend.core.interview.engine import InterviewEngine
from backend.core.interview.analyzer import CheatingDetector
from backend.core.cache import redis_cache
from backend.db.repository import db_repository
from backend.config.settings import settings
from backend.core.security.ws_auth import authenticate_websocket
from engine.auth import TokenData

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
active_connections: dict[str, int] = {}


async def _send_error(websocket: WebSocket, code: str, message: str):
    await websocket.send_text(
        json.dumps(
            {
                "type": "error",
                "code": code,
                "message": message,
            }
        )
    )


async def _resolve_user(websocket: WebSocket) -> TokenData | None:
    if not settings.WS_AUTH_REQUIRED:
        return None
    return await authenticate_websocket(websocket)


def _get_auth_header_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


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

    # Resolve auth context and validate ownership
    db = db_repository
    if db is None:
        await _send_error(websocket, "db_unavailable", "Database connection unavailable")
        await websocket.close(code=1011)
        return

    try:
        current_user = await _resolve_user(websocket)
    except HTTPException as exc:
        await _send_error(websocket, "unauthorized", exc.detail)
        await websocket.close(code=1008)
        return

    if current_user is not None:
        if not await db.session_belongs_to_user(session_id, current_user.user_id):
            session_exists = await db.get_session(session_id)
            code = "forbidden" if session_exists else "session_not_found"
            msg = "You do not own this session" if session_exists else "Session not found"
            await _send_error(websocket, code, msg)
            await websocket.close(code=1008)
            return

    # Session reconnect logic: Redis first, then DB
    async with sessions_lock:
        if session_id not in sessions:
            cached_session = await redis_cache.get_session(session_id)
            if cached_session:
                cached_user = cached_session.get("user_id")
                if current_user is not None and cached_user and cached_user != current_user.user_id:
                    await _send_error(websocket, "forbidden", "Cached session owner mismatch")
                    await websocket.close(code=1008)
                    return

                sessions[session_id] = InterviewSession(
                    session_id,
                    company_focus=cached_session.get("persona", "General"),
                    difficulty=cached_session.get("difficulty", "Medium"),
                    topic=cached_session.get("topic", "General"),
                )
                logger.info("Restored session from Redis: %s", session_id)
            else:
                db_session = await db.get_session(session_id)
                if db_session:
                    sessions[session_id] = InterviewSession(
                        session_id,
                        company_focus=db_session.get("persona", "General"),
                        difficulty=db_session.get("difficulty", "Medium"),
                        topic=db_session.get("topic", "General"),
                    )
                    logger.info("Restored session from DB: %s", session_id)
                else:
                    await _send_error(websocket, "session_not_found", "Session not found")
                    await websocket.close(code=1008)
                    return
        else:
            logger.info("Reconnecting to existing session: %s", session_id)

        active_connections[session_id] = active_connections.get(session_id, 0) + 1
        current_session = sessions[session_id]

    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse JSON with error handling
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                await _send_error(websocket, "invalid_json", "Invalid JSON format")
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
                    logger.exception("Vision processing error for session %s", session_id)
                    await _send_error(websocket, "vision_error", "Unable to process tracking payload")
            
            # --- AUDIO CONVERSATION ---
            elif payload.get("type") == "conversation":
                logger.info("Processing audio...")
                
                # Validate audio_data key exists
                if 'audio_data' not in payload or not payload.get('audio_data'):
                    await _send_error(websocket, "missing_audio", "Missing audio data")
                    continue
                
                try:
                    # 1. Process Audio → Text
                    audio_data = base64.b64decode(payload['audio_data'])
                    analysis = audio_processor.process_audio(audio_data)
                    user_text = analysis['text']
                    
                    if analysis.get('error'):
                        logger.error(f"Audio error: {analysis['error']}")
                    
                    if not user_text:
                        await _send_error(websocket, "empty_transcript", "I didn't catch that. Could you speak up?")
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
                    await db.add_message(session_id, "user", user_text)
                    await db.add_message(session_id, "ai", ai_reply)
                    
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
                        "user_id": current_user.user_id if current_user else None,
                        "persona": current_session.company_focus,
                        "difficulty": current_session.difficulty,
                        "topic": current_session.topic,
                        "history": engine.sessions.get(session_id, []),
                        "analytics": current_session.get_analytics(),
                    }
                    await redis_cache.set_session(session_id, session_state)
                
                except Exception as e:
                    logger.error(f"Processing error: {e}")
                    await _send_error(websocket, "processing_error", "System error processing audio")

            else:
                await _send_error(websocket, "unsupported_type", "Unsupported websocket payload type")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        
        # Session cleanup on disconnect without disrupting active peer sockets
        async with sessions_lock:
            current_count = active_connections.get(session_id, 0)
            if current_count <= 1:
                active_connections.pop(session_id, None)
                sessions.pop(session_id, None)
                logger.info("Cleaned up in-memory session (last socket): %s", session_id)
            else:
                active_connections[session_id] = current_count - 1
                logger.info(
                    "Kept session state for remaining sockets session_id=%s remaining=%s",
                    session_id,
                    active_connections[session_id],
                )
        
        logger.info(f"Session {session_id} cleanup complete")
        
    except Exception as e:
        logger.error(f"CRITICAL Error in session {session_id}: {e}")
        
        # Cleanup on error without removing state for other active sockets
        async with sessions_lock:
            current_count = active_connections.get(session_id, 0)
            if current_count <= 1:
                active_connections.pop(session_id, None)
                sessions.pop(session_id, None)
                logger.info("Cleaned up session after error: %s", session_id)
            else:
                active_connections[session_id] = current_count - 1
