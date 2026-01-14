import time
import json

class InterviewSession:
    def __init__(self, session_id):
        self.id = session_id
        self.start_time = time.time()
        self.transcript = []  # Stores: {"role": "user", "text": "..."}
        
        # This will store the data for the graphs later
        self.history = {
            "timestamps": [],
            "fidget_scores": [],
            "eye_contact_scores": [],
            "stress_flags": []
        }

    def log_interaction(self, user_text, ai_reply):
        """Saves what was said."""
        self.transcript.append({"role": "user", "content": user_text})
        self.transcript.append({"role": "ai", "content": ai_reply})

    def log_vision_metrics(self, metrics):
        """Saves how the candidate looked at this specific second."""
        elapsed = round(time.time() - self.start_time, 1)
        
        self.history["timestamps"].append(elapsed)
        self.history["fidget_scores"].append(metrics.get("fidget_score", 0))
        self.history["eye_contact_scores"].append(metrics.get("eye_contact_score", 0))
        self.history["stress_flags"].append(1 if metrics.get("is_stressed") else 0)

    def get_report_card(self):
        """Calculates the final score when the interview ends."""
        if not self.history["eye_contact_scores"]:
            return {"score": 0, "feedback": "No data recorded."}

        # 1. Math Analysis
        avg_eye = sum(self.history["eye_contact_scores"]) / len(self.history["eye_contact_scores"])
        avg_fidget = sum(self.history["fidget_scores"]) / len(self.history["fidget_scores"])
        
        # 2. Simple Rule-Based Feedback (Placeholder for now)
        strengths = []
        weaknesses = []
        
        if avg_eye > 0.7: strengths.append("Great eye contact!")
        else: weaknesses.append("Look at the camera more often.")
        
        if avg_fidget < 5.0: strengths.append("You sat very still.")
        else: weaknesses.append("You were fidgeting a lot.")

        return {
            "duration_sec": round(time.time() - self.start_time),
            "overall_score": int(avg_eye * 100),
            "analytics": self.history,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "full_transcript": self.transcript
        }