import numpy as np
from collections import deque
import time

# Import our advanced vision components (Task 1-3)
from engine.holistic_processor import HolisticProcessor
from engine.signal_smoother import SignalSmoother
from engine.analyzers.posture_analyzer import PostureAnalyzer

class VisionEngine:
    def __init__(self):
        # Legacy tracking for backward compatibility
        self.nose_history = deque(maxlen=20)
        self.gesture_history = deque(maxlen=30)
        
        # NEW: Advanced vision components (Task 1-3)
        print("🚀 Initializing Advanced Vision System...")
        self.holistic_processor = HolisticProcessor()
        # Balanced smoothing for real-time feel
        self.signal_smoother = SignalSmoother(
            freq=15.0,           # Back to 15Hz for responsiveness
            min_cutoff=1.5,      # Moderate smoothing (was 3.0)
            beta=0.1,            # Some velocity adaptation
            d_cutoff=1.0
        )
        self.posture_analyzer = PostureAnalyzer()
        self.frame_count = 0
        self.last_valid_metrics = None  # Cache last valid result
        print("✅ Advanced Vision System Ready!") 

    def get_distance(self, p1, p2):
        """Euclidean distance between two landmarks."""
        def get_c(p, axis):
            return p[axis] if isinstance(p, dict) else getattr(p, axis)
        return float(np.sqrt((get_c(p1, 'x') - get_c(p2, 'x'))**2 + 
                       (get_c(p1, 'y') - get_c(p2, 'y'))**2))

    def detect_head_gesture(self):
        """
        Analyzes the gesture_history to detect 'nodding' (Yes) or 'shaking' (No).
        Returns: "nodding", "shaking", or "neutral"
        """
        if len(self.gesture_history) < 10:
            return "neutral"

        # Extract X and Y movements
        x_movements = [p[0] for p in self.gesture_history]
        y_movements = [p[1] for p in self.gesture_history]

        # Calculate the range of motion (Max - Min)
        x_range = max(x_movements) - min(x_movements)
        y_range = max(y_movements) - min(y_movements)

        # Thresholds (tuned for normalized coordinates 0.0-1.0)
        # You might need to tweak these based on camera sensitivity
        MOVEMENT_THRESHOLD = 0.03 
        DOMINANCE_RATIO = 1.5 # One axis must move much more than the other

        # Detect Nodding (Vertical movement dominates)
        if y_range > MOVEMENT_THRESHOLD and y_range > (x_range * DOMINANCE_RATIO):
            return "nodding"
        
        # Detect Shaking (Horizontal movement dominates)
        if x_range > MOVEMENT_THRESHOLD and x_range > (y_range * DOMINANCE_RATIO):
            return "shaking"

        return "neutral"

    def analyze_frame(self, landmarks_or_frame):
        """
        Enhanced frame analysis with backward compatibility.
        
        Can accept either:
        - landmarks dict (legacy mode - face only)
        - raw frame (new mode - full body holistic analysis)
        """
        # Detect if we're getting a raw frame or landmarks
        is_raw_frame = isinstance(landmarks_or_frame, np.ndarray)
        
        if is_raw_frame:
            # NEW MODE: Full holistic analysis with posture
            return self._analyze_holistic(landmarks_or_frame)
        else:
            # LEGACY MODE: Face-only analysis
            return self._analyze_legacy(landmarks_or_frame)
    
    def _analyze_holistic(self, frame):
        """NEW: Full-body holistic analysis with posture detection."""
        self.frame_count += 1
        timestamp = time.time()
        
        try:
            # Process frame with MediaPipe Holistic
            holistic_results = self.holistic_processor.process_frame(frame)
            
            if not holistic_results.pose_landmarks:
                # No pose detected - return last valid metrics if available
                if self.last_valid_metrics:
                    return self.last_valid_metrics
                return self._get_default_metrics()
            
            # Smooth ALL landmarks (pose, face, hands)
            smoothed_pose, smoothed_face, smoothed_left_hand, smoothed_right_hand = \
                self.signal_smoother.smooth_landmarks(
                    holistic_results.pose_landmarks,
                    holistic_results.face_landmarks,
                    holistic_results.left_hand_landmarks,
                    holistic_results.right_hand_landmarks,
                    timestamp
                )
            
            # Analyze posture (Task 3) - only needs pose landmarks
            posture_metrics = self.posture_analyzer.analyze(smoothed_pose, timestamp)
            
            # Legacy face analysis (if face landmarks available)
            legacy_metrics = {}
            if smoothed_face:
                # Convert smoothed landmarks to dict format for legacy code
                face_landmarks_dict = [
                    {'x': lm.x, 'y': lm.y, 'z': lm.z} 
                    for lm in smoothed_face
                ]
                legacy_metrics = self._analyze_legacy(face_landmarks_dict)
            elif holistic_results.face_landmarks:
                # Fallback to unsmoothed if smoothing failed
                legacy_metrics = self._analyze_legacy(holistic_results.face_landmarks)
            
            # Combine all metrics
            combined_metrics = {
                # Legacy metrics (backward compatible)
                "eye_contact_score": legacy_metrics.get("eye_contact_score", 0.5),
                "fidget_score": legacy_metrics.get("fidget_score", 0.0),
                "head_gesture": legacy_metrics.get("head_gesture", "neutral"),
                "is_smiling": legacy_metrics.get("is_smiling", False),
                "is_stressed": legacy_metrics.get("is_stressed", False),
                "stress_detected": legacy_metrics.get("stress_detected", False),
                
                # NEW: Posture metrics (Task 3)
                "posture": {
                    "shoulder_angle": posture_metrics.shoulder_angle,
                    "is_leaning": posture_metrics.is_leaning,
                    "is_slouching": posture_metrics.is_slouching,
                    "slouch_score": posture_metrics.slouch_score,
                    "arms_crossed": posture_metrics.arms_crossed,
                    "rocking_score": posture_metrics.rocking_score,
                    "shoulder_stability": posture_metrics.shoulder_stability,
                },
                
                # NEW: Pose landmarks for frontend visualization
                "pose_landmarks_for_drawing": [
                    {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                    for lm in smoothed_pose
                ] if smoothed_pose else None,
                
                # Meta
                "frame_number": self.frame_count,
                "timestamp": timestamp,
                "mode": "holistic"
            }
            
            # Cache this as last valid result
            self.last_valid_metrics = combined_metrics
            return combined_metrics
            
        except Exception as e:
            print(f"⚠️ Holistic analysis error: {e}")
            # Return last valid metrics if available, otherwise defaults
            if self.last_valid_metrics:
                return self.last_valid_metrics
            return self._get_default_metrics()
    
    def _analyze_legacy(self, landmarks):
        """LEGACY: Original face-only analysis for backward compatibility."""
        def get_coord(lm, axis):
            if isinstance(lm, dict): return lm[axis]
            return getattr(lm, axis)

        try:
            # --- 1. Eye Contact Analysis (Existing) ---
            left_inner_x = get_coord(landmarks[33], 'x')
            left_outer_x = get_coord(landmarks[133], 'x')
            eye_width = abs(left_inner_x - left_outer_x)
            if eye_width < 0.001: eye_width = 0.1 

            left_iris_x = get_coord(landmarks[468], 'x')
            eye_center_dist = abs(left_iris_x - ((left_inner_x + left_outer_x) / 2))
            eye_contact_score = float(round(max(0, 1.0 - (eye_center_dist / eye_width)), 2))

            # --- 2. Fidget Score & Gesture Tracking ---
            nose = landmarks[1]
            nose_x, nose_y = get_coord(nose, 'x'), get_coord(nose, 'y')
            
            self.nose_history.append((nose_x, nose_y))
            self.gesture_history.append((nose_x, nose_y))
            
            fidget_score = 0.0
            if len(self.nose_history) > 5:
                # Calculate standard deviation of movement (jitter)
                std_dev = np.std([p[0] for p in self.nose_history])
                fidget_score = float(round(std_dev * 100, 2))

            head_gesture = self.detect_head_gesture()

            # --- 3. Stress Proxy (Brow Distance) (Existing) ---
            brow_dist = self.get_distance(landmarks[55], landmarks[285])
            is_stressed = bool(brow_dist < 0.05) # Furrowed brows

            # --- 4. Emotion Detection (Smile) ---
            # Mouth corners: 61 (left), 291 (right)
            # Reference: Eye corners 33 and 263 to normalize for face distance
            mouth_width = self.get_distance(landmarks[61], landmarks[291])
            face_width = self.get_distance(landmarks[33], landmarks[263])
            
            # Ratio of mouth width to face width
            # Normal resting ratio is usually around 0.35 - 0.45
            smile_ratio = mouth_width / face_width if face_width > 0 else 0
            is_smiling = bool(smile_ratio > 0.55) # Threshold for a smile

            return {
                "eye_contact_score": eye_contact_score,
                "fidget_score": fidget_score,
                "head_gesture": head_gesture, # "nodding", "shaking", "neutral"
                "is_smiling": is_smiling,
                "stress_detected": is_stressed,
                "is_stressed": bool(is_stressed or eye_contact_score < 0.4),
                "mode": "legacy"
            }

        except Exception as e:
            # Fallback for safety
            return {
                "error": str(e), 
                "eye_contact_score": 0.5, 
                "fidget_score": 0.0, 
                "head_gesture": "neutral",
                "is_smiling": False,
                "is_stressed": False,
                "mode": "error"
            }
    
    def _get_default_metrics(self):
        """Return default metrics when no detection is possible."""
        return {
            "eye_contact_score": 0.5,
            "fidget_score": 0.0,
            "head_gesture": "neutral",
            "is_smiling": False,
            "is_stressed": False,
            "stress_detected": False,
            "posture": {
                "shoulder_angle": 0.0,
                "is_leaning": False,
                "is_slouching": False,
                "slouch_score": 0.0,
                "arms_crossed": False,
                "rocking_score": 0.0,
                "shoulder_stability": 1.0,
            },
            "frame_number": self.frame_count,
            "timestamp": time.time(),
            "mode": "default"
        }
    
    def release(self):
        """Release resources."""
        if hasattr(self, 'holistic_processor'):
            self.holistic_processor.release()
        print("✅ Vision Engine released")