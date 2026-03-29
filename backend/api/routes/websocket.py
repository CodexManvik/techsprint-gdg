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
from backend.core.interview.engine import InterviewEngine, SessionNotFoundError
from backend.core.interview.scorer import TurnScoringService
from backend.core.interview.analyzer import CheatingDetector
from backend.core.cache import redis_cache
from backend.db.repository import db_repository
from backend.config.settings import settings
from backend.core.session_store import legacy_sessions, sessions_lock, active_connections
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


def _normalize_engine_history(messages: list[dict]) -> list[dict[str, str]]:
    """
    Normalize message history for InterviewEngine compatibility.
    
    Converts "ai" role to "assistant" and filters out "system" messages.
    
    IMPORTANT: System messages are intentionally dropped here because the InterviewEngine
    rebuilds system prompts dynamically on reconnect. If the DB schema evolves to store
    system messages that need preservation, this filter will silently drop them.
    
    Returns:
        List of normalized messages with only "user" and "assistant" roles.
    """
    normalized: list[dict[str, str]] = []
    for msg in messages or []:
        role = (msg or {}).get("role")
        content = (msg or {}).get("content", "")
        if role == "ai":
            role = "assistant"
        if role not in {"user", "assistant"}:
            # System messages are filtered out - see docstring above
            continue
        normalized.append({"role": role, "content": str(content)})
    return normalized


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


async def get_turn_scorer() -> TurnScoringService | None:
    """Dependency: Get turn scoring service instance."""
    from backend.main import turn_scorer
    return turn_scorer


