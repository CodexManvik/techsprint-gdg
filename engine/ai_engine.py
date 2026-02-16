import os
import json
from google import genai
from engine.difficulty import get_difficulty_prompt
from engine.personas import get_persona_prompt

class AIEngine:
    api_call_count = 0

    def __init__(self, require_google=False):
        """
        Initialize AI Engine.
        
        Args:
            require_google: If True, raises error when Google API key is missing.
                           If False, allows initialization without Google (for Ollama backend).
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            if require_google:
                raise ValueError("CRITICAL: GOOGLE_API_KEY not found.")
            else:
                print("ℹ️ Google API key not found - AIEngine will not be available")
                print("   Using Ollama backend instead")
                self.client = None
                self.model_id = None
                self.chat = None
                return
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-flash-latest" 
        self.chat = None

    def reset_session(self, style="FAANG_Architect", difficulty="Intermediate", topic="System Design", resume_context=None, custom_instructions=None):
        """Initializes the AI with the specific persona, difficulty, and topic."""
        try:
            AIEngine.api_call_count += 1
            print(f"🔢 API Call #{AIEngine.api_call_count} - reset_session")
            print(f"🎯 Initializing AI with:")
            print(f"   - Persona: {style}")
            print(f"   - Difficulty: {difficulty}")
            print(f"   - Topic: {topic}")
            
            if custom_instructions:
                print("✅ Using CUSTOM instructions")
                persona_prompt = custom_instructions
            else:
                persona_prompt = get_persona_prompt(style)
                print(f"✅ Persona prompt loaded: {persona_prompt[:100]}...")
            
            difficulty_prompt = get_difficulty_prompt(difficulty)
            print(f"✅ Difficulty prompt loaded: {difficulty_prompt[:100]}...")
            
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

            self.chat = self.client.chats.create(
                model=self.model_id,
                config={"system_instruction": base_instructions}
            )
            print(f"✅ AI Initialized: {style} | {difficulty} | {topic}")
            
            # Generate an opening question based on the context
            init_response = self.chat.send_message(f"Start the interview. Ask the first question about {topic}.")
            return init_response.text

        except Exception as e:
            print(f"⚠️ AI Init Warning: {e}")
            self.chat = self.client.chats.create(model=self.model_id)
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
        response = self.chat.send_message(prompt)
        return response.text

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
            print(f"🔧 DEV MODE: Mock feedback report")
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
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Report Gen Error: {e}")
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
