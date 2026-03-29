import time
import json

class InterviewSession:
    def __init__(self, session_id, company_focus="General", difficulty="Medium", topic="General", job_description=""):
        self.id = session_id
        self.start_time = time.time()
        self.company_focus = company_focus
        self.difficulty = difficulty
        self.topic = topic
        self.job_description = job_description or ""
        
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
        """Return both summarized and raw analytics consumed by reports/charts."""
        def _avg(values):
            if not values:
                return 0.0
            return float(sum(values) / len(values))

        avg_eye_contact = _avg(self.history["eye_contact_scores"])
        avg_wpm = _avg(self.history["wpm_scores"])
        avg_stress = _avg(self.history["stress_flags"])

        # Approximate posture confidence from inverse fidget score on a 0..1 scale.
        posture_samples = [max(0.0, min(1.0, 1.0 - (float(v) / 10.0))) for v in self.history["fidget_scores"]]
        posture_avg = _avg(posture_samples)

        return {
            "duration": round(time.time() - self.start_time),
            "avg_wpm": avg_wpm,
            "avg_eye_contact": avg_eye_contact,
            "posture_avg": posture_avg,
            "avg_stress": avg_stress,
            "history": self.history,
            "transcript_text": "\n".join([f"{t['role'].upper()}: {t['content']}" for t in self.transcript])
        }