"""
Interview Engine - Orchestrates LLM-powered Interview Sessions

Handles session initialization, real-time feedback injection, and report generation.
"""
import re
import asyncio
from typing import Optional
from backend.core.llm.base import LLMClient
from backend.core.llm.ollama import OllamaClient
from backend.core.llm.circuit_breaker import CircuitBreaker
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class InterviewEngine:
    """Main interview orchestration service"""
    
    def __init__(self):
        # Initialize LLM client based on config
        self.llm: LLMClient = self._create_llm_client()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0
        )
        
        # Session context storage (message history per session)
        self.sessions: dict[str, list[dict]] = {}
        self.sessions_lock = asyncio.Lock()  # Protect concurrent access
    
    def _create_llm_client(self) -> LLMClient:
        """Factory method for LLM client creation"""
        if settings.LLM_PROVIDER == "ollama":
            return OllamaClient()
        else:
            # Fallback to Gemini (existing implementation)
            from engine.ai_engine import AIEngine
            return AIEngine()  # TODO: Wrap in adapter
    
    
    def _sanitize_prompt(self, text: str) -> str:
        """Remove potential prompt injection patterns"""
        if not text:
            return ""
        
        # Remove common injection patterns
        dangerous_patterns = [
            r"ignore (previous|all) (instructions|prompts)",
            r"system:\s*",
            r"<\|.*?\|>",  # Special tokens
            r"\[INST\].*?\[\/INST\]",  # Instruction markers
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    async def start_session(
        self,
        session_id: str,
        persona: str,
        difficulty: str,
        topic: str,
        resume_context: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Initialize a new interview session.
        
        Returns:
            Opening question from the AI
        """
        # Session overwrite check (with lock)
        async with self.sessions_lock:
            if session_id in self.sessions:
                logger.warning(f"Session {session_id} already exists. Overwriting.")
            
            # Sanitize custom_instructions for prompt injection
            safe_instructions = ""
            if custom_instructions:
                safe_instructions = self._sanitize_prompt(custom_instructions)
                if safe_instructions != custom_instructions:
                    logger.warning(f"Sanitized custom instructions for session {session_id}")
            
            # Build system prompt
            system_prompt = self._build_system_prompt(
                persona, difficulty, topic, resume_context, safe_instructions
            )
            
            # Initialize message history
            self.sessions[session_id] = [
                {"role": "system", "content": system_prompt}
            ]
        
        # Get opening question  
        opening_msg = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Start the interview. Ask the first question about {topic}."}
        ]
        
        response = await self.circuit_breaker.call(
            self.llm.chat,
            opening_msg,
            stream=False
        )
        
        # Add to history (with lock)
        async with self.sessions_lock:
            self.sessions[session_id].append({"role": "assistant", "content": response})
        
        return response
    
    async def process_turn(
        self,
        session_id: str,
        user_input: str,
        metrics: Optional[dict] = None
    ) -> str:
        """
        Process one conversational turn with optional real-time feedback.
        
        Args:
            session_id: Active session ID
            user_input: User's spoken answer
            metrics: Vision/audio metrics (eye contact, WPM, etc.)
            
        Returns:
            AI's response
        """
        async with self.sessions_lock:
            if session_id not in self.sessions:
                return "❌ Session not found. Please start a new interview."
            
            # Inject behavioral feedback if metrics indicate issues
            enhanced_input = self._inject_feedback(user_input, metrics)
            
            # Add user message to history
            self.sessions[session_id].append({"role": "user", "content": enhanced_input})
            
            # Copy history for processing
            messages = self.sessions[session_id].copy()
        
        # Get AI response with circuit breaker protection
        response = await self.circuit_breaker.call(
            self.llm.chat,
            messages,
            stream=False
        )
        
        # Add AI response to history (with lock)
        async with self.sessions_lock:
            self.sessions[session_id].append({"role": "assistant", "content": response})
        
        return response
    
    def _build_system_prompt(
        self,
        persona: str,
        difficulty: str,
        topic: str,
        resume_context: Optional[str],
        custom_instructions: Optional[str]
    ) -> str:
        """Construct LLM system prompt"""
        base_prompt = f"""You are conducting an interview with the following parameters:
- **Persona**: {persona}
- **Difficulty**: {difficulty}
- **Topic**: {topic}

CRITICAL INSTRUCTIONS:
1. Keep responses concise (1-3 sentences max) for natural back-and-forth conversation.
2. Ask ONE question at a time.
3. Provide real-time feedback on body language when mentioned.
4. If the candidate looks away from camera (low eye contact), gently remind them ONCE.
5. Be professional but conversational.
"""
        
        if resume_context:
            base_prompt += f"\n\n**RESUME CONTEXT**:\n{resume_context[:1000]}\n"
        
        if custom_instructions:
            base_prompt += f"\n\n**CUSTOM INSTRUCTIONS**:\n{custom_instructions}\n"
        
        return base_prompt
    
    def _inject_feedback(self, user_input: str, metrics: Optional[dict]) -> str:
        """Add behavioral context to user input for AI awareness"""
        if not metrics:
            return user_input
        
        feedback_notes = []
        
        # Eye contact warning
        eye_contact = metrics.get("eye_contact_score", 1.0)
        if eye_contact < 0.3:
            feedback_notes.append(f"[Candidate looking away from camera - eye contact: {eye_contact:.0%}]")
        
        # Fidgeting detection
        fidget_score = metrics.get("fidget_score", 0)
        if fidget_score > 5.0:
            feedback_notes.append(f"[Excessive head movement detected]")
        
        # Stress indicators
        if metrics.get("is_stressed"):
            feedback_notes.append("[Stress indicators detected - furrowed brows]")
        
        # Combine with user input
        if feedback_notes:
            context = " ".join(feedback_notes)
            return f"{context}\n\nCandidate's answer: \"{user_input}\""
        
        return user_input
    
    async def close(self):
        """Cleanup resources"""
        await self.llm.close()