@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
    engine: InterviewEngine = Depends(get_interview_engine),
    scorer: TurnScoringService | None = Depends(get_turn_scorer),
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
    last_tracking_time = connection_start_time

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
        if current_user.user_id is None:
            await _send_error(websocket, "unauthorized", "Invalid authentication token")
            await websocket.close(code=1008)
            return
        if not await db.session_belongs_to_user(session_id, current_user.user_id):
            session_exists = await db.get_session(session_id)
            code = "forbidden" if session_exists else "session_not_found"
            msg = "You do not own this session" if session_exists else "Session not found"
            await _send_error(websocket, code, msg)
            await websocket.close(code=1008)
            return

    # Session reconnect logic: Redis first, then DB
    async with sessions_lock:
        engine_history: list[dict[str, str]] = []
        resume_text: str | None = None
        
        if session_id not in legacy_sessions:
            cached_session = await redis_cache.get_session(session_id)
            if cached_session:
                cached_user = cached_session.get("user_id")
                if current_user is not None and cached_user and cached_user != current_user.user_id:
                    await _send_error(websocket, "forbidden", "Cached session owner mismatch")
                    await websocket.close(code=1008)
                    return

                legacy_sessions[session_id] = InterviewSession(
                    session_id,
                    company_focus=cached_session.get("persona", "General"),
                    difficulty=cached_session.get("difficulty", "Medium"),
                    topic=cached_session.get("topic", "General"),
                    job_description=cached_session.get("job_description", ""),
                )
                engine_history = _normalize_engine_history(cached_session.get("history") or [])
                resume_text = cached_session.get("resume_text")
                logger.info("Restored session from Redis: %s", session_id)
            else:
                db_session = await db.get_session(session_id)
                if db_session:
                    legacy_sessions[session_id] = InterviewSession(
                        session_id,
                        company_focus=db_session.get("persona", "General"),
                        difficulty=db_session.get("difficulty", "Medium"),
                        topic=db_session.get("topic", "General"),
                        job_description=db_session.get("job_description", ""),
                    )
                    db_messages = await db.get_messages(session_id)
                    engine_history = _normalize_engine_history(db_messages)
                    resume_text = db_session.get("resume_text")  # Phase 4: Restore resume from DB
                    logger.info("Restored session from DB: %s", session_id)
                else:
                    await _send_error(websocket, "session_not_found", "Session not found")
                    await websocket.close(code=1008)
                    return
        else:
            logger.info("Reconnecting to existing session: %s", session_id)

        current_session = legacy_sessions[session_id]

        # Ensure InterviewEngine has runtime state restored before processing turns.
        if session_id not in engine.sessions:
            await engine.restore_session_state(
                session_id=session_id,
                persona=current_session.company_focus,
                difficulty=current_session.difficulty,
                topic=current_session.topic,
                job_description=current_session.job_description,
                history=engine_history,
                resume_context=resume_text,  # Phase 4: Pass resume to engine
            )

        active_connections[session_id] = active_connections.get(session_id, 0) + 1

    await websocket.send_text(
        json.dumps(
            {
                "type": "connected",
                "session_id": session_id,
            }
        )
    )

    try:
        last_client_activity = time.monotonic()
        heartbeat_interval = float(settings.WS_HEARTBEAT_INTERVAL_SEC)
        heartbeat_timeout = float(settings.WS_HEARTBEAT_TIMEOUT_SEC)

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=heartbeat_interval)
                last_client_activity = time.monotonic()
            except asyncio.TimeoutError:
                idle_seconds = time.monotonic() - last_client_activity
                if idle_seconds >= heartbeat_timeout:
                    await _send_error(websocket, "heartbeat_timeout", "WebSocket heartbeat timeout")
                    await websocket.close(code=1001)
                    break

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": int(time.time()),
                        }
                    )
                )
                continue
            
            # Parse JSON with error handling
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                await _send_error(websocket, "invalid_json", "Invalid JSON format")
                continue

            if payload.get("type") == "pong":
                last_client_activity = time.monotonic()
                continue

            if payload.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": int(time.time())}))
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
                    now = time.time()
                    elapsed = max(0.0, now - last_tracking_time)
                    last_tracking_time = now
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
                    # 1. Process Audio → Text (async to avoid blocking event loop)
                    audio_data = base64.b64decode(payload['audio_data'])
                    loop = asyncio.get_event_loop()
                    analysis = await loop.run_in_executor(None, audio_processor.process_audio, audio_data)
                    user_text = analysis['text']
                    
                    if analysis.get('error'):
                        logger.error(f"Audio error: {analysis['error']}")
                    
                    if not user_text:
                        await _send_error(websocket, "empty_transcript", "I didn't catch that. Could you speak up?")
                        continue

                    if len(user_text) > settings.MAX_USER_INPUT_CHARS:
                        await _send_error(
                            websocket,
                            "input_too_long",
                            f"Maximum input length is {settings.MAX_USER_INPUT_CHARS} characters",
                        )
                        continue
                    
                    # Redact PII from logs - log only metadata
                    logger.info(f"User message length: {len(user_text)} chars")
                    
                    # 2. Get current vision metrics for context
                    current_metrics = None
                    if payload.get('landmarks'):
                        current_metrics = vision.analyze_frame(payload['landmarks'])
                    
                    # 3. Get AI Response via NEW InterviewEngine
                    prior_question = ""
                    session_history = engine.sessions.get(session_id, [])
                    for msg in reversed(session_history):
                        if msg.get("role") == "assistant":
                            prior_question = msg.get("content", "")
                            break

                    try:
                        ai_reply = await engine.process_turn(
                            session_id=session_id,
                            user_input=user_text,
                            metrics=current_metrics
                        )
                    except SessionNotFoundError:
                        await engine.restore_session_state(
                            session_id=session_id,
                            persona=current_session.company_focus,
                            difficulty=current_session.difficulty,
                            topic=current_session.topic,
                            job_description=current_session.job_description,
                            history=_normalize_engine_history(await db.get_messages(session_id)),
                        )
                        ai_reply = await engine.process_turn(
                            session_id=session_id,
                            user_input=user_text,
                            metrics=current_metrics
                        )
                    
                    # Redact PII from logs - log only length
                    logger.info(f"AI reply length: {len(ai_reply)} chars")
                    
                    # 4. Log interaction
                    current_session.log_audio_metrics(analysis)
                    current_session.log_interaction(user_text, ai_reply)
                    
                    # 5. Save to DB asynchronously (non-blocking)
                    user_message_id = await db.add_message(session_id, "user", user_text)
                    await db.add_message(session_id, "ai", ai_reply)

                    evidence_payload = {
                        "session_id": session_id,
                        "message_id": user_message_id,
                        "topic": current_session.topic,
                        "persona": current_session.company_focus,
                        "difficulty": current_session.difficulty,
                        "job_description": current_session.job_description,
                        "previous_question": prior_question,
                        "user_text": user_text,
                        "ai_reply": ai_reply,
                        "metrics": current_metrics or {},
                        "audio": {
                            "wpm": analysis.get("wpm"),
                            "speech_ratio": analysis.get("speech_ratio"),  # New metric from faster-whisper
                            "duration_seconds": analysis.get("duration_seconds"),
                            "error": analysis.get("error"),
                        },
                        # Phase 4: Enrich with competencies and turn context
                        "expected_competencies": engine.session_state.get(session_id, {}).get("competencies", []),
                        "turn_number": len(engine.sessions.get(session_id, [])) // 2,
                        "speech_metrics": {
                            "wpm": analysis.get("wpm"),
                            "speech_ratio": analysis.get("speech_ratio"),
                            "duration_seconds": analysis.get("duration_seconds"),
                        },
                        "timestamp": time.time(),
                    }
                    await db.add_turn_evidence(session_id, evidence_payload, message_id=user_message_id)

                    if scorer is not None:
                        await scorer.enqueue(evidence_payload)
                    
                    # 6. Generate TTS audio (async to avoid blocking event loop)
                    logger.info("Generating TTS audio...")
                    loop = asyncio.get_event_loop()
                    audio_b64 = await loop.run_in_executor(None, tts.generate_audio, ai_reply)
                    
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
                        "job_description": current_session.job_description,
                        "history": engine.sessions.get(session_id, []),
                        "analytics": current_session.get_analytics(),
                    }
                    await redis_cache.set_session(session_id, session_state)
                
                except Exception as e:
                    logger.error(f"Processing error: {e}")
                    await _send_error(websocket, "processing_error", "System error processing audio")

            else:
                await _send_error(websocket, "unsupported_type", "Unsupported websocket payload type")
    
    except WebSocketDisconnect as exc:
        logger.info("WebSocket disconnected for session %s code=%s", session_id, exc.code)
        
        # Session cleanup on disconnect without disrupting active peer sockets
        async with sessions_lock:
            current_count = active_connections.get(session_id, 0)
            if current_count <= 1:
                active_connections.pop(session_id, None)
                legacy_sessions.pop(session_id, None)
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
        logger.exception("CRITICAL Error in session %s", session_id)
        
        # Cleanup on error without removing state for other active sockets
        async with sessions_lock:
            current_count = active_connections.get(session_id, 0)
            if current_count <= 1:
                active_connections.pop(session_id, None)
                legacy_sessions.pop(session_id, None)
                logger.info("Cleaned up session after error: %s", session_id)
            else:
                active_connections[session_id] = current_count - 1
                logger.info(
                    "Decremented active connections after error session_id=%s remaining=%s",
                    session_id,
                    active_connections[session_id],
                )

        try:
            await websocket.close(code=1011)
        except RuntimeError:
            # Socket may already be closed by client.
            pass
