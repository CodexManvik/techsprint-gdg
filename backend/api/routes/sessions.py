"""
Session Management Routes

Handles interview session CRUD operations, history, and reports.
"""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from engine.auth import AuthEngine, TokenData
from engine.ai_engine import AIEngine
from engine.personas import get_persona_list
from engine.difficulty import get_difficulty_list, get_topics_list
from engine.session_manager import InterviewSession
from engine.tts_engine import TTSEngine
from backend.db.repository import get_db, DatabaseRepository
from backend.core.interview.engine import InterviewEngine
from backend.core.cache import redis_cache
from pypdf import PdfReader
import io
import uuid

router = APIRouter()

# Global instances (TODO: Move to dependency injection)
auth_engine = AuthEngine()
ai = None  # Lazy loaded when needed
tts = TTSEngine()
sessions = {}  # In-memory fallback


class StartSessionRequest(BaseModel):
    persona: str
    difficulty: str
    topic: str
    resume_text: str = None
    custom_instructions: str = None


async def get_interview_engine() -> InterviewEngine:
    """Dependency: Get interview engine instance"""
    from backend.main import interview_engine
    return interview_engine


@router.get("/config/options")
async def get_config_options():
    """Returns available personas, difficulties, and topics for frontend"""
    return {
        "personas": get_persona_list(),
        "difficulties": get_difficulty_list(),
        "topics": get_topics_list()
    }


@router.post("/start-interview")
async def start_interview(
    req: StartSessionRequest,
    current_user: TokenData = Depends(auth_engine.get_current_user),
    engine: InterviewEngine = Depends(get_interview_engine),
    db: DatabaseRepository = Depends(get_db)
):
    """
    Start a new interview session using NEW InterviewEngine.
    
    This endpoint now uses the refactored backend with circuit breaker.
    """
    session_id = str(uuid.uuid4())
    
    print(f"🚀 Starting interview with NEW backend:")
    print(f"   - Session ID: {session_id}")
    print(f"   - User: {current_user.email}")
    
    # Create legacy session for compatibility
    sessions[session_id] = InterviewSession(
        session_id,
        company_focus=req.persona,
        difficulty=req.difficulty,
        topic=req.topic
    )
    
    # DB: Create session
    await db.create_session(session_id, current_user.user_id, req.persona, req.topic, req.difficulty)
    
    # Set TTS persona
    tts.set_persona(req.persona)
    
    # Use NEW InterviewEngine
    opening_question = await engine.start_session(
        session_id=session_id,
        persona=req.persona,
        difficulty=req.difficulty,
        topic=req.topic,
        resume_context=req.resume_text,
        custom_instructions=req.custom_instructions
    )
    
    return {"session_id": session_id, "opening_question": opening_question}


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(auth_engine.get_current_user)
):
    """Extract text from uploaded PDF resume (requires authentication)"""
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file with size limit (10MB max)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        content = await file.read(MAX_FILE_SIZE + 1)
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Parse PDF safely
        reader = PdfReader(io.BytesIO(content))
        
        # Extract text from all pages, coalescing None to empty string
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        text = "\n".join(text_parts)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF contains no extractable text")
        
        return {"status": "success", "text": text[:5000]}  # Limit text size
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle PDF parsing errors or other unexpected errors
        raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")


@router.get("/history")
async def get_history(
    current_user: TokenData = Depends(auth_engine.get_current_user),
    db: DatabaseRepository = Depends(get_db)
):
    """Get user's interview session history"""
    return await db.get_user_sessions(current_user.user_id)


@router.get("/check_session/{session_id}")
async def check_session(
    session_id: str,
    current_user: TokenData = Depends(auth_engine.get_current_user),
    db: DatabaseRepository = Depends(get_db)
):
    """Verifies if a session ID is valid and active (requires authentication)"""
    # Check in-memory
    if session_id in sessions:
        session_obj = sessions[session_id]
        # Verify ownership (if session has user tracking)
        # For now, return basic details
        return {
            "valid": True,
            "details": {
                "topic": session_obj.topic,
                "persona": session_obj.company_focus
            }
        }
    
    # Check Redis
    cached = await redis_cache.get_session(session_id)
    if cached:
        return {"valid": True, "details": {"topic": cached.get("topic"), "persona": cached.get("persona")}}
    
    # Check DB with ownership verification
    session = await db.get_session(session_id)
    if session:
        # Verify ownership
        if session.get('user_id') != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied: You do not own this session")
        
        return {
            "valid": True,
            "details": {
                "topic": session['topic'],
                "persona": session['persona']
            }
        }
    
    return {"valid": False}


