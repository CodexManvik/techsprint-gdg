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
        
        # Analytics History - Basic metrics
        self.history = {
            "timestamps": [],
            "fidget_scores": [],
            "eye_contact_scores": [],
            "wpm_scores": [],
            "stress_flags": []
        }
        
        # NEW: Detailed metrics tracking
        self.detailed_metrics = {
            # Posture metrics over time
            "posture": {
                "shoulder_angles": [],
                "slouch_scores": [],
                "arms_crossed_frames": [],
                "rocking_scores": [],
                "shoulder_stability": [],
            },
            # Stress metrics over time
            "stress": {
                "blink_rates": [],
                "blink_counts": [],
                "lip_pursing_events": [],
                "stress_levels": [],  # "low", "moderate", "high"
                "ear_values": [],  # Eye aspect ratio
            },
            # Integrity metrics over time
            "integrity": {
                "gaze_positions": [],  # (x, y) tuples
                "cheat_flags": [],
                "integrity_scores": [],
                "suspicious_events": [],
            },
            # Behavioral metrics
            "behavioral": {
                "head_gestures": [],  # nodding, shaking, neutral
                "smile_events": [],
                "high_cognitive_load_frames": [],
            }
        }

    def log_interaction(self, user_text, ai_reply):
        self.transcript.append({"role": "user", "content": user_text})
        self.transcript.append({"role": "ai", "content": ai_reply})

    def log_vision_metrics(self, metrics):
        """Log comprehensive vision metrics from vision engine."""
        elapsed = round(time.time() - self.start_time, 1)
        self.history["timestamps"].append(elapsed)
        self.history["fidget_scores"].append(metrics.get("fidget_score", 0))
        self.history["eye_contact_scores"].append(metrics.get("eye_contact_score", 0))
        self.history["stress_flags"].append(1 if metrics.get("is_stressed") else 0)
        
        # NEW: Log detailed posture metrics
        if "posture" in metrics:
            posture = metrics["posture"]
            self.detailed_metrics["posture"]["shoulder_angles"].append(posture.get("shoulder_angle", 0))
            self.detailed_metrics["posture"]["slouch_scores"].append(posture.get("slouch_score", 0))
            self.detailed_metrics["posture"]["arms_crossed_frames"].append(1 if posture.get("arms_crossed") else 0)
            self.detailed_metrics["posture"]["rocking_scores"].append(posture.get("rocking_score", 0))
            self.detailed_metrics["posture"]["shoulder_stability"].append(posture.get("shoulder_stability", 1.0))
        
        # NEW: Log detailed stress metrics
        if "stress" in metrics:
            stress = metrics["stress"]
            self.detailed_metrics["stress"]["blink_rates"].append(stress.get("blink_rate", 0))
            self.detailed_metrics["stress"]["blink_counts"].append(stress.get("blink_count", 0))
            if stress.get("lip_pursing"):
                self.detailed_metrics["stress"]["lip_pursing_events"].append({
                    "timestamp": elapsed,
                    "duration": stress.get("lip_purse_duration", 0)
                })
            self.detailed_metrics["stress"]["stress_levels"].append(stress.get("stress_level", "low"))
            self.detailed_metrics["stress"]["ear_values"].append(stress.get("average_ear", 0.5))
        
        # NEW: Log detailed integrity metrics
        if "integrity" in metrics:
            integrity = metrics["integrity"]
            self.detailed_metrics["integrity"]["gaze_positions"].append((
                integrity.get("gaze_x", 0.5),
                integrity.get("gaze_y", 0.5)
            ))
            self.detailed_metrics["integrity"]["cheat_flags"].append(integrity.get("cheat_flag_count", 0))
            self.detailed_metrics["integrity"]["integrity_scores"].append(integrity.get("integrity_score", 1.0))
            if integrity.get("integrity_warning"):
                self.detailed_metrics["integrity"]["suspicious_events"].append({
                    "timestamp": elapsed,
                    "gaze_cluster": integrity.get("gaze_cluster_id"),
                    "cheat_flags": integrity.get("cheat_flag_count", 0)
                })
        
        # NEW: Log behavioral metrics
        self.detailed_metrics["behavioral"]["head_gestures"].append(metrics.get("head_gesture", "neutral"))
        if metrics.get("is_smiling"):
            self.detailed_metrics["behavioral"]["smile_events"].append(elapsed)
        if metrics.get("stress", {}).get("high_cognitive_load"):
            self.detailed_metrics["behavioral"]["high_cognitive_load_frames"].append(elapsed)

    def log_audio_metrics(self, audio_analysis):
        # We can log WPM (Pace) here if available
        if "wpm" in audio_analysis:
             self.history["wpm_scores"].append(audio_analysis["wpm"])

    def get_analytics(self):
        """Returns computed analytics for the frontend."""
        duration = round(time.time() - self.start_time)
        
        # Compute averages from basic metrics
        avg_eye_contact = sum(self.history["eye_contact_scores"]) / len(self.history["eye_contact_scores"]) if self.history["eye_contact_scores"] else 0
        avg_fidget = sum(self.history["fidget_scores"]) / len(self.history["fidget_scores"]) if self.history["fidget_scores"] else 0
        avg_stress = sum(self.history["stress_flags"]) / len(self.history["stress_flags"]) if self.history["stress_flags"] else 0
        avg_wpm = sum(self.history["wpm_scores"]) / len(self.history["wpm_scores"]) if self.history["wpm_scores"] else 0
        
        # Compute posture average (inverse of fidget)
        posture_avg = 1.0 - avg_fidget if avg_fidget > 0 else 0.75
        
        # NEW: Compute detailed posture metrics
        posture_metrics = self._compute_posture_analytics()
        stress_metrics = self._compute_stress_analytics()
        integrity_metrics = self._compute_integrity_analytics()
        behavioral_metrics = self._compute_behavioral_analytics()
        
        # Compute derived scores (0-100 scale)
        technical_score = 75  # Placeholder - would need NLP analysis
        communication_score = min(100, max(0, 70 + (avg_wpm - 130) / 2)) if avg_wpm > 0 else 70
        confidence_score = min(100, avg_eye_contact * 100)
        problem_solving = 80  # Placeholder
        
        # Integrity events (times when eye contact dropped significantly)
        integrity_events = []
        for i, score in enumerate(self.history["eye_contact_scores"]):
            if score < 0.3:  # Low eye contact threshold
                integrity_events.append({
                    "timestamp": self.history["timestamps"][i] if i < len(self.history["timestamps"]) else i * 5,
                    "type": "gaze_away",
                    "duration": 2
                })
        
        # Add suspicious events from integrity checker
        integrity_events.extend(self.detailed_metrics["integrity"]["suspicious_events"])
        
        return {
            "duration": duration,
            "avg_wpm": avg_wpm,
            "avg_stress": avg_stress,
            "avg_eye_contact": avg_eye_contact,
            "posture_avg": posture_avg,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "confidence_score": confidence_score,
            "problem_solving": problem_solving,
            "integrity_events": integrity_events,
            "history": self.history,
            "transcript_text": "\n".join([f"{t['role'].upper()}: {t['content']}" for t in self.transcript]),
            "summary": f"Interview completed. Duration: {duration}s. Analyzed {len(self.transcript)} exchanges.",
            
            # NEW: Detailed metrics
            "detailed_posture": posture_metrics,
            "detailed_stress": stress_metrics,
            "detailed_integrity": integrity_metrics,
            "detailed_behavioral": behavioral_metrics,
        }
    
    def _compute_posture_analytics(self):
        """Compute comprehensive posture analytics."""
        posture = self.detailed_metrics["posture"]
        
        if not posture["shoulder_angles"]:
            return {
                "avg_shoulder_angle": 0,
                "avg_slouch_score": 0,
                "arms_crossed_percentage": 0,
                "avg_rocking_score": 0,
                "avg_shoulder_stability": 1.0,
                "posture_quality": "good"
            }
        
        avg_slouch = sum(posture["slouch_scores"]) / len(posture["slouch_scores"])
        arms_crossed_pct = (sum(posture["arms_crossed_frames"]) / len(posture["arms_crossed_frames"])) * 100
        avg_stability = sum(posture["shoulder_stability"]) / len(posture["shoulder_stability"])
        
        # Determine posture quality
        if avg_slouch < 0.3 and avg_stability > 0.7:
            quality = "excellent"
        elif avg_slouch < 0.5 and avg_stability > 0.5:
            quality = "good"
        elif avg_slouch < 0.7:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "avg_shoulder_angle": sum(posture["shoulder_angles"]) / len(posture["shoulder_angles"]),
            "avg_slouch_score": avg_slouch,
            "arms_crossed_percentage": arms_crossed_pct,
            "avg_rocking_score": sum(posture["rocking_scores"]) / len(posture["rocking_scores"]),
            "avg_shoulder_stability": avg_stability,
            "posture_quality": quality,
            "frames_analyzed": len(posture["shoulder_angles"])
        }
    
    def _compute_stress_analytics(self):
        """Compute comprehensive stress analytics."""
        stress = self.detailed_metrics["stress"]
        
        if not stress["blink_rates"]:
            return {
                "avg_blink_rate": 0,
                "total_blinks": 0,
                "high_cognitive_load_detected": False,
                "lip_pursing_count": 0,
                "max_lip_purse_duration": 0,
                "stress_assessment": "low",
                "avg_ear": 0.5
            }
        
        avg_blink_rate = sum(stress["blink_rates"]) / len(stress["blink_rates"])
        total_blinks = max(stress["blink_counts"]) if stress["blink_counts"] else 0
        
        # Count stress levels
        stress_level_counts = {"low": 0, "moderate": 0, "high": 0}
        for level in stress["stress_levels"]:
            stress_level_counts[level] = stress_level_counts.get(level, 0) + 1
        
        # Determine overall stress assessment
        if stress_level_counts["high"] > len(stress["stress_levels"]) * 0.3:
            assessment = "high"
        elif stress_level_counts["moderate"] > len(stress["stress_levels"]) * 0.4:
            assessment = "moderate"
        else:
            assessment = "low"
        
        max_lip_purse = max([e["duration"] for e in stress["lip_pursing_events"]], default=0)
        
        return {
            "avg_blink_rate": avg_blink_rate,
            "total_blinks": total_blinks,
            "high_cognitive_load_detected": avg_blink_rate > 30,
            "lip_pursing_count": len(stress["lip_pursing_events"]),
            "max_lip_purse_duration": max_lip_purse,
            "stress_assessment": assessment,
            "avg_ear": sum(stress["ear_values"]) / len(stress["ear_values"]) if stress["ear_values"] else 0.5
        }
    
    def _compute_integrity_analytics(self):
        """Compute comprehensive integrity analytics."""
        integrity = self.detailed_metrics["integrity"]
        
        if not integrity["integrity_scores"]:
            return {
                "avg_integrity_score": 1.0,
                "total_cheat_flags": 0,
                "suspicious_event_count": len(integrity["suspicious_events"]),
                "integrity_assessment": "clean",
                "gaze_dispersion": 0,
                "recommendations": []
            }
        
        avg_score = sum(integrity["integrity_scores"]) / len(integrity["integrity_scores"])
        total_flags = sum(integrity["cheat_flags"])
        
        # Calculate gaze dispersion (how much gaze moves around)
        if len(integrity["gaze_positions"]) > 1:
            gaze_x_values = [pos[0] for pos in integrity["gaze_positions"]]
            gaze_y_values = [pos[1] for pos in integrity["gaze_positions"]]
            import numpy as np
            gaze_dispersion = float(np.std(gaze_x_values) + np.std(gaze_y_values))
        else:
            gaze_dispersion = 0
        
        # Determine assessment
        if avg_score > 0.9 and total_flags == 0:
            assessment = "clean"
        elif avg_score > 0.7 and total_flags < 3:
            assessment = "good"
        elif avg_score > 0.5:
            assessment = "suspicious"
        else:
            assessment = "highly_suspicious"
        
        # Generate recommendations
        recommendations = []
        if total_flags > 5:
            recommendations.append("Multiple suspicious gaze patterns detected. Maintain eye contact with camera.")
        if gaze_dispersion > 0.3:
            recommendations.append("Gaze frequently moves away from screen. Focus on the interviewer.")
        if len(integrity["suspicious_events"]) > 3:
            recommendations.append("Several integrity warnings triggered. Ensure you're in a distraction-free environment.")
        
        return {
            "avg_integrity_score": avg_score,
            "total_cheat_flags": total_flags,
            "suspicious_event_count": len(integrity["suspicious_events"]),
            "integrity_assessment": assessment,
            "gaze_dispersion": gaze_dispersion,
            "recommendations": recommendations
        }
    
    def _compute_behavioral_analytics(self):
        """Compute behavioral analytics."""
        behavioral = self.detailed_metrics["behavioral"]
        
        # Count head gestures
        gesture_counts = {"nodding": 0, "shaking": 0, "neutral": 0}
        for gesture in behavioral["head_gestures"]:
            gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1
        
        return {
            "nodding_count": gesture_counts["nodding"],
            "shaking_count": gesture_counts["shaking"],
            "smile_count": len(behavioral["smile_events"]),
            "high_cognitive_load_frames": len(behavioral["high_cognitive_load_frames"]),
            "engagement_score": min(100, (gesture_counts["nodding"] + len(behavioral["smile_events"])) * 5)
        }
