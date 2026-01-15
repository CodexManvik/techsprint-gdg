"""
Stress Signal Detection Analyzer

This module implements stress indicator detection including:
- Eye Aspect Ratio (EAR) calculation for blink detection
- Blink rate monitoring for cognitive load assessment
- Lip compression detection for anxiety indicators

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import time
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple
from collections import deque


@dataclass
class StressMetrics:
    """Comprehensive stress analysis metrics for a single frame"""
    # Eye and blink metrics
    left_ear: float  # Eye Aspect Ratio for left eye
    right_ear: float  # Eye Aspect Ratio for right eye
    average_ear: float  # Average of both eyes
    blink_detected: bool  # True if blink detected this frame
    blink_count: int  # Cumulative blinks in session
    blink_rate: float  # Blinks per minute
    
    # Cognitive load indicators
    high_cognitive_load: bool  # True if blink rate > 30/min
    
    # Lip compression metrics
    lip_distance: float  # Distance between upper and lower lip
    lip_pursing: bool  # True if lips compressed while not speaking
    lip_purse_duration: float  # Seconds of sustained lip pursing
    
    # Overall stress assessment
    stress_level: str  # "low", "moderate", "high"
    
    # Processing metadata
    processing_time_ms: float
    timestamp: float


class StressAnalyzer:
    """
    Analyzes stress signals from facial landmarks including blink patterns
    and lip compression indicators.
    
    Uses Eye Aspect Ratio (EAR) formula for blink detection:
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Tracks blink rate and lip compression for stress assessment.
    """
    
    def __init__(self, 
                 ear_threshold: float = 0.2,
                 blink_rate_threshold: float = 30.0,  # blinks per minute
                 lip_compression_ratio: float = 0.7,  # Ratio of baseline for compression
                 lip_purse_duration_threshold: float = 2.0):  # seconds
        """
        Initialize stress analyzer with configurable thresholds.
        
        Args:
            ear_threshold: EAR value below which blink is detected
            blink_rate_threshold: Blinks per minute indicating high cognitive load
            lip_compression_ratio: Ratio of baseline lip opening indicating compression
            lip_purse_duration_threshold: Seconds of compression to flag pursing
        """
        # Thresholds
        self.ear_threshold = ear_threshold
        self.blink_rate_threshold = blink_rate_threshold
        self.lip_compression_ratio = lip_compression_ratio
        self.lip_purse_duration_threshold = lip_purse_duration_threshold
        
        # Blink tracking state
        self.blink_count = 0
        self.session_start_time = time.time()
        self.eye_state = "open"  # "open" or "closed" to prevent double counting
        self.blink_history = deque(maxlen=300)  # Last 10 seconds at 30fps
        
        # Distance-adaptive EAR tracking
        self.baseline_ear = None
        self.ear_calibration_frames = 0
        self.ear_calibration_sum = 0.0
        self.face_size_history = deque(maxlen=30)  # Track face size for distance estimation
        
        # Lip compression tracking with adaptive baseline
        self.lip_purse_start_time = None
        self.lip_purse_duration = 0.0
        self.lip_distance_history = deque(maxlen=90)  # Last 3 seconds at 30fps
        self.baseline_lip_distance = None
        self.lip_calibration_frames = 0
        self.lip_calibration_sum = 0.0
        
        # Performance tracking
        self.frame_count = 0
    
    def reset(self):
        """Reset analyzer state for new session"""
        self.blink_count = 0
        self.session_start_time = time.time()
        self.eye_state = "open"
        self.blink_history.clear()
        self.baseline_ear = None
        self.ear_calibration_frames = 0
        self.ear_calibration_sum = 0.0
        self.face_size_history.clear()
        self.lip_purse_start_time = None
        self.lip_purse_duration = 0.0
        self.lip_distance_history.clear()
        self.baseline_lip_distance = None
        self.lip_calibration_frames = 0
        self.lip_calibration_sum = 0.0
        self.frame_count = 0
    
    def _calculate_face_size(self, face_landmarks) -> float:
        """
        Calculate face size to estimate distance from camera.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            Face size metric (larger = closer to camera)
        """
        if not face_landmarks or len(face_landmarks) < 468:
            return 0.1  # Default small face size
        
        # Use face outline landmarks for size calculation
        # Face width: left temple to right temple
        left_temple = face_landmarks[234]   # Left temple
        right_temple = face_landmarks[454]  # Right temple
        face_width = abs(left_temple.x - right_temple.x)
        
        # Face height: forehead to chin
        forehead = face_landmarks[10]   # Forehead center
        chin = face_landmarks[152]      # Chin center  
        face_height = abs(forehead.y - chin.y)
        
        # Face size is the average of width and height
        face_size = (face_width + face_height) / 2.0
        
        # Track face size history for stability
        self.face_size_history.append(face_size)
        
        return face_size
    
    def _get_adaptive_ear_threshold(self, face_size: float) -> float:
        """
        Calculate adaptive EAR threshold based on face size (distance).
        
        Args:
            face_size: Current face size metric
            
        Returns:
            Adjusted EAR threshold for current distance
        """
        if len(self.face_size_history) < 5:
            return self.ear_threshold  # Use default until we have enough data
        
        # Calculate average face size
        avg_face_size = sum(self.face_size_history) / len(self.face_size_history)
        
        # Adjust threshold based on face size
        # Smaller face (farther away) = higher threshold (more sensitive)
        # Larger face (closer) = lower threshold (less sensitive)
        
        if avg_face_size < 0.15:  # Very far
            adjusted_threshold = self.ear_threshold * 1.4  # Much more sensitive
        elif avg_face_size < 0.25:  # Far
            adjusted_threshold = self.ear_threshold * 1.2  # More sensitive
        elif avg_face_size > 0.4:   # Very close
            adjusted_threshold = self.ear_threshold * 0.8  # Less sensitive
        elif avg_face_size > 0.3:   # Close
            adjusted_threshold = self.ear_threshold * 0.9  # Slightly less sensitive
        else:  # Normal distance
            adjusted_threshold = self.ear_threshold
        
        return adjusted_threshold
    
    def _calculate_ear(self, eye_landmarks: List[Tuple[float, float]]) -> float:
        """
        Calculate Eye Aspect Ratio using the standard formula.
        
        Args:
            eye_landmarks: List of (x, y) coordinates for eye landmarks
                          Expected order: [p1, p2, p3, p4, p5, p6]
                          where p1-p4 are horizontal, p2-p6 and p3-p5 are vertical
        
        Returns:
            Eye Aspect Ratio value
        """
        if len(eye_landmarks) < 6:
            return 0.5  # Default EAR when landmarks unavailable
        
        # Extract landmark coordinates
        p1, p2, p3, p4, p5, p6 = eye_landmarks[:6]
        
        # Calculate distances
        # Vertical distances
        dist_p2_p6 = math.sqrt((p2[0] - p6[0])**2 + (p2[1] - p6[1])**2)
        dist_p3_p5 = math.sqrt((p3[0] - p5[0])**2 + (p3[1] - p5[1])**2)
        
        # Horizontal distance
        dist_p1_p4 = math.sqrt((p1[0] - p4[0])**2 + (p1[1] - p4[1])**2)
        
        # Avoid division by zero
        if dist_p1_p4 == 0:
            return 0.5
        
        # EAR formula
        ear = (dist_p2_p6 + dist_p3_p5) / (2.0 * dist_p1_p4)
        return ear
    
    def _detect_blink_adaptive(self, average_ear: float, face_size: float) -> bool:
        """
        Detect blink using adaptive threshold based on face distance.
        
        Args:
            average_ear: Current frame's average EAR value
            face_size: Current face size for distance estimation
            
        Returns:
            True if new blink detected
        """
        current_time = time.time()
        blink_detected = False
        
        # Establish baseline EAR during first 60 frames
        if self.baseline_ear is None and self.ear_calibration_frames < 60:
            self.ear_calibration_frames += 1
            self.ear_calibration_sum += average_ear
            
            if self.ear_calibration_frames >= 60:
                self.baseline_ear = self.ear_calibration_sum / self.ear_calibration_frames
                print(f"👁️ EAR baseline established: {self.baseline_ear:.3f}")
            
            return False  # Don't detect blinks during calibration
        
        # Use adaptive threshold based on face size
        adaptive_threshold = self._get_adaptive_ear_threshold(face_size)
        
        # If we have a baseline, use relative threshold
        if self.baseline_ear is not None:
            # Blink when EAR drops to 60% of baseline or below adaptive threshold
            relative_threshold = self.baseline_ear * 0.6
            final_threshold = min(adaptive_threshold, relative_threshold)
        else:
            final_threshold = adaptive_threshold
        
        # State machine to prevent double counting
        if average_ear < final_threshold:
            # Eye is closed
            if self.eye_state == "open":
                # Transition from open to closed - new blink
                self.blink_count += 1
                self.blink_history.append(current_time)
                blink_detected = True
                self.eye_state = "closed"
        else:
            # Eye is open
            self.eye_state = "open"
        
        return blink_detected
        """
        Calculate Eye Aspect Ratio using the standard formula.
        
        Args:
            eye_landmarks: List of (x, y) coordinates for eye landmarks
                          Expected order: [p1, p2, p3, p4, p5, p6]
                          where p1-p4 are horizontal, p2-p6 and p3-p5 are vertical
        
        Returns:
            Eye Aspect Ratio value
        """
        if len(eye_landmarks) < 6:
            return 0.5  # Default EAR when landmarks unavailable
        
        # Extract landmark coordinates
        p1, p2, p3, p4, p5, p6 = eye_landmarks[:6]
        
        # Calculate distances
        # Vertical distances
        dist_p2_p6 = math.sqrt((p2[0] - p6[0])**2 + (p2[1] - p6[1])**2)
        dist_p3_p5 = math.sqrt((p3[0] - p5[0])**2 + (p3[1] - p5[1])**2)
        
        # Horizontal distance
        dist_p1_p4 = math.sqrt((p1[0] - p4[0])**2 + (p1[1] - p4[1])**2)
        
        # Avoid division by zero
        if dist_p1_p4 == 0:
            return 0.5
        
        # EAR formula
        ear = (dist_p2_p6 + dist_p3_p5) / (2.0 * dist_p1_p4)
        return ear
    
    def _detect_blink(self, average_ear: float) -> bool:
        """
        Detect blink based on EAR threshold and prevent double counting.
        
        Args:
            average_ear: Current frame's average EAR value
            
        Returns:
            True if new blink detected
        """
        current_time = time.time()
        blink_detected = False
        
        # State machine to prevent double counting
        if average_ear < self.ear_threshold:
            # Eye is closed
            if self.eye_state == "open":
                # Transition from open to closed - new blink
                self.blink_count += 1
                self.blink_history.append(current_time)
                blink_detected = True
                self.eye_state = "closed"
        else:
            # Eye is open
            self.eye_state = "open"
        
        return blink_detected
    
    def _calculate_blink_rate(self) -> float:
        """
        Calculate current blink rate in blinks per minute.
        
        Returns:
            Blinks per minute based on recent history
        """
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        if session_duration < 1.0:
            return 0.0  # Not enough data
        
        # Calculate rate from total session
        blinks_per_minute = (self.blink_count / session_duration) * 60.0
        return blinks_per_minute
    
    def _calculate_lip_distance(self, face_landmarks) -> float:
        """
        Calculate lip opening using multiple landmarks for better accuracy.
        
        Uses the lip contour area instead of just two points for more reliable detection.
        
        Args:
            face_landmarks: MediaPipe face landmarks (468 points)
            
        Returns:
            Lip opening ratio (0.0 = completely closed, higher = more open)
        """
        if not face_landmarks or len(face_landmarks) < 468:
            return 0.05  # Default moderate opening
        
        # Key lip landmarks for accurate measurement
        # Upper lip outline (left to right)
        upper_lip_points = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        # Lower lip outline (left to right) 
        lower_lip_points = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 324]
        
        # Inner lip landmarks for opening measurement
        upper_inner = [13, 82, 81, 80, 78]  # Upper inner lip
        lower_inner = [14, 87, 178, 88, 95]  # Lower inner lip
        
        # Calculate vertical distances at multiple points
        vertical_distances = []
        
        # Method 1: Inner lip vertical distances
        for i in range(min(len(upper_inner), len(lower_inner))):
            upper_point = face_landmarks[upper_inner[i]]
            lower_point = face_landmarks[lower_inner[i]]
            
            distance = abs(upper_point.y - lower_point.y)
            vertical_distances.append(distance)
        
        # Method 2: Center lip measurement (most reliable)
        # Upper lip center
        upper_center = face_landmarks[13]  # Cupid's bow center
        # Lower lip center  
        lower_center = face_landmarks[14]  # Lower lip center
        
        center_distance = abs(upper_center.y - lower_center.y)
        vertical_distances.append(center_distance * 2)  # Weight center more
        
        # Method 3: Lip corner measurements
        # Left corner
        left_upper = face_landmarks[61]   # Left upper corner
        left_lower = face_landmarks[84]   # Left lower corner
        left_distance = abs(left_upper.y - left_lower.y)
        
        # Right corner
        right_upper = face_landmarks[291]  # Right upper corner
        right_lower = face_landmarks[314]  # Right lower corner  
        right_distance = abs(right_upper.y - right_lower.y)
        
        vertical_distances.extend([left_distance, right_distance])
        
        # Calculate average opening with outlier removal
        if len(vertical_distances) > 2:
            # Remove extreme values
            vertical_distances.sort()
            # Remove top and bottom 20% to reduce noise
            trim_count = max(1, len(vertical_distances) // 5)
            trimmed_distances = vertical_distances[trim_count:-trim_count] if trim_count > 0 else vertical_distances
            
            average_opening = sum(trimmed_distances) / len(trimmed_distances)
        else:
            average_opening = sum(vertical_distances) / len(vertical_distances) if vertical_distances else 0.05
        
        return float(average_opening)
    
    def _detect_lip_pursing(self, lip_distance: float, is_speaking: bool) -> Tuple[bool, float]:
        """
        Detect sustained lip compression indicating anxiety using adaptive baseline.
        
        Args:
            lip_distance: Current frame's lip distance
            is_speaking: Whether user is currently speaking
            
        Returns:
            Tuple of (lip_pursing_detected, purse_duration)
        """
        current_time = time.time()
        self.lip_distance_history.append(lip_distance)
        
        # Don't detect lip pursing while speaking
        if is_speaking:
            self.lip_purse_start_time = None
            self.lip_purse_duration = 0.0
            return False, 0.0
        
        # Establish baseline during first 60 frames (2 seconds at 30fps)
        if self.baseline_lip_distance is None and self.lip_calibration_frames < 60:
            self.lip_calibration_frames += 1
            self.lip_calibration_sum += lip_distance
            
            if self.lip_calibration_frames >= 60:
                self.baseline_lip_distance = self.lip_calibration_sum / self.lip_calibration_frames
                print(f"📏 Lip baseline established: {self.baseline_lip_distance:.4f} (70% threshold: {self.baseline_lip_distance * 0.7:.4f})")
            
            # Don't detect pursing during calibration
            return False, 0.0
        
        # If no baseline established yet, use default threshold
        if self.baseline_lip_distance is None:
            compression_threshold = 0.015  # Conservative default
        else:
            # Use ratio of baseline (e.g., 60% of normal distance)
            compression_threshold = self.baseline_lip_distance * self.lip_compression_ratio
        
        # Check if lips are compressed relative to baseline
        lips_compressed = lip_distance < compression_threshold
        
        if lips_compressed:
            if self.lip_purse_start_time is None:
                # Start of lip pursing
                self.lip_purse_start_time = current_time
            else:
                # Ongoing lip pursing
                self.lip_purse_duration = current_time - self.lip_purse_start_time
        else:
            # Lips not compressed - reset
            self.lip_purse_start_time = None
            self.lip_purse_duration = 0.0
        
        # Flag lip pursing if sustained for threshold duration
        lip_pursing = self.lip_purse_duration >= self.lip_purse_duration_threshold
        
        return lip_pursing, self.lip_purse_duration
    
    def _classify_stress_level(self, blink_rate: float, lip_pursing: bool) -> str:
        """
        Classify overall stress level based on multiple indicators.
        
        Args:
            blink_rate: Current blinks per minute
            lip_pursing: Whether lip pursing is detected
            
        Returns:
            Stress level classification: "low", "moderate", "high"
        """
        stress_indicators = 0
        
        # High blink rate indicator
        if blink_rate > self.blink_rate_threshold:
            stress_indicators += 2  # Strong indicator
        elif blink_rate > self.blink_rate_threshold * 0.7:
            stress_indicators += 1  # Moderate indicator
        
        # Lip pursing indicator
        if lip_pursing:
            stress_indicators += 2  # Strong indicator
        
        # Classify based on total indicators
        if stress_indicators >= 3:
            return "high"
        elif stress_indicators >= 1:
            return "moderate"
        else:
            return "low"
    
    def analyze(self, face_landmarks, is_speaking: bool = False) -> StressMetrics:
        """
        Analyze stress signals from facial landmarks.
        
        Args:
            face_landmarks: MediaPipe face landmarks (468 points)
            is_speaking: Whether user is currently speaking
            
        Returns:
            StressMetrics with comprehensive stress analysis
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Default values for missing landmarks
        left_ear = right_ear = average_ear = 0.5
        blink_detected = False
        lip_distance = 0.05
        lip_pursing = False
        lip_purse_duration = 0.0
        
        if face_landmarks and len(face_landmarks) >= 468:
            # Extract eye landmarks for EAR calculation
            # Left eye landmarks (user's left eye)
            left_eye = [
                (face_landmarks[33].x, face_landmarks[33].y),  # p1 - left corner
                (face_landmarks[160].x, face_landmarks[160].y),  # p2 - top
                (face_landmarks[158].x, face_landmarks[158].y),  # p3 - top
                (face_landmarks[133].x, face_landmarks[133].y),  # p4 - right corner
                (face_landmarks[153].x, face_landmarks[153].y),  # p5 - bottom
                (face_landmarks[144].x, face_landmarks[144].y),  # p6 - bottom
            ]
            
            # Right eye landmarks (user's right eye)
            right_eye = [
                (face_landmarks[362].x, face_landmarks[362].y),  # p1 - right corner
                (face_landmarks[387].x, face_landmarks[387].y),  # p2 - top
                (face_landmarks[385].x, face_landmarks[385].y),  # p3 - top
                (face_landmarks[263].x, face_landmarks[263].y),  # p4 - left corner
                (face_landmarks[380].x, face_landmarks[380].y),  # p5 - bottom
                (face_landmarks[373].x, face_landmarks[373].y),  # p6 - bottom
            ]
            
            # Calculate EAR for both eyes
            left_ear = self._calculate_ear(left_eye)
            right_ear = self._calculate_ear(right_eye)
            average_ear = (left_ear + right_ear) / 2.0
            
            # Calculate face size for distance adaptation
            face_size = self._calculate_face_size(face_landmarks)
            
            # Detect blinks using adaptive threshold
            blink_detected = self._detect_blink_adaptive(average_ear, face_size)
            
            # Calculate lip opening using improved multi-point method
            lip_distance = self._calculate_lip_distance(face_landmarks)
            lip_pursing, lip_purse_duration = self._detect_lip_pursing(lip_distance, is_speaking)
        
        # Calculate blink rate
        blink_rate = self._calculate_blink_rate()
        
        # Determine cognitive load
        high_cognitive_load = blink_rate > self.blink_rate_threshold
        
        # Classify overall stress level
        stress_level = self._classify_stress_level(blink_rate, lip_pursing)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        return StressMetrics(
            left_ear=left_ear,
            right_ear=right_ear,
            average_ear=average_ear,
            blink_detected=blink_detected,
            blink_count=self.blink_count,
            blink_rate=blink_rate,
            high_cognitive_load=high_cognitive_load,
            lip_distance=lip_distance,
            lip_pursing=lip_pursing,
            lip_purse_duration=lip_purse_duration,
            stress_level=stress_level,
            processing_time_ms=processing_time_ms,
            timestamp=time.time()
        )
    
    def get_session_summary(self) -> dict:
        """
        Get comprehensive session summary for stress analysis.
        
        Returns:
            Dictionary with session-wide stress metrics
        """
        session_duration = time.time() - self.session_start_time
        average_blink_rate = self._calculate_blink_rate()
        
        return {
            "session_duration_minutes": session_duration / 60.0,
            "total_blinks": self.blink_count,
            "average_blink_rate": average_blink_rate,
            "high_cognitive_load_detected": average_blink_rate > self.blink_rate_threshold,
            "max_lip_purse_duration": self.lip_purse_duration,
            "frames_processed": self.frame_count,
            "stress_assessment": self._classify_stress_level(average_blink_rate, self.lip_purse_duration > 0)
        }