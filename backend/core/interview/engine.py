"""
Interview Engine - Orchestrates LLM-powered Interview Sessions

Handles session initialization, real-time feedback injection, and report generation.
"""
from __future__ import annotations

import re
import asyncio
import json
from typing import Optional
from backend.core.llm.base import LLMClient
from backend.core.llm.ollama import OllamaClient
from backend.core.llm.circuit_breaker import CircuitBreaker
from backend.config.settings import settings
from backend.core.models.llm_schemas import InterviewTurnResponse
import logging

logger = logging.getLogger(__name__)


class SessionNotFoundError(Exception):
    """Raised when a session is not found in the engine"""
    pass


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
        """Create local Ollama client only."""
        if settings.LLM_PROVIDER != "ollama":
            logger.warning("Unsupported LLM_PROVIDER=%s, forcing ollama", settings.LLM_PROVIDER)
        return OllamaClient()
    
    
    def _sanitize_prompt(self, text: str) -> str:
        """Remove potential prompt injection patterns"""
        if not text:
            return ""
        
        # Remove common injection patterns
        dangerous_patterns = [
            r"ignore (previous|all) (instructions|prompts)",
            r"disregard .*?(rules|instructions)",
            r"system:\s*",
            r"<\|.*?\|>",  # Special tokens
            r"\[INST\].*?\[\/INST\]",  # Instruction markers
            r"developer:\s*",
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()

    def _bounded_messages(self, messages: list[dict]) -> list[dict]:
        """Keep system prompt + last N conversational messages."""
        if not messages:
            return []

        system_messages = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        tail = non_system[-settings.MAX_CONTEXT_MESSAGES :]
        return system_messages[:1] + tail

    def _structured_response_prompt(self) -> str:
        """Prompt that enforces concise JSON output contract."""
        return (
            "Return strict JSON only with keys: acknowledgement, feedback_short, next_question. "
            "Use concise professional language, one short sentence each. "
            "No markdown, no code fences, no extra keys."
        )

    def _build_plain_fallback(self, topic: str) -> str:
        """Last-resort concise fallback text."""
        return (
            "Thank you for your response. "
            "You communicated clearly and stayed focused. "
            f"Next question: Could you explain a practical {topic} scenario and your approach?"
        )

    def _safe_parse_json_object(self, raw: str) -> Optional[dict]:
        """Parse JSON object from a model response with minimal tolerance."""
        if not raw:
            return None
        text = raw.strip()

        # Attempt direct parse first.
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Attempt to extract first JSON object block.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None
        return None

    async def _parse_or_repair_structured(self, raw: str, topic: str) -> InterviewTurnResponse:
        """Parse structured response; on failure attempt one JSON repair call."""
        parsed = self._safe_parse_json_object(raw)
        if parsed:
            try:
                return InterviewTurnResponse.model_validate(parsed)
            except Exception:
                pass

        repair_messages = [
            {
                "role": "system",
                "content": (
                    "You are a JSON repair assistant. Return strict JSON only with keys: "
                    "acknowledgement, feedback_short, next_question."
                ),
            },
            {
                "role": "user",
                "content": f"Repair this to valid JSON without changing intent:\n{raw}",
            },
        ]

        repaired = await self.circuit_breaker.call(
            self.llm.chat,
            repair_messages,
            stream=False,
            temperature=0.0,
            top_p=1.0,
            max_tokens=200,
        )

        repaired_dict = self._safe_parse_json_object(repaired if isinstance(repaired, str) else "")
        if repaired_dict:
            try:
                return InterviewTurnResponse.model_validate(repaired_dict)
            except Exception:
                pass

        return InterviewTurnResponse(
            acknowledgement="Thank you for your response.",
            feedback_short="You explained your ideas clearly.",
            next_question=f"Could you describe a practical {topic} challenge and how you would solve it?",
        )

    def _format_client_reply(self, structured: InterviewTurnResponse) -> str:
        """Compose final concise response for frontend compatibility."""
        parts = [
            structured.acknowledgement.strip(),
            structured.feedback_short.strip(),
            f"Next question: {structured.next_question.strip()}",
        ]
        return " ".join(p for p in parts if p)
    
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
            {
                "role": "user",
                "content": (
                    f"Start the interview for topic '{topic}'. "
                    "Provide acknowledgement, short feedback, and first question as JSON."
                ),
            },
        ]

        if settings.LLM_JSON_MODE:
            opening_msg.insert(1, {"role": "system", "content": self._structured_response_prompt()})

        bounded_opening = self._bounded_messages(opening_msg)
        
        response = await self.circuit_breaker.call(
            self.llm.chat,
            bounded_opening,
            stream=False,
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            max_tokens=settings.LLM_MAX_NEW_TOKENS,
        )

        if not isinstance(response, str):
            response = self._build_plain_fallback(topic)

        if settings.LLM_JSON_MODE:
            structured = await self._parse_or_repair_structured(response, topic)
            formatted = self._format_client_reply(structured)
        else:
            formatted = response.strip() or self._build_plain_fallback(topic)
        
        # Add to history (with lock)
        async with self.sessions_lock:
            self.sessions[session_id].append({"role": "assistant", "content": formatted})
        
        return formatted
    
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
            
        Raises:
            SessionNotFoundError: If session_id doesn't exist
        """
        async with self.sessions_lock:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            # Inject behavioral feedback if metrics indicate issues
            enhanced_input = self._inject_feedback(user_input, metrics)
            
            # Add user message to history
            self.sessions[session_id].append({"role": "user", "content": enhanced_input})
            
            # Copy history for processing
            messages = self.sessions[session_id].copy()

        if settings.LLM_JSON_MODE:
            messages.append({"role": "system", "content": self._structured_response_prompt()})
        bounded_messages = self._bounded_messages(messages)
        
        # Get AI response with circuit breaker protection
        response = await self.circuit_breaker.call(
            self.llm.chat,
            bounded_messages,
            stream=False,
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            max_tokens=settings.LLM_MAX_NEW_TOKENS,
        )

        if not isinstance(response, str):
            response = self._build_plain_fallback("interview")

        if settings.LLM_JSON_MODE:
            structured = await self._parse_or_repair_structured(response, "interview")
            formatted = self._format_client_reply(structured)
        else:
            formatted = response.strip() or self._build_plain_fallback("interview")
        
        # Add AI response to history (with lock and defensive check)
        async with self.sessions_lock:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} was removed during processing")
            self.sessions[session_id].append({"role": "assistant", "content": formatted})
        
        return formatted
    
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