@router.get("/session/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: TokenData = Depends(auth_engine.get_current_user),
    db: DatabaseRepository = Depends(get_db)
):
    """Retrieve chat history for a session (with ownership verification)"""
    # Verify session belongs to user
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get('user_id') != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this session")
    
    messages = await db.get_messages(session_id)
    return messages


@router.get("/report")
async def get_report(
    session_id: Optional[str] = None,
    current_user: TokenData = Depends(auth_engine.get_current_user),
    db: DatabaseRepository = Depends(get_db)
):
    """
    Generate interview report with AI feedback (requires authentication and ownership).
    
    TODO: Migrate to use async database calls
    """
    print(f"📋 Report requested for session: {session_id}")
    
    # Mock data if no session_id
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
                {"label": "Words Per Minute", "value": 0, "unit": "WPM", "status": "moderate"},
                {"label": "Stress Level", "value": 0, "unit": "%", "status": "good"},
                {"label": "Eye Contact", "value": 0, "unit": "%", "status": "moderate"},
                {"label": "Posture Score", "value": 0, "unit": "%", "status": "moderate"}
            ],
            "integrityEvents": [],
            "totalDuration": 0
        }
    
    # Verify ownership and fetch session analytics
    db_session = await db.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Ownership check
    if db_session.get('user_id') != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this session")
    
    # Get analytics from memory or DB
    session = sessions.get(session_id)
    analytics = session.get_analytics() if session else {}
    
    if not analytics and db_session.get('analytics'):
        try:
            analytics = json.loads(db_session['analytics'])
        except (json.JSONDecodeError, TypeError):
            analytics = {}
    
    # Fetch chat history
    chat_history = await db.get_messages(session_id)
    
    # Generate AI feedback (skip if AI engine not available)
    ai_report = None
    if ai:
        ai_report = ai.generate_feedback_report(chat_history)
    else:
        # Fallback: Generate basic report without AI
        print("ℹ️ AI Engine not available - generating basic report")
        ai_report = {
            "summary": "Interview completed. Metrics tracked successfully.",
            "overall_score": 75,
            "radar_chart": {
                "technical_accuracy": 75,
                "communication_clarity": 75,
                "confidence_level": 75,
                "problem_solving": 75,
                "cultural_fit": 75
            },
            "detailed_analysis": []
        }
    
    # Update DB
    await db.update_session_analytics(
        session_id,
        analytics,
        ai_report.get("summary", ""),
        ai_report.get("radar_chart", {})
    )
    
    # Update individual message ratings (only if AI provided analysis)
    for msg_analysis in ai_report.get("detailed_analysis", []):
        if "id" in msg_analysis:
            await db.update_message_analysis(
                msg_analysis["id"],
                msg_analysis.get("rating"),
                msg_analysis.get("feedback"),
                msg_analysis.get("improved_answer")
            )
    
    # Re-fetch updated chat history
    updated_chat_history = await db.get_messages(session_id)
    
    # Format for frontend
    report_data = {
        "sessionId": session_id,
        "summary": ai_report.get("summary", "Interview completed."),
        "overallScore": ai_report.get("overall_score", 75),
        "metrics": [
            {"label": "Words Per Minute", "value": analytics.get("avg_wpm", 0), "unit": "WPM", "status": "moderate"},
            {"label": "Eye Contact", "value": int(analytics.get("avg_eye_contact", 0)*100), "unit": "%", "status": "good" if analytics.get("avg_eye_contact", 0) > 0.6 else "poor"},
            {"label": "Posture Score", "value": int(analytics.get("posture_avg", 0)*100), "unit": "%", "status": "good"},
            {"label": "Stress Level", "value": int(analytics.get("avg_stress", 0)*100), "unit": "%", "status": "moderate"}
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
    
    print(f"📋 Returning analytics + AI report")
    return report_data
