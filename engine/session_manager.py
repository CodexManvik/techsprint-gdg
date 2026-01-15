import time
import json

class InterviewSession:
    def __init__(self, session_id, company_focus="General", difficulty="Medium", topic="General"):
        self.id = session_id
        self.start_time = time.time()
        self.company_focus = company_focus
        self.difficulty = difficulty
        self.topic = topic
        
        self.transcript = [] 
        
        # Analytics History
        self.history = {
            "timestamps": [],
            "fidget_scores": [],
            "eye_contact_scores": [],
            "wpm_scores": [], # Added WPM tracking
            "stress_flags": []
        }

    def log_interaction(self, user_text, ai_reply):
        self.transcript.append({"role": "user", "content": user_text})
        self.transcript.append({"role": "ai", "content": ai_reply})

    def log_vision_metrics(self, metrics):
        elapsed = round(time.time() - self.start_time, 1)
        self.history["timestamps"].append(elapsed)
        self.history["fidget_scores"].append(metrics.get("fidget_score", 0))
        self.history["eye_contact_scores"].append(metrics.get("eye_contact_score", 0))
        self.history["stress_flags"].append(1 if metrics.get("is_stressed") else 0)

    def log_audio_metrics(self, audio_analysis):
        # We can log WPM (Pace) here if available
        if "wpm" in audio_analysis:
             self.history["wpm_scores"].append(audio_analysis["wpm"])

    def get_analytics(self):
        """Returns raw data for the frontend to render graphs."""
        return {
            "duration": round(time.time() - self.start_time),
            "history": self.history,
            "transcript_text": "\n".join([f"{t['role'].upper()}: {t['content']}" for t in self.transcript])
        }