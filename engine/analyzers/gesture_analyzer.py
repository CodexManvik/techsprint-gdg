"""
Gesture Intelligence Module for Interview Mirror.

Analyzes hand gestures and movements including:
- Face-touching behavior detection
- Hand gesture frequency tracking
- Communication style classification
- Hand activity level assessment
"""

import math
import time
from dataclasses import dataclass
from typing import Optional, List, Tuple
from collections import deque


@dataclass
class Landmark:
    """Single landmark point with normalized coordinates."""
    x: float  # Normalized 0.0-1.0
    y: float  # Normalized 0.0-1.0
    z: float  # Depth (relative scale)
    visibility: float  # Confidence 0.0-1.0


@dataclass
class GestureMetrics:
    """
    Comprehensive gesture analysis results.
    
    Tracks hand visibility, face-touching behavior, gesture frequency,
    and overall hand activity level.
    """
    left_hand_visible: bool
    right_hand_visible: bool
    face_touch_detected: bool  # Current frame detection
    face_touch_count: int  # Cumulative session count
    active_gesture_count: int  # Current frame gestures
    gesture_frequency: float  # Gestures per minute
    hand_activity_level: str  # "passive", "moderate", "dynamic"
    left_hand_above_shoulders: bool  # Left hand elevated
    right_hand_above_shoulders: bool  # Right hand elevated
    timestamp: float


@dataclass
class GestureSummary:
    """
    Session-wide gesture analysis summary.
    
    Provides aggregate statistics and classification for the entire
    interview session.
    """
    total_face_touches: int
    total_gestures: int
    average_gestures_per_minute: float
    session_duration_minutes: float
    classification: str  # "passive", "moderate", "dynamic"
    face_touch_frequency: float  # Touches per minute
    most_active_period: str  # Time period with highest activity


