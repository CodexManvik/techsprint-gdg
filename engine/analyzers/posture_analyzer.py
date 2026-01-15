"""
Posture Analysis Module for Interview Mirror.

Analyzes body posture including:
- Shoulder alignment (leaning detection)
- Slouch detection (spine position)
- Arms crossed detection
- Body stability (rocking/fidgeting)
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, List
from collections import deque


@dataclass
class Landmark:
    """Single landmark point with normalized coordinates."""
    x: float  # Normalized 0.0-1.0
    y: float  # Normalized 0.0-1.0
    z: float  # Depth (relative scale)
    visibility: float  # Confidence 0.0-1.0


@dataclass
class PostureMetrics:
    """
    Comprehensive posture analysis results.
    
    All metrics are calculated from pose landmarks (33 points).
    """
    shoulder_angle: float  # Degrees from horizontal (0 = level)
    is_leaning: bool  # True if angle > threshold
    is_slouching: bool  # True if nose too close to shoulders
    slouch_score: float  # 0.0-1.0 severity (0 = perfect, 1 = severe slouch)
    arms_crossed: bool  # True if wrists crossed in front
    rocking_score: float  # Horizontal instability (0 = stable)
    shoulder_stability: float  # 0.0-1.0 (1.0 = perfectly stable)
    timestamp: float


class PostureAnalyzer:
    """
    Analyzes body posture from pose landmarks.
    
    Uses MediaPipe Pose landmarks (33 points) to detect:
    - Shoulder alignment and leaning
    - Slouching (nose-to-shoulder distance)
    - Arms crossed position
    - Body rocking and stability
    """
    
    # Pose landmark indices (MediaPipe Pose)
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    
    def __init__(self, 
                 shoulder_angle_threshold: float = 15.0,
                 slouch_threshold: float = 0.05,  # More sensitive (was 0.1)
                 rock_threshold: float = 0.02,
                 history_size: int = 30,
                 arms_crossed_frames: int = 10):
        """
        Initialize posture analysis with configurable thresholds.
        
        Args:
            shoulder_angle_threshold: Max shoulder tilt in degrees before flagging lean
            slouch_threshold: Vertical distance change for slouch detection (lower = more sensitive)
            rock_threshold: Horizontal movement threshold for rocking detection
            history_size: Number of frames to track for stability analysis
            arms_crossed_frames: Consecutive frames needed to confirm arms crossed (default 10 = ~0.6s at 16fps)
        """
        self.shoulder_angle_threshold = shoulder_angle_threshold
        self.slouch_threshold = slouch_threshold
        self.rock_threshold = rock_threshold
        self.arms_crossed_frames = arms_crossed_frames
        
        # History buffers for temporal analysis
        self.shoulder_history = deque(maxlen=history_size)
        self.baseline_nose_shoulder_dist: Optional[float] = None
        self.arms_crossed_history = deque(maxlen=arms_crossed_frames)
        
        print(f"✅ PostureAnalyzer initialized (angle_threshold={shoulder_angle_threshold}°, "
              f"slouch_threshold={slouch_threshold}, rock_threshold={rock_threshold})")
    
    def _calculate_shoulder_angle(self, 
                                  left_shoulder: Landmark, 
                                  right_shoulder: Landmark) -> float:
        """
        Calculate the angle of the line between shoulders from horizontal.
        
        Returns the deviation from horizontal (0 degrees = level shoulders).
        Positive angles indicate the right shoulder is higher, negative means left is higher.
        
        Args:
            left_shoulder: Left shoulder landmark
            right_shoulder: Right shoulder landmark
            
        Returns:
            Angle in degrees from horizontal (-90 to +90)
        """
        dx = right_shoulder.x - left_shoulder.x
        dy = right_shoulder.y - left_shoulder.y
        
        # Calculate angle in radians, then convert to degrees
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to -90 to +90 range (deviation from horizontal)
        # atan2 gives us -180 to +180, but shoulders should be roughly horizontal
        # So angles near 180 or -180 are actually close to 0 (horizontal)
        if angle_deg > 90:
            angle_deg = 180 - angle_deg
        elif angle_deg < -90:
            angle_deg = -180 - angle_deg
        
        return float(angle_deg)
    def _detect_slouch(
        self,
        nose: Landmark,
        shoulders: Tuple[Landmark, Landmark]
    ) -> Tuple[bool, float]:
        """
        Slouch detection calibrated for SEATED interview posture.
        
        Uses adaptive baseline: learns your upright sitting position,
        then detects when you slouch forward from that baseline.
        """
        left_shoulder, right_shoulder = shoulders

        shoulder_width = abs(right_shoulder.x - left_shoulder.x)
        if shoulder_width < 0.01:
            return False, 0.0

        shoulder_avg_y = (left_shoulder.y + right_shoulder.y) / 2.0
        vertical_dist = shoulder_avg_y - nose.y
        normalized_dist = vertical_dist / shoulder_width

        # Establish baseline on first few frames (adaptive calibration)
        if self.baseline_nose_shoulder_dist is None:
            self.baseline_nose_shoulder_dist = normalized_dist
            return False, 0.0
        
        # For seated posture, we expect nose to be closer to shoulders than standing
        # Typical seated upright: 0.5-0.8 ratio
        # Slouching: ratio decreases (nose gets even closer to shoulders)
        
        # Calculate deviation from baseline
        deviation = self.baseline_nose_shoulder_dist - normalized_dist
        
        # Slouching means nose moves DOWN (closer to shoulders)
        # So deviation will be POSITIVE when slouching
        
        if deviation <= 0:
            # Not slouching (actually sitting more upright than baseline)
            return False, 0.0
        
        # Slouch threshold: 15% decrease from baseline is noticeable slouch
        slouch_threshold = 0.15
        slouch_score = min(1.0, deviation / slouch_threshold)
        
        # Flag as slouching if score > 0.5 (about 7.5% decrease from baseline)
        is_slouching = slouch_score > 0.5

        return is_slouching, float(slouch_score)

    
    def _detect_arms_crossed(
        self,
        left_wrist: Landmark,
        right_wrist: Landmark,
        left_elbow: Landmark,
        right_elbow: Landmark,
        left_shoulder: Landmark,
        right_shoulder: Landmark,
        left_hip: Landmark,
        right_hip: Landmark
    ) -> bool:
        """
        Robust arms-crossed detection using spatial relationships.
        
        Logic:
        1. Check if wrists are closer to OPPOSITE shoulders than same-side shoulders
        2. Verify wrists are near chest center (not extended outward)
        3. Ensure wrists are above hips (prevents false positives from relaxed hands)
        
        Uses temporal smoothing to prevent flickering.
        """
        
        # Visibility check
        if (left_wrist.visibility < 0.5 or 
            right_wrist.visibility < 0.5 or
            left_shoulder.visibility < 0.5 or
            right_shoulder.visibility < 0.5):
            self.arms_crossed_history.append(False)
            return False
        
        # Calculate shoulder center
        shoulder_cx = (left_shoulder.x + right_shoulder.x) / 2.0
        shoulder_cy = (left_shoulder.y + right_shoulder.y) / 2.0
        
        # Hip Y coordinate (for vertical validation)
        hip_y = (left_hip.y + right_hip.y) / 2.0
        
        # Distance helper function
        def dist(a: Landmark, b: Landmark) -> float:
            return math.hypot(a.x - b.x, a.y - b.y)
        
        # Key signal: distances to opposite shoulders vs same-side shoulders
        lw_to_rs = dist(left_wrist, right_shoulder)  # Left wrist to RIGHT shoulder
        rw_to_ls = dist(right_wrist, left_shoulder)  # Right wrist to LEFT shoulder
        lw_to_ls = dist(left_wrist, left_shoulder)   # Left wrist to LEFT shoulder
        rw_to_rs = dist(right_wrist, right_shoulder) # Right wrist to RIGHT shoulder
        
        # Wrists close to chest center (not extended outward)
        lw_center_dist = math.hypot(left_wrist.x - shoulder_cx, left_wrist.y - shoulder_cy)
        rw_center_dist = math.hypot(right_wrist.x - shoulder_cx, right_wrist.y - shoulder_cy)
        wrists_inward = (lw_center_dist < 0.25 and rw_center_dist < 0.25)
        
        # Wrists above hips (prevents relaxed hand false positives)
        wrists_up = (left_wrist.y < hip_y and right_wrist.y < hip_y)
        
        # Core crossed-arm condition:
        # Each wrist is closer to the OPPOSITE shoulder than its own shoulder
        crossed = (
            lw_to_rs < lw_to_ls and  # Left wrist closer to right shoulder
            rw_to_ls < rw_to_rs and  # Right wrist closer to left shoulder
            wrists_inward and        # Wrists near chest
            wrists_up                # Wrists elevated
        )
        
        # Add to history for temporal smoothing
        self.arms_crossed_history.append(crossed)
        
        # Need enough frames to make a decision
        if len(self.arms_crossed_history) < self.arms_crossed_frames:
            return False
        
        # Return True if majority of recent frames show crossed
        crossed_count = sum(self.arms_crossed_history)
        return crossed_count >= (self.arms_crossed_frames * 0.7)  # 70% threshold

    
    def _detect_rocking(self, shoulders: Tuple[Landmark, Landmark]) -> Tuple[float, float]:
        """
        Calculate rocking/fidgeting score from shoulder movement.
        
        Tracks horizontal movement of shoulders over time to detect
        side-to-side rocking or instability.
        
        Args:
            shoulders: Tuple of (left_shoulder, right_shoulder)
            
        Returns:
            Tuple of (rocking_score, shoulder_stability)
        """
        left_shoulder, right_shoulder = shoulders
        
        # Calculate shoulder midpoint X position
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2.0
        
        # Add to history
        self.shoulder_history.append(shoulder_mid_x)
        
        # Need at least 10 frames for meaningful analysis
        if len(self.shoulder_history) < 10:
            return 0.0, 1.0
        
        # Calculate standard deviation of shoulder position (jitter)
        positions = list(self.shoulder_history)
        mean_x = sum(positions) / len(positions)
        variance = sum((x - mean_x) ** 2 for x in positions) / len(positions)
        std_dev = math.sqrt(variance)
        
        # Rocking score: normalized standard deviation
        # Typical stable sitting has std_dev < 0.01
        rocking_score = min(1.0, std_dev / self.rock_threshold)
        
        # Stability score: inverse of rocking (1.0 = perfectly stable)
        shoulder_stability = max(0.0, 1.0 - rocking_score)
        
        return float(rocking_score), float(shoulder_stability)
    
    def analyze(self, 
                pose_landmarks: Optional[List[Landmark]],
                timestamp: float) -> PostureMetrics:
        """
        Perform complete posture analysis on pose landmarks.
        
        Args:
            pose_landmarks: List of 33 pose landmarks (or None if not detected)
            timestamp: Current timestamp in seconds
            
        Returns:
            PostureMetrics with all posture indicators
        """
        # Default metrics if no pose detected
        if pose_landmarks is None or len(pose_landmarks) < 25:
            return PostureMetrics(
                shoulder_angle=0.0,
                is_leaning=False,
                is_slouching=False,
                slouch_score=0.0,
                arms_crossed=False,
                rocking_score=0.0,
                shoulder_stability=1.0,
                timestamp=timestamp
            )
        
        # Extract key landmarks
        nose = pose_landmarks[self.NOSE]
        left_shoulder = pose_landmarks[self.LEFT_SHOULDER]
        right_shoulder = pose_landmarks[self.RIGHT_SHOULDER]
        left_elbow = pose_landmarks[self.LEFT_ELBOW]
        right_elbow = pose_landmarks[self.RIGHT_ELBOW]
        left_wrist = pose_landmarks[self.LEFT_WRIST]
        right_wrist = pose_landmarks[self.RIGHT_WRIST]
        
        # 1. Calculate shoulder angle
        shoulder_angle = self._calculate_shoulder_angle(left_shoulder, right_shoulder)
        is_leaning = abs(shoulder_angle) > self.shoulder_angle_threshold
        
        # 2. Detect slouching
        is_slouching, slouch_score = self._detect_slouch(nose, (left_shoulder, right_shoulder))
        
        # 3. Detect arms crossed
        left_hip = pose_landmarks[self.LEFT_HIP]
        right_hip = pose_landmarks[self.RIGHT_HIP]

        arms_crossed = self._detect_arms_crossed(
            left_wrist,
            right_wrist,
            left_elbow,
            right_elbow,
            left_shoulder,
            right_shoulder,
            left_hip,
            right_hip
        )

        
        # 4. Detect rocking/stability
        rocking_score, shoulder_stability = self._detect_rocking((left_shoulder, right_shoulder))
        
        return PostureMetrics(
            shoulder_angle=shoulder_angle,
            is_leaning=is_leaning,
            is_slouching=is_slouching,
            slouch_score=slouch_score,
            arms_crossed=arms_crossed,
            rocking_score=rocking_score,
            shoulder_stability=shoulder_stability,
            timestamp=timestamp
        )
    
    def reset(self):
        """Reset analyzer state (history buffers and baselines)."""
        self.shoulder_history.clear()
        self.arms_crossed_history.clear()
        self.baseline_nose_shoulder_dist = None
        print("✅ PostureAnalyzer state reset")
    
    def get_session_summary(self) -> dict:
        """
        Get comprehensive session summary for posture analysis.
        
        Returns:
            Dictionary with session-wide posture metrics
        """
        # Calculate average shoulder stability
        avg_stability = 1.0
        if len(self.shoulder_history) > 0:
            positions = list(self.shoulder_history)
            mean_x = sum(positions) / len(positions)
            variance = sum((x - mean_x) ** 2 for x in positions) / len(positions)
            std_dev = math.sqrt(variance)
            rocking_score = min(1.0, std_dev / self.rock_threshold)
            avg_stability = max(0.0, 1.0 - rocking_score)
        
        # Calculate arms crossed percentage
        arms_crossed_frames = sum(self.arms_crossed_history) if self.arms_crossed_history else 0
        total_frames = len(self.arms_crossed_history) if self.arms_crossed_history else 1
        arms_crossed_percentage = (arms_crossed_frames / total_frames) * 100
        
        return {
            "frames_analyzed": total_frames,
            "average_shoulder_stability": avg_stability,
            "arms_crossed_percentage": arms_crossed_percentage,
            "arms_crossed_frames": arms_crossed_frames,
            "shoulder_movement_samples": len(self.shoulder_history),
            "baseline_established": self.baseline_nose_shoulder_dist is not None
        }
