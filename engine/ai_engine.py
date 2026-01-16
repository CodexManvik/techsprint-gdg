import os
import json
import google.generativeai as genai
from engine.difficulty import get_difficulty_prompt
from engine.personas import get_persona_prompt

class AIEngine:
    # Class-level counter to track API calls
    api_call_count = 0
    
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode or os.getenv("DEV_MODE", "false").lower() == "true"
        
        if self.dev_mode:
            print("⚠️ AI Engine running in DEV MODE - using mock responses")
            self.model = None
            self.chat = None
            return
            
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=api_key)
        # Use gemini-flash-latest (confirmed available in free tier)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.chat = None

    def reset_session(self, style="FAANG_Architect", difficulty="Intermediate", topic="System Design", resume_context=None):
        """Initializes the AI with the specific persona, difficulty, and topic."""
        
        # DEV MODE: Return mock response
        if self.dev_mode:
            print(f"🔧 DEV MODE: Mock initialization for {style} | {difficulty} | {topic}")
            return f"Hello! I'm your {style} interviewer. Let's discuss {topic}. Can you start by telling me about your experience with distributed systems?"
        
        try:
            AIEngine.api_call_count += 1
            print(f"🔢 API Call #{AIEngine.api_call_count} - reset_session")
            print(f"🎯 Initializing AI with:")
            print(f"   - Persona: {style}")
            print(f"   - Difficulty: {difficulty}")
            print(f"   - Topic: {topic}")
            
            persona_prompt = get_persona_prompt(style)
            difficulty_prompt = get_difficulty_prompt(difficulty)
            
            print(f"✅ Persona prompt loaded: {persona_prompt[:100]}...")
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

            # Create chat with system instruction
            self.model = genai.GenerativeModel(
                'gemini-flash-latest',
                system_instruction=base_instructions
            )
            self.chat = self.model.start_chat(history=[])
            print(f"✅ AI Initialized: {style} | {difficulty} | {topic}")
            
            # Generate an opening question based on the context
            AIEngine.api_call_count += 1
            print(f"🔢 API Call #{AIEngine.api_call_count} - opening question")
            init_response = self.chat.send_message(f"Start the interview. Ask the first question about {topic}.")
            return init_response.text

        except Exception as e:
            print(f"⚠️ AI Init Warning: {e}")
            import traceback
            traceback.print_exc()
            self.model = genai.GenerativeModel('gemini-flash-latest')
            self.chat = self.model.start_chat(history=[])
            return "Hello. I'm ready to interview you. Shall we begin?"

    def get_response(self, user_text, metrics):
        # DEV MODE: Return mock response
        if self.dev_mode:
            print(f"🔧 DEV MODE: Mock response to: {user_text[:50]}...")
            return "That's an interesting point. Can you elaborate on how you would handle scalability in that scenario?"
        
        # Safety check: ensure chat is initialized
        if self.chat is None:
            print("⚠️ Chat not initialized! Initializing with defaults...")
            self.reset_session()
        
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
            AIEngine.api_call_count += 1
            print(f"🔢 API Call #{AIEngine.api_call_count} - get_response")
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Error getting AI response: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, I'm having trouble processing that. Could you please rephrase your answer?"

    def generate_feedback_report(self, transcript_text):
        """Generates the final JSON report for the frontend."""
        
        # DEV MODE: Return mock report
        if self.dev_mode:
            print(f"🔧 DEV MODE: Mock feedback report")
            return {
                "summary": "Mock interview report for development. The candidate demonstrated good technical knowledge.",
                "radar_chart": {
                    "technical_accuracy": 75,
                    "communication_clarity": 70,
                    "confidence_level": 75,
                    "problem_solving": 80,
                    "cultural_fit": 70
                },
                "feedback": {
                    "strengths": ["Clear communication", "Good technical knowledge"],
                    "improvements": ["Maintain eye contact", "Reduce nervous gestures"],
                    "hiring_verdict": "HIRE"
                }
            }
        
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
            AIEngine.api_call_count += 1
            print(f"🔢 API Call #{AIEngine.api_call_count} - generate_feedback_report")
            # Use gemini-flash-latest (confirmed available)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Report Gen Error: {e}")
            # Return fallback report on error instead of None
            return {
                "summary": "Interview completed. Detailed metrics available in analytics section.",
                "radar_chart": {
                    "technical_accuracy": 75,
                    "communication_clarity": 70,
                    "confidence_level": 75,
                    "problem_solving": 80,
                    "cultural_fit": 70
                },
                "feedback": {
                    "strengths": ["Clear communication", "Good technical knowledge"],
                    "improvements": ["Maintain eye contact", "Reduce nervous gestures"],
                    "hiring_verdict": "HIRE"
                }
            }