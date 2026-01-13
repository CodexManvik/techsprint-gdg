import numpy as np
from collections import deque

class VisionEngine:
    def __init__(self):
        # Tracks the last 20 frames of the nose tip to calculate jitter/fidgeting
        self.nose_history = deque(maxlen=20)
        
        # We need a slightly longer history to detect slow gestures like nodding
        self.gesture_history = deque(maxlen=30) 

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

    def analyze_frame(self, landmarks):
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
                "is_stressed": bool(is_stressed or eye_contact_score < 0.4)
            }

        except Exception as e:
            # Fallback for safety
            return {
                "error": str(e), 
                "eye_contact_score": 0.5, 
                "fidget_score": 0.0, 
                "head_gesture": "neutral",
                "is_smiling": False,
                "is_stressed": False
            }