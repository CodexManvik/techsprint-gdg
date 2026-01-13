from google import genai
import os

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GOOGLE_API_KEY not found.")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-flash-latest" # Use 1.5 Flash for faster document reading
        
        # Initialize chat
        self.chat = self.client.chats.create(model=self.model_id)
        
        # Base System Prompt
        self.system_context = """
        You are an elite Recruitment Officer from Dell. 
        Conduct a technical interview.
        """
        # Seed the chat with the system context immediately
        self.chat.send_message(self.system_context)

    def load_resume(self, resume_text):
        """
        Feeds the resume to Gemini so it can ask specific questions.
        """
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
        # Construct the behavioral prompt
        # We add "User said: " to make it clear who is talking
        prompt = f"""
        [Behavioral Metrics from Webcam]
        - Eye Contact: {metrics.get('eye_contact_score', 'N/A')} (Goal: >0.6)
        - Fidgeting: {metrics.get('fidget_score', 0)} (Goal: <5.0)
        - Smiling: {metrics.get('is_smiling', False)}
        
        Candidate Answer: "{user_text}"
        
        INSTRUCTIONS:
        1. If the answer is short, ask for more details.
        2. If eye contact is bad (<0.5), gently mention it in your reply.
        3. Keep the conversation moving.
        """
        
        response = self.chat.send_message(prompt)
        return response.text