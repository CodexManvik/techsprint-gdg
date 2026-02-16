"""
Cheating Detection Analyzer

Monitors vision metrics for integrity violations.
"""


class CheatingDetector:
    """Real-time cheating detection based on vision metrics"""
    
    def __init__(self):
        # Track violation history
        self.low_eye_contact_duration = 0
        self.face_lost_count = 0
        self.multiple_faces_count = 0
        
        # Thresholds
        self.EYE_CONTACT_THRESHOLD = 0.3
        self.LOW_EYE_CONTACT_LIMIT_SEC = 10
        
    def check_violations(self, metrics: dict, elapsed_sec: float) -> dict:
        """
        Analyze metrics for cheating indicators.
        
        Args:
            metrics: Vision analysis results
            elapsed_sec: Seconds since last check
            
        Returns:
            {
                "alert": str | None,
                "severity": "info" | "warning" | "critical"
            }
        """
        eye_contact = metrics.get("eye_contact_score", 1.0)
        
        # Track low eye contact duration
        if eye_contact < self.EYE_CONTACT_THRESHOLD:
            self.low_eye_contact_duration += elapsed_sec
        else:
            # Reset counter when eye contact improves
            self.low_eye_contact_duration = 0
        
        # Trigger alert if sustained low eye contact
        if self.low_eye_contact_duration >= self.LOW_EYE_CONTACT_LIMIT_SEC:
            self.low_eye_contact_duration = 0  # Reset after alert
            return {
                "alert": "📷 Please maintain eye contact with the camera.",
                "severity": "warning"
            }
        
        # Face detection (future implementation)
        # if metrics.get("face_count", 1) == 0:
        #     return {
        #         "alert": "❓ Are you still there?",
        #         "severity": "info"
        #     }
        
        # if metrics.get("face_count", 1) > 1:
        #     return {
        #         "alert": "⚠️ Multiple faces detected. Please ensure you're alone.",
        #         "severity": "critical"
        #     }
        
        return {"alert": None, "severity": "info"}
