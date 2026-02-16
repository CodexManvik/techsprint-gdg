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
from database import Database
from backend.core.interview.engine import InterviewEngine
from backend.core.cache import redis_cache
from pypdf import PdfReader
import io
import uuid

router = APIRouter()

# Global instances (TODO: Move to dependency injection)
db = Database()
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
    engine: InterviewEngine = Depends(get_interview_engine)
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
    db.create_session(session_id, current_user.user_id, req.persona, req.topic, req.difficulty)
    
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
async def upload_resume(file: UploadFile = File(...)):
    """Extract text from uploaded PDF resume"""
    try:
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() for page in reader.pages])
        return {"status": "success", "text": text[:5000]}  # Limit text size
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/history")
async def get_history(current_user: TokenData = Depends(auth_engine.get_current_user)):
    """Get user's interview session history"""
    return db.get_user_sessions(current_user.user_id)


@router.post("/check_session/{session_id}")
async def check_session(session_id: str):
    """Verifies if a session ID is valid and active"""
    # Check in-memory
    if session_id in sessions:
        return {
            "valid": True,
            "details": {
                "topic": sessions[session_id].topic,
                "persona": sessions[session_id].company_focus
            }
        }
    
    # Check Redis
    cached = await redis_cache.get_session(session_id)
    if cached:
        return {"valid": True, "details": cached}
    
    # Check DB
    session = db.get_session(session_id)
    if session:
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
    current_user: TokenData = Depends(auth_engine.get_current_user)
):
    """Retrieve chat history for a session"""
    # TODO: Verify session belongs to user
    messages = db.get_messages(session_id)
    return messages


@router.get("/report")
async def get_report(session_id: Optional[str] = None):
    """
    Generate interview report with AI feedback.
    
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
    
    # Fetch session analytics
    session = sessions.get(session_id)
    analytics = session.get_analytics() if session else {}
    
    if not analytics and session_id:
        # Try DB
        db_session = db.get_session(session_id)
        if db_session and db_session['analytics']:
            analytics = json.loads(db_session['analytics'])
    
    # Fetch chat history
    chat_history = db.get_messages(session_id)
    
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
    db.update_session_analytics(
        session_id,
        analytics,
        ai_report.get("summary", ""),
        ai_report.get("radar_chart", {})
    )
    
    # Update individual message ratings (only if AI provided analysis)
    for msg_analysis in ai_report.get("detailed_analysis", []):
        if "id" in msg_analysis:
            db.update_message_analysis(
                msg_analysis["id"],
                msg_analysis.get("rating"),
                msg_analysis.get("feedback"),
                msg_analysis.get("improved_answer")
            )
    
    # Re-fetch updated chat history
    updated_chat_history = db.get_messages(session_id)
    
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
