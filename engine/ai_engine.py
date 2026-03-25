import os
import json
import logging
import httpx
from engine.difficulty import get_difficulty_prompt
from engine.personas import get_persona_prompt


logger = logging.getLogger(__name__)

class AIEngine:
    api_call_count = 0

    def __init__(self, require_google=False):
        """Initialize local-only AI engine backed by Ollama."""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_id = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
        self.client = httpx.Client(base_url=self.base_url, timeout=20.0)
        self.messages = []
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"

        if require_google:
            logger.warning("require_google flag is ignored; AIEngine is Ollama-only")

    def _safe_json_parse(self, text: str) -> dict | None:
        if not text:
            return None
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start : end + 1])
                    return parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    return None
            return None

    def _chat_once(self, messages: list[dict], *, json_mode: bool = False) -> str:
        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.9,
                "num_predict": 256 if json_mode else 128,
            },
        }
        if json_mode:
            payload["format"] = "json"

        response = self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        message = data.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(data.get("response"), str):
            return data["response"]
        return ""

    def reset_session(self, style="FAANG_Architect", difficulty="Intermediate", topic="System Design", resume_context=None, custom_instructions=None):
        """Initializes the AI with the specific persona, difficulty, and topic."""
        try:
            AIEngine.api_call_count += 1
            logger.info(
                "AI reset session call=%s persona=%s difficulty=%s topic=%s",
                AIEngine.api_call_count,
                style,
                difficulty,
                topic,
            )
            
            if custom_instructions:
                persona_prompt = custom_instructions
            else:
                persona_prompt = get_persona_prompt(style)
            
            difficulty_prompt = get_difficulty_prompt(difficulty)
            
            base_instructions = (
                f"{persona_prompt}\n\n"
                f"{difficulty_prompt}\n\n"
                f"The specific interview topic is: {topic}.\n"
                "You are conducting a live video interview. "
                "Keep responses concise (1-3 sentences) to allow for back-and-forth conversation. "
                "Do not write long paragraphs."
            )

            if resume_context:
                base_instructions += f"\n\nRESUME CONTEXT: {resume_context}"

            self.messages = [{"role": "system", "content": base_instructions}]

            opening = self._chat_once(
                self.messages
                + [{"role": "user", "content": f"Start the interview. Ask the first question about {topic}."}],
                json_mode=False,
            )
            self.messages.append({"role": "assistant", "content": opening})
            logger.info("AI initialized successfully")
            return opening or "Hello. I am ready to begin the interview."

        except Exception as e:
            logger.warning("AI init warning: %s", e)
            self.messages = [{"role": "system", "content": "You are conducting a professional interview."}]
            return "Hello. I'm ready to interview you. Shall we begin?"

    def get_response(self, user_text, metrics):
        # We inject behavioral data so the AI can react to it (e.g., "You seem nervous")
        prompt = f"""
        [Real-time Metrics]
        - Eye Contact: {metrics.get('eye_contact_score', 0):.2f} (Target: >0.6)
        - Smiling: {metrics.get('is_smiling', False)}
        
        Candidate Answer: "{user_text}"
        
        Instructions:
        1. Respond to the answer relevantly.
        2. If eye contact is consistently low (<0.4), briefly mention it in a supportive way *once*.
        """
        try:
            self.messages.append({"role": "user", "content": prompt})
            response_text = self._chat_once(self.messages, json_mode=False)
            self.messages.append({"role": "assistant", "content": response_text})
            return response_text
        except Exception as e:
            logger.error("AI response generation failed: %s", e)
            return "Thank you for your answer. Could you elaborate with one concrete example?"

    def generate_feedback_report(self, chat_history):
        """Generates the final JSON report for the frontend with per-message analysis."""
        
        # Prepare transcript for the prompt
        transcript_text = ""
        user_message_ids = []
        for msg in chat_history:
            role = msg['role'].upper()
            content = msg['content']
            transcript_text += f"[{msg['id']}] {role}: {content}\n"
            if msg['role'] == 'user':
                user_message_ids.append(msg['id'])
        
        # DEV MODE: Return mock report
        if self.dev_mode:
            logger.info("DEV MODE: mock feedback report")
            detailed_analysis = []
            for msg_id in user_message_ids:
                detailed_analysis.append({
                    "id": msg_id,
                    "rating": 75,
                    "feedback": "[DEV MODE] Mock feedback",
                    "improved_answer": "[DEV MODE] Mock improved answer"
                })
            return {
                "summary": "[DEV MODE] Mock Interview Summary",
                "overall_score": 75,
                "radar_chart": {
                    "technical_accuracy": 75,
                    "communication_clarity": 75,
                    "confidence_level": 75,
                    "problem_solving": 75,
                    "cultural_fit": 75
                },
                "detailed_analysis": detailed_analysis
            }
        
        # REAL AI REPORT
        prompt = f"""
Based on the following interview transcript, generate a comprehensive JSON report.

IMPORTANT:
1. For "detailed_analysis", include an entry for EVERY user message ID shown.
2. Each entry must have: "id" (the message ID number), "rating" (1-100), "feedback" (2 sentences), "improved_answer" (better version).

TRANSCRIPT:
{transcript_text}

Expected JSON format:
{{
  "summary": "Overall interview assessment (2-3 sentences)",
  "overall_score": 75,
  "radar_chart": {{
    "technical_accuracy": 75,
    "communication_clarity": 75,
    "confidence_level": 75,
    "problem_solving": 75,
    "cultural_fit": 75
  }},
  "detailed_analysis": [
    {{"id": 1, "rating": 80, "feedback": "...", "improved_answer": "..."}},
    {{"id": 2, "rating": 70, "feedback": "...", "improved_answer": "..."}}
  ]
}}
"""
        
        try:
            response_text = self._chat_once(
                [
                    {
                        "role": "system",
                        "content": "Return strict JSON only and no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                json_mode=True,
            )
            parsed = self._safe_json_parse(response_text)
            if parsed:
                return parsed
            raise ValueError("Invalid JSON report payload from Ollama")
        except Exception as e:
            logger.error("Report generation error: %s", e)
            # Return fallback report on error
            return {
                "summary": "Interview completed. Detailed metrics available in analytics section.",
                "overall_score": 70,
                "radar_chart": {
                    "technical_accuracy": 70,
                    "communication_clarity": 70,
                    "confidence_level": 70,
                    "problem_solving": 70,
                    "cultural_fit": 70
                },
                "detailed_analysis": []
            }

    def close(self):
        """Cleanup local HTTP client."""
        try:
            self.client.close()
        except Exception:
            pass
