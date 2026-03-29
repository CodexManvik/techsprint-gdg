"""
Interview Engine - Orchestrates LLM-powered Interview Sessions.

Responsibilities:
- Manage per-session interviewer context and behavior policy state
- Ground interview flow to the provided job description
- Serialize LLM calls to avoid concurrent GPU pressure on low VRAM setups
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Optional

from backend.config.settings import settings
from backend.core.llm.base import LLMClient
from backend.core.llm.circuit_breaker import CircuitBreaker
from backend.core.llm.ollama import OllamaClient
from backend.core.models.llm_schemas import InterviewTurnResponse

logger = logging.getLogger(__name__)


class SessionNotFoundError(Exception):
    """Raised when a session is not found in the engine."""


class InterviewEngine:
    """Main interview orchestration service."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._owns_llm = llm_client is None
        self.llm: LLMClient = llm_client or self._create_llm_client()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

        # Separate locks for interviewer (real-time) vs scorer (background).
        # On low VRAM GPU, OS-level scheduler handles queuing more efficiently than Python-level blocking.
        self.inference_lock = asyncio.Lock()  # Live interview turns
        self.scoring_lock = asyncio.Lock()    # Background scorer

        # Session message history and runtime policy state.
        self.sessions: dict[str, list[dict[str, str]]] = {}
        self.session_state: dict[str, dict[str, Any]] = {}
        self.sessions_lock = asyncio.Lock()

    def _create_llm_client(self) -> LLMClient:
        if settings.LLM_PROVIDER != "ollama":
            logger.warning("Unsupported LLM_PROVIDER=%s, forcing ollama", settings.LLM_PROVIDER)
        return OllamaClient()

    def _sanitize_prompt(self, text: str) -> str:
        """Remove common prompt-injection patterns from user provided instructions."""
        if not text:
            return ""

        dangerous_patterns = [
            r"ignore (previous|all) (instructions|prompts)",
            r"disregard .*?(rules|instructions)",
            r"system:\s*",
            r"<\|.*?\|>",
            r"\[INST\].*?\[\/INST\]",
            r"developer:\s*",
        ]

        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    def _bounded_messages(self, messages: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
        """Keep primary system prompt and most recent conversational context."""
        if not messages:
            return []

        system_messages = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        tail = non_system[-max(1, limit) :]
        return system_messages[:1] + tail

    def _structured_response_prompt(self) -> str:
        return (
            "Return strict JSON only with keys: acknowledgement, feedback_short, next_question. "
            "No markdown, no code fences, no extra keys. "
            "Use professional conversational tone and keep each field clear and specific."
        )

    def _build_plain_fallback(self, topic: str) -> str:
        return (
            "Thank you for your response. You explained your reasoning clearly. "
            f"Next question: Walk me through a realistic {topic} scenario and how you would handle it."
        )

    def _safe_parse_json_object(self, raw: str) -> Optional[dict]:
        if not raw:
            return None

        text = raw.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

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

    async def _run_llm(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        top_k: int,
        min_p: float,
        presence_penalty: float,
        repetition_penalty: float,
        max_tokens: int,
        model: Optional[str] = None,
        use_scoring_lock: bool = False,
    ) -> str:
        """Run one LLM call under a lock to avoid model concurrency pressure.
        
        Args:
            use_scoring_lock: If True, uses scoring_lock (background). Otherwise uses inference_lock (real-time).
        """
        lock = self.scoring_lock if use_scoring_lock else self.inference_lock
        async with lock:
            response = await self.circuit_breaker.call(
                self.llm.chat,
                messages,
                stream=False,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                min_p=min_p,
                presence_penalty=presence_penalty,
                repetition_penalty=repetition_penalty,
                max_tokens=max_tokens,
                model=model,
            )

        return response if isinstance(response, str) else ""

    async def _parse_or_repair_structured(self, raw: str, topic: str) -> InterviewTurnResponse:
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
            {"role": "user", "content": f"Repair this to valid JSON without changing intent:\n{raw}"},
        ]

        repaired = await self._run_llm(
            repair_messages,
            temperature=0.0,
            top_p=1.0,
            top_k=20,
            min_p=0.0,
            presence_penalty=0.0,
            repetition_penalty=1.0,
            max_tokens=220,
            model=settings.OLLAMA_MODEL,
        )

        repaired_dict = self._safe_parse_json_object(repaired)
        if repaired_dict:
            try:
                return InterviewTurnResponse.model_validate(repaired_dict)
            except Exception:
                pass

        return InterviewTurnResponse(
            acknowledgement="Thank you for your response.",
            feedback_short="You communicated your thinking clearly.",
            next_question=f"Could you describe a practical {topic} challenge and your approach?",
        )

    def _format_client_reply(self, structured: InterviewTurnResponse) -> str:
        parts = [
            structured.acknowledgement.strip(),
            structured.feedback_short.strip(),
            f"Next question: {structured.next_question.strip()}",
        ]
        return " ".join(p for p in parts if p)

    def _extract_competencies(self, topic: str, job_description: Optional[str]) -> list[str]:
        """Derive a compact competency list used for on-track guardrails."""
        seed = {
            "python",
            "apis",
            "testing",
            "debugging",
            "sql",
            "communication",
            "problem solving",
            "system design",
            "ownership",
        }
        extracted: list[str] = [topic.lower()]

        if job_description:
            jd_lower = job_description.lower()
            for token in seed:
                if token in jd_lower:
                    extracted.append(token)

        # Preserve order while removing duplicates.
        seen: set[str] = set()
        ordered = []
        for item in extracted:
            if item and item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered[:12]

    def _make_summary(self, messages: list[dict[str, str]]) -> str:
        """Build lightweight rolling summary from older turns without extra model calls."""
        convo = [m for m in messages if m.get("role") != "system"]
        if len(convo) <= settings.INTERVIEW_CONTEXT_MESSAGES:
            return ""

        older = convo[: -settings.INTERVIEW_CONTEXT_MESSAGES]
        snippets: list[str] = []
        for message in older[-8:]:
            role = message.get("role", "user")
            content = message.get("content", "").strip().replace("\n", " ")
            if not content:
                continue
            snippets.append(f"{role}: {content[:150]}")

        return " | ".join(snippets)[:1200]

    def _needs_behavioral_reminder(self, metrics: Optional[dict], state: dict[str, Any]) -> bool:
        if not metrics:
            return False

        eye_contact = float(metrics.get("eye_contact_score", 1.0) or 1.0)
        if eye_contact >= 0.3:
            return False

        reminders_used = int(state.get("eye_contact_reminders", 0))
        if reminders_used >= settings.MAX_EYE_CONTACT_REMINDERS:
            return False

        now = time.time()
        last_ts = float(state.get("last_reminder_ts", 0.0) or 0.0)
        return (now - last_ts) >= float(settings.REMINDER_COOLDOWN_SEC)

    def _build_behavior_note(self, metrics: Optional[dict], state: dict[str, Any]) -> str:
        if not self._needs_behavioral_reminder(metrics, state):
            return ""

        state["eye_contact_reminders"] = int(state.get("eye_contact_reminders", 0)) + 1
        state["last_reminder_ts"] = time.time()
        return "[Policy note: Gently remind the candidate to maintain eye contact in this turn.]"

    def _is_on_track(self, response_text: str, topic: str, competencies: list[str]) -> bool:
        if not response_text:
            return False

        text = response_text.lower()
        checks = [topic.lower()] + competencies[:6]
        return any(token and token in text for token in checks)

    async def _maybe_regenerate_on_track(
        self,
        response: str,
        messages: list[dict[str, str]],
        topic: str,
        competencies: list[str],
    ) -> str:
        """If output drifts from role/JD, retry once with explicit grounding."""
        if self._is_on_track(response, topic, competencies):
            return response

        stricter = messages + [
            {
                "role": "system",
                "content": (
                    "Your previous draft drifted from the target role. Regenerate and stay strictly on the "
                    "job description competencies and interview topic."
                ),
            }
        ]
        bounded = self._bounded_messages(stricter, settings.INTERVIEW_CONTEXT_MESSAGES)
        retry = await self._run_llm(
            bounded,
            temperature=settings.INTERVIEW_TEMPERATURE,
            top_p=settings.INTERVIEW_TOP_P,
            top_k=settings.INTERVIEW_TOP_K,
            min_p=settings.INTERVIEW_MIN_P,
            presence_penalty=settings.INTERVIEW_PRESENCE_PENALTY,
            repetition_penalty=settings.INTERVIEW_REPETITION_PENALTY,
            max_tokens=settings.INTERVIEW_MAX_NEW_TOKENS,
            model=settings.OLLAMA_MODEL,
        )
        return retry or response

    async def start_session(
        self,
        session_id: str,
        persona: str,
        difficulty: str,
        topic: str,
        job_description: Optional[str] = None,
        resume_context: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Initialize a new interview session and return opening prompt."""
        async with self.sessions_lock:
            if session_id in self.sessions:
                logger.warning("Session %s already exists. Overwriting.", session_id)

            safe_instructions = ""
            if custom_instructions:
                safe_instructions = self._sanitize_prompt(custom_instructions)
                if safe_instructions != custom_instructions:
                    logger.warning("Sanitized custom instructions for session %s", session_id)

            competencies = self._extract_competencies(topic, job_description)
            system_prompt = self._build_system_prompt(
                persona,
                difficulty,
                topic,
                job_description,
                competencies,
                resume_context,
                safe_instructions,
            )
            self.sessions[session_id] = [{"role": "system", "content": system_prompt}]
            self.session_state[session_id] = {
                "topic": topic,
                "job_description": job_description or "",
                "competencies": competencies,
                "eye_contact_reminders": 0,
                "last_reminder_ts": 0.0,
                "rolling_summary": "",
            }

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

        bounded = self._bounded_messages(opening_msg, settings.INTERVIEW_CONTEXT_MESSAGES)
        response = await self._run_llm(
            bounded,
            temperature=settings.INTERVIEW_TEMPERATURE,
            top_p=settings.INTERVIEW_TOP_P,
            top_k=settings.INTERVIEW_TOP_K,
            min_p=settings.INTERVIEW_MIN_P,
            presence_penalty=settings.INTERVIEW_PRESENCE_PENALTY,
            repetition_penalty=settings.INTERVIEW_REPETITION_PENALTY,
            max_tokens=settings.INTERVIEW_MAX_NEW_TOKENS,
            model=settings.OLLAMA_MODEL,
        )

        if not response:
            response = self._build_plain_fallback(topic)

        if settings.LLM_JSON_MODE:
            structured = await self._parse_or_repair_structured(response, topic)
            formatted = self._format_client_reply(structured)
        else:
            formatted = response.strip() or self._build_plain_fallback(topic)

        async with self.sessions_lock:
            self.sessions[session_id].append({"role": "assistant", "content": formatted})

        return formatted

    async def restore_session_state(
        self,
        session_id: str,
        persona: str,
        difficulty: str,
        topic: str,
        job_description: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        resume_context: Optional[str] = None,
    ) -> None:
        """Restore session history/state for reconnect paths after process restart."""
        safe_history = history or []
        normalized_history: list[dict[str, str]] = []

        for message in safe_history:
            role = (message or {}).get("role")
            content = (message or {}).get("content", "")
            if role not in {"user", "assistant"}:
                continue
            normalized_history.append({"role": role, "content": str(content)})

        competencies = self._extract_competencies(topic, job_description)
        system_prompt = self._build_system_prompt(
            persona,
            difficulty,
            topic,
            job_description,
            competencies,
            resume_context,  # Phase 4: Include resume in restored system prompt
            custom_instructions=None,
        )

        async with self.sessions_lock:
            self.sessions[session_id] = [{"role": "system", "content": system_prompt}] + normalized_history
            self.session_state[session_id] = {
                "topic": topic,
                "job_description": job_description or "",
                "competencies": competencies,
                "eye_contact_reminders": 0,
                "last_reminder_ts": 0.0,
                "rolling_summary": self._make_summary(self.sessions[session_id]),
            }

    async def process_turn(self, session_id: str, user_input: str, metrics: Optional[dict] = None) -> str:
        """Process a single interview turn."""
        async with self.sessions_lock:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} not found")

            state = self.session_state.get(session_id, {})
            behavior_note = self._build_behavior_note(metrics, state)
            enhanced_input = self._inject_feedback(user_input, metrics)
            if behavior_note:
                enhanced_input = f"{behavior_note}\n\n{enhanced_input}"

            self.sessions[session_id].append({"role": "user", "content": enhanced_input})
            summary = self._make_summary(self.sessions[session_id])
            if summary:
                state["rolling_summary"] = summary
            messages = self.sessions[session_id].copy()
            state_snapshot = dict(state)

        if state_snapshot.get("rolling_summary"):
            messages.insert(
                1,
                {
                    "role": "system",
                    "content": (
                        "Session memory summary from earlier turns for continuity:\n"
                        f"{state_snapshot['rolling_summary']}"
                    ),
                },
            )
        if settings.LLM_JSON_MODE:
            messages.append({"role": "system", "content": self._structured_response_prompt()})

        bounded = self._bounded_messages(messages, settings.INTERVIEW_CONTEXT_MESSAGES)
        response = await self._run_llm(
            bounded,
            temperature=settings.INTERVIEW_TEMPERATURE,
            top_p=settings.INTERVIEW_TOP_P,
            top_k=settings.INTERVIEW_TOP_K,
            min_p=settings.INTERVIEW_MIN_P,
            presence_penalty=settings.INTERVIEW_PRESENCE_PENALTY,
            repetition_penalty=settings.INTERVIEW_REPETITION_PENALTY,
            max_tokens=settings.INTERVIEW_MAX_NEW_TOKENS,
            model=settings.OLLAMA_MODEL,
        )

        if not response:
            response = self._build_plain_fallback(state_snapshot.get("topic", "interview"))

        response = await self._maybe_regenerate_on_track(
            response,
            bounded,
            state_snapshot.get("topic", "interview"),
            state_snapshot.get("competencies", []),
        )

        if settings.LLM_JSON_MODE:
            structured = await self._parse_or_repair_structured(response, state_snapshot.get("topic", "interview"))
            formatted = self._format_client_reply(structured)
        else:
            formatted = response.strip() or self._build_plain_fallback("interview")

        async with self.sessions_lock:
            if session_id not in self.sessions:
                raise SessionNotFoundError(f"Session {session_id} was removed during processing")
            self.sessions[session_id].append({"role": "assistant", "content": formatted})

        return formatted

    async def score_turn(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Score one user turn using enriched evidence and competency-based rubric."""
        # Extract enriched context
        competencies = evidence.get("expected_competencies", [])
        comp_str = ", ".join(competencies[:6]) if competencies else "general interview skills"
        
        speech_metrics = evidence.get("speech_metrics", {})
        wpm = speech_metrics.get("wpm")
        speech_ratio = speech_metrics.get("speech_ratio")
        
        # Build pace/delivery notes
        pace_note = ""
        if wpm is not None:
            if wpm < 100:
                pace_note = f"Candidate spoke slowly ({wpm} WPM). "
            elif wpm > 200:
                pace_note = f"Candidate spoke very fast ({wpm} WPM). "
        if speech_ratio is not None and speech_ratio < 0.4:
            pace_note += "Long silences detected — possible hesitation."
        if not pace_note:
            pace_note = "Normal pace."
        
        schema_prompt = (
            "Return strict JSON only. Keys: rating (1-100), feedback (2 sentences max, specific to THIS answer), "
            "improved_answer (rewrite candidate's answer better), competency_scores (object, each key from the "
            "competency list, value 1-100), communication_notes (1 sentence on delivery)."
        )
        
        context = (
            f"Job: {evidence.get('job_description', 'Not specified')[:500]}\n"
            f"Topic: {evidence.get('topic')}\n"
            f"Difficulty: {evidence.get('difficulty')}\n"
            f"Competencies to score: {comp_str}\n"
            f"Question asked: {evidence.get('previous_question', 'Not available')}\n"
            f"Candidate answer: {evidence.get('user_text', '')}\n"
            f"Delivery notes: {pace_note}"
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an interview scoring assistant. Score using only the provided evidence and job description. "
                    "Evaluate against the specific competencies listed. Focus on technical accuracy, clarity, and relevance. "
                    "Do not invent missing facts."
                ),
            },
            {"role": "system", "content": schema_prompt},
            {"role": "user", "content": context},
        ]

        bounded = self._bounded_messages(messages, settings.SCORING_CONTEXT_MESSAGES)
        model_name = settings.OLLAMA_SCORING_MODEL or settings.OLLAMA_MODEL
        raw = await self._run_llm(
            bounded,
            temperature=settings.SCORING_TEMPERATURE,
            top_p=settings.SCORING_TOP_P,
            top_k=settings.SCORING_TOP_K,
            min_p=settings.SCORING_MIN_P,
            presence_penalty=settings.SCORING_PRESENCE_PENALTY,
            repetition_penalty=settings.SCORING_REPETITION_PENALTY,
            max_tokens=settings.SCORING_MAX_NEW_TOKENS,
            model=model_name,
            use_scoring_lock=True,  # Use separate lock to avoid blocking live interviews
        )

        parsed = self._safe_parse_json_object(raw)
        if not parsed:
            return {
                "rating": 70,
                "feedback": "Answer captured. Add one concrete example and clearer impact metrics.",
                "improved_answer": evidence.get("user_text", ""),
                "competency_scores": {},
            }

        return {
            "rating": int(parsed.get("rating", 70)),
            "feedback": str(parsed.get("feedback", ""))[:1000],
            "improved_answer": str(parsed.get("improved_answer", ""))[:2000],
            "competency_scores": parsed.get("competency_scores", {}),
        }

    def _build_system_prompt(
        self,
        persona: str,
        difficulty: str,
        topic: str,
        job_description: Optional[str],
        competencies: list[str],
        resume_context: Optional[str],
        custom_instructions: Optional[str],
    ) -> str:
        base_prompt = f"""You are conducting an interview with the following parameters:
- Persona: {persona}
- Difficulty: {difficulty}
- Topic: {topic}

CRITICAL INSTRUCTIONS:
1. Ask ONE question at a time.
2. Keep the interview tightly grounded to the role and job description.
3. Provide useful, professional feedback with natural tone.
4. If behavioral policy notes appear in user context, follow them exactly for that turn.
5. Keep the interview coherent across turns and adapt to candidate responses.
"""

        if competencies:
            base_prompt += "\nCore competencies to evaluate:\n- " + "\n- ".join(competencies[:10]) + "\n"

        if job_description:
            base_prompt += f"\nJOB DESCRIPTION:\n{job_description[:2500]}\n"

        if resume_context:
            base_prompt += f"\nRESUME CONTEXT:\n{resume_context[:1000]}\n"

        if custom_instructions:
            base_prompt += f"\nCUSTOM INSTRUCTIONS:\n{custom_instructions}\n"

        return base_prompt

    def _inject_feedback(self, user_input: str, metrics: Optional[dict]) -> str:
        if not metrics:
            return user_input

        feedback_notes = []
        eye_contact = metrics.get("eye_contact_score", 1.0)
        if eye_contact < 0.3:
            feedback_notes.append(f"[Candidate looking away from camera - eye contact: {eye_contact:.0%}]")

        fidget_score = metrics.get("fidget_score", 0)
        if fidget_score > 5.0:
            feedback_notes.append("[Excessive head movement detected]")

        if metrics.get("is_stressed"):
            feedback_notes.append("[Stress indicators detected - furrowed brows]")

        if feedback_notes:
            return f"{' '.join(feedback_notes)}\n\nCandidate's answer: \"{user_input}\""
        return user_input

    async def close(self):
        """Cleanup resources."""
        if self._owns_llm:
            await self.llm.close()
