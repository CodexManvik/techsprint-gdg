import os
import json
from google import genai
from engine.difficulty import get_difficulty_prompt
from engine.personas import get_persona_prompt

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GOOGLE_API_KEY not found.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-flash-latest" 
        self.chat = None

    def reset_session(self, style="FAANG_Architect", difficulty="Intermediate", topic="System Design", resume_context=None):
        """Initializes the AI with the specific persona, difficulty, and topic."""
        try:
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

    def generate_feedback_report(self, transcript_text):
        """Generates the final JSON report for the frontend."""
        prompt = f"""
        Analyze this interview transcript and return a JSON object.
        
        TRANSCRIPT:
        {transcript_text}
        
        REQUIRED JSON FORMAT:
        {{
            "radar_chart": {{
                "technical_accuracy": <0-100>,
                "communication_clarity": <0-100>,
                "confidence_level": <0-100>,
                "problem_solving": <0-100>,
                "cultural_fit": <0-100>
            }},
            "feedback": {{
                "strengths": ["point 1", "point 2"],
                "improvements": ["point 1", "point 2"],
                "hiring_verdict": "HIRE" | "NO HIRE" | "STRONG HIRE"
            }},
            "summary": "A 2-sentence summary of the candidate's performance."
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
            return None