class GestureAnalyzer:
    """
    Analyzes hand gestures and movements from hand landmarks.
    
    Uses MediaPipe Hand landmarks (21 points per hand) to detect:
    - Face-touching behavior (nervousness indicator)
    - Hand gesture frequency (communication style)
    - Hand elevation and activity levels
    - Overall gesture classification
    """
    
    # Hand landmark indices (MediaPipe Hands)
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    
    def __init__(self, 
                 face_touch_threshold: float = 0.1,
                 gesture_height_threshold: float = 0.1,
                 gesture_velocity_threshold: float = 0.02,
                 history_size: int = 30):
        """
        Initialize gesture analysis with configurable thresholds.
        
        Args:
            face_touch_threshold: Distance threshold for face-touch detection (normalized units)
            gesture_height_threshold: Height above shoulders to count as gesture (normalized units)
            gesture_velocity_threshold: Minimum hand movement to count as gesture
            history_size: Number of frames to track for velocity and frequency analysis
        """
        self.face_touch_threshold = face_touch_threshold
        self.gesture_height_threshold = gesture_height_threshold
        self.gesture_velocity_threshold = gesture_velocity_threshold
        
        # Session tracking
        self.session_start_time = time.time()
        self.total_face_touches = 0
        self.total_gestures = 0
        
        # Frame-to-frame tracking
        self.left_hand_history = deque(maxlen=history_size)
        self.right_hand_history = deque(maxlen=history_size)
        self.gesture_timestamps = deque(maxlen=100)  # Track gesture timing
        self.face_touch_timestamps = deque(maxlen=50)  # Track face-touch timing
        
        print(f"✅ GestureAnalyzer initialized (face_touch_threshold={face_touch_threshold}, "
              f"gesture_height_threshold={gesture_height_threshold})")
    
    def _calculate_distance(self, point1: Landmark, point2: Landmark) -> float:
        """
        Calculate Euclidean distance between two landmarks.
        
        Args:
            point1: First landmark point
            point2: Second landmark point
            
        Returns:
            Euclidean distance in normalized coordinates
        """
        return math.sqrt(
            (point1.x - point2.x) ** 2 + 
            (point1.y - point2.y) ** 2
        )
    
    def _detect_face_touch(self, 
                          left_hand_landmarks: Optional[List[Landmark]], 
                          right_hand_landmarks: Optional[List[Landmark]],
                          nose_landmark: Optional[Landmark]) -> bool:
        """
        Detect if either hand is touching or near the face.
        
        Uses index finger tip as the primary detection point, as it's most
        commonly used for face-touching gestures.
        
        Args:
            left_hand_landmarks: Left hand landmarks (21 points)
            right_hand_landmarks: Right hand landmarks (21 points)
            nose_landmark: Nose landmark for face reference
            
        Returns:
            True if face-touch detected, False otherwise
        """
        if not nose_landmark:
            return False
        
        face_touch_detected = False
        
        # Check left hand
        if (left_hand_landmarks and 
            len(left_hand_landmarks) > self.INDEX_TIP and
            left_hand_landmarks[self.INDEX_TIP].visibility > 0.5):
            
            distance = self._calculate_distance(
                left_hand_landmarks[self.INDEX_TIP], 
                nose_landmark
            )
            
            if distance < self.face_touch_threshold:
                face_touch_detected = True
        
        # Check right hand
        if (right_hand_landmarks and 
            len(right_hand_landmarks) > self.INDEX_TIP and
            right_hand_landmarks[self.INDEX_TIP].visibility > 0.5):
            
            distance = self._calculate_distance(
                right_hand_landmarks[self.INDEX_TIP], 
                nose_landmark
            )
            
            if distance < self.face_touch_threshold:
                face_touch_detected = True
        
        # Update counters if face-touch detected
        if face_touch_detected:
            current_time = time.time()
            self.face_touch_timestamps.append(current_time)
            self.total_face_touches += 1
        
        return face_touch_detected
    
    def _count_active_gestures(self, 
                              left_hand_landmarks: Optional[List[Landmark]], 
                              right_hand_landmarks: Optional[List[Landmark]],
                              shoulder_y: float) -> Tuple[int, bool, bool]:
        """
        Count expressive hand movements and elevated gestures.
        
        Detects when hands are elevated above shoulder line and moving
        with sufficient velocity to indicate expressive communication.
        
        Args:
            left_hand_landmarks: Left hand landmarks
            right_hand_landmarks: Right hand landmarks
            shoulder_y: Average Y-coordinate of shoulders for reference
            
        Returns:
            Tuple of (active_gesture_count, left_above_shoulders, right_above_shoulders)
        """
        current_time = time.time()
        active_gestures = 0
        left_above_shoulders = False
        right_above_shoulders = False
        
        # Analyze left hand
        if (left_hand_landmarks and 
            len(left_hand_landmarks) > self.WRIST and
            left_hand_landmarks[self.WRIST].visibility > 0.5):
            
            wrist = left_hand_landmarks[self.WRIST]
            
            # Check if hand is elevated above shoulders
            if wrist.y < (shoulder_y - self.gesture_height_threshold):
                left_above_shoulders = True
                
                # Track movement velocity
                self.left_hand_history.append((wrist.x, wrist.y, current_time))
                
                # Calculate velocity if we have enough history
                if len(self.left_hand_history) >= 3:
                    recent_positions = list(self.left_hand_history)[-3:]
                    
                    # Calculate movement over last 3 frames
                    total_movement = 0
                    for i in range(1, len(recent_positions)):
                        prev_x, prev_y, _ = recent_positions[i-1]
                        curr_x, curr_y, _ = recent_positions[i]
                        movement = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
                        total_movement += movement
                    
                    # If significant movement detected, count as active gesture
                    if total_movement > self.gesture_velocity_threshold:
                        active_gestures += 1
                        self.gesture_timestamps.append(current_time)
        
        # Analyze right hand (same logic)
        if (right_hand_landmarks and 
            len(right_hand_landmarks) > self.WRIST and
            right_hand_landmarks[self.WRIST].visibility > 0.5):
            
            wrist = right_hand_landmarks[self.WRIST]
            
            # Check if hand is elevated above shoulders
            if wrist.y < (shoulder_y - self.gesture_height_threshold):
                right_above_shoulders = True
                
                # Track movement velocity
                self.right_hand_history.append((wrist.x, wrist.y, current_time))
                
                # Calculate velocity if we have enough history
                if len(self.right_hand_history) >= 3:
                    recent_positions = list(self.right_hand_history)[-3:]
                    
                    # Calculate movement over last 3 frames
                    total_movement = 0
                    for i in range(1, len(recent_positions)):
                        prev_x, prev_y, _ = recent_positions[i-1]
                        curr_x, curr_y, _ = recent_positions[i]
                        movement = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
                        total_movement += movement
                    
                    # If significant movement detected, count as active gesture
                    if total_movement > self.gesture_velocity_threshold:
                        active_gestures += 1
                        self.gesture_timestamps.append(current_time)
        
        # Update total gesture count
        self.total_gestures += active_gestures
        
        return active_gestures, left_above_shoulders, right_above_shoulders
    
    def _calculate_gesture_frequency(self) -> float:
        """
        Calculate gestures per minute based on recent activity.
        
        Returns:
            Gestures per minute (float)
        """
        current_time = time.time()
        session_duration_minutes = (current_time - self.session_start_time) / 60.0
        
        if session_duration_minutes < 0.1:  # Less than 6 seconds
            return 0.0
        
        return self.total_gestures / session_duration_minutes
    
    def _classify_activity_level(self, gesture_frequency: float) -> str:
        """
        Classify hand activity level based on gesture frequency.
        
        Args:
            gesture_frequency: Gestures per minute
            
        Returns:
            Classification: "passive", "moderate", or "dynamic"
        """
        if gesture_frequency < 5.0:
            return "passive"
        elif gesture_frequency < 15.0:
            return "moderate"
        else:
            return "dynamic"
    
    def analyze(self, 
                left_hand_landmarks: Optional[List[Landmark]],
                right_hand_landmarks: Optional[List[Landmark]],
                nose_landmark: Optional[Landmark],
                shoulder_y: float,
                timestamp: float) -> GestureMetrics:
        """
        Perform complete gesture analysis on hand and face landmarks.
        
        Args:
            left_hand_landmarks: Left hand landmarks (21 points)
            right_hand_landmarks: Right hand landmarks (21 points)
            nose_landmark: Nose landmark for face-touch detection
            shoulder_y: Average Y-coordinate of shoulders
            timestamp: Current timestamp in seconds
            
        Returns:
            GestureMetrics with all gesture indicators
        """
        # Check hand visibility
        left_hand_visible = (left_hand_landmarks is not None and 
                           len(left_hand_landmarks) > 0 and
                           left_hand_landmarks[0].visibility > 0.5)
        
        right_hand_visible = (right_hand_landmarks is not None and 
                            len(right_hand_landmarks) > 0 and
                            right_hand_landmarks[0].visibility > 0.5)
        
        # Detect face-touching
        face_touch_detected = self._detect_face_touch(
            left_hand_landmarks, 
            right_hand_landmarks, 
            nose_landmark
        )
        
        # Count active gestures
        active_gesture_count, left_above_shoulders, right_above_shoulders = \
            self._count_active_gestures(
                left_hand_landmarks, 
                right_hand_landmarks, 
                shoulder_y
            )
        
        # Calculate frequency and classify activity
        gesture_frequency = self._calculate_gesture_frequency()
        hand_activity_level = self._classify_activity_level(gesture_frequency)
        
        return GestureMetrics(
            left_hand_visible=left_hand_visible,
            right_hand_visible=right_hand_visible,
            face_touch_detected=face_touch_detected,
            face_touch_count=self.total_face_touches,
            active_gesture_count=active_gesture_count,
            gesture_frequency=gesture_frequency,
            hand_activity_level=hand_activity_level,
            left_hand_above_shoulders=left_above_shoulders,
            right_hand_above_shoulders=right_above_shoulders,
            timestamp=timestamp
        )
    
    def get_session_summary(self) -> GestureSummary:
        """
        Get aggregate gesture statistics for the entire session.
        
        Returns:
            GestureSummary with session-wide statistics
        """
        current_time = time.time()
        session_duration_minutes = (current_time - self.session_start_time) / 60.0
        
        # Calculate averages
        avg_gestures_per_minute = (self.total_gestures / session_duration_minutes 
                                 if session_duration_minutes > 0 else 0.0)
        
        face_touch_frequency = (self.total_face_touches / session_duration_minutes 
                              if session_duration_minutes > 0 else 0.0)
        
        # Classify overall session
        classification = self._classify_activity_level(avg_gestures_per_minute)
        
        # Find most active period (simplified - could be enhanced)
        most_active_period = "middle" if len(self.gesture_timestamps) > 10 else "beginning"
        
        return GestureSummary(
            total_face_touches=self.total_face_touches,
            total_gestures=self.total_gestures,
            average_gestures_per_minute=avg_gestures_per_minute,
            session_duration_minutes=session_duration_minutes,
            classification=classification,
            face_touch_frequency=face_touch_frequency,
            most_active_period=most_active_period
        )
    
    def reset(self):
        """Reset analyzer state for new session."""
        self.session_start_time = time.time()
        self.total_face_touches = 0
        self.total_gestures = 0
        self.left_hand_history.clear()
        self.right_hand_history.clear()
        self.gesture_timestamps.clear()
        self.face_touch_timestamps.clear()
        print("✅ GestureAnalyzer state reset")