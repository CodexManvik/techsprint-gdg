from google import genai
import os

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GOOGLE_API_KEY not found.")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-flash-latest" # Updated to a stable model name
        self.chat = None
        self.reset_session()

    def reset_session(self):
        """Clears history for a new user."""
        self.system_context = """
        You are an elite Recruitment Officer from Dell. 
        Conduct a technical interview.
        Keep your responses concise (under 2 sentences) unless asked for an explanation.
        """
        self.chat = self.client.chats.create(model=self.model_id)
        self.chat.send_message(self.system_context)

    def load_resume(self, resume_text):
        print(f"📄 Loading Resume ({len(resume_text)} chars)...")
        prompt = f"""
        CONTEXT UPDATE: Here is the candidate's resume. 
        Base your future technical questions on the skills and projects listed here.
        
        RESUME TEXT:
        {resume_text}
        
        Start by asking a question specifically about one of their projects.
        """
        response = self.chat.send_message(prompt)
        return response.text

    def get_response(self, user_text, metrics):
        prompt = f"""
        [Behavioral Metrics]
        - Eye Contact: {metrics.get('eye_contact_score', 'N/A')}
        - Fidgeting: {metrics.get('fidget_score', 0)}
        - Smiling: {metrics.get('is_smiling', False)}
        
        Candidate Answer: "{user_text}"
        
        INSTRUCTIONS:
        1. If eye contact is bad (<0.5), gently mention it in your reply.
        2. Keep the conversation moving.
        """
        
        response = self.chat.send_message(prompt)
        return response.text