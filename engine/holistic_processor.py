"""
MediaPipe Holistic Processor for full-body landmark extraction.
Extracts 543 landmarks: 33 pose + 468 face + 42 hands (21 per hand)
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Landmark:
    """Single landmark point with normalized coordinates."""
    x: float  # Normalized 0.0-1.0
    y: float  # Normalized 0.0-1.0
    z: float  # Depth (relative scale)
    visibility: float  # Confidence 0.0-1.0


@dataclass
class HolisticResults:
    """Complete holistic analysis results for a single frame."""
    pose_landmarks: Optional[List[Landmark]]  # 33 points
    face_landmarks: Optional[List[Landmark]]  # 468 points
    left_hand_landmarks: Optional[List[Landmark]]  # 21 points
    right_hand_landmarks: Optional[List[Landmark]]  # 21 points
    timestamp: float
    frame_number: int


class HolisticProcessor:
    """
    Manages MediaPipe Holistic model for full-body landmark extraction.
    Handles frame preprocessing, landmark extraction, and performance optimization.
    """
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 enable_frame_skip: bool = True,
                 target_fps: float = 15.0):
        """
        Initialize MediaPipe Holistic model.
        
        Args:
            min_detection_confidence: Minimum confidence for detection (0.0-1.0)
            min_tracking_confidence: Minimum confidence for tracking (0.0-1.0)
            enable_frame_skip: Whether to skip frames under load
            target_fps: Target processing rate (frames per second)
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.enable_frame_skip = enable_frame_skip
        self.target_fps = target_fps
        
        # Initialize MediaPipe Holistic
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=1,  # 0=Lite, 1=Full, 2=Heavy
            smooth_landmarks=True,  # Enable built-in smoothing
            enable_segmentation=False,  # Disable to save CPU
            refine_face_landmarks=True  # Enable for better eye/lip tracking
        )
        
        # Performance tracking
        self.frame_count = 0
        self.last_process_time = time.time()
        self.processing_times = []
        self.skip_counter = 0
        
        print(f"✅ HolisticProcessor initialized (confidence: {min_detection_confidence})")
    
    def _convert_landmarks(self, mp_landmarks) -> Optional[List[Landmark]]:
        """
        Convert MediaPipe landmarks to our Landmark dataclass.
        
        Args:
            mp_landmarks: MediaPipe landmark list
            
        Returns:
            List of Landmark objects or None if no landmarks
        """
        if not mp_landmarks:
            return None
            
        landmarks = []
        for lm in mp_landmarks.landmark:
            landmarks.append(Landmark(
                x=float(lm.x),
                y=float(lm.y),
                z=float(lm.z),
                visibility=float(getattr(lm, 'visibility', 1.0))
            ))
        return landmarks
    
    def should_skip_frame(self) -> bool:
        """
        Determine if current frame should be skipped based on performance.
        
        Returns:
            True if frame should be skipped
        """
        if not self.enable_frame_skip:
            return False
        
        # Calculate current FPS
        if len(self.processing_times) < 5:
            return False
        
        avg_time = sum(self.processing_times[-10:]) / min(10, len(self.processing_times))
        current_fps = 1.0 / avg_time if avg_time > 0 else 30.0
        
        # Skip every other frame if FPS drops below target
        if current_fps < self.target_fps:
            self.skip_counter += 1
            if self.skip_counter % 2 == 0:
                return True
        else:
            self.skip_counter = 0
        
        return False
    
    def process_frame(self, frame: np.ndarray) -> HolisticResults:
        """
        Process a single video frame and extract landmarks.
        
        Args:
            frame: BGR image from OpenCV (H x W x 3)
            
        Returns:
            HolisticResults containing pose, face, and hand landmarks
        """
        start_time = time.time()
        
        # Check if we should skip this frame
        if self.should_skip_frame():
            # Return empty results for skipped frame
            return HolisticResults(
                pose_landmarks=None,
                face_landmarks=None,
                left_hand_landmarks=None,
                right_hand_landmarks=None,
                timestamp=start_time,
                frame_number=self.frame_count
            )
        
        # Convert BGR to RGB (MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Mark frame as not writeable to improve performance
        rgb_frame.flags.writeable = False
        
        # Process frame with MediaPipe Holistic
        results = self.holistic.process(rgb_frame)
        
        # Convert landmarks to our format
        pose_landmarks = self._convert_landmarks(results.pose_landmarks)
        face_landmarks = self._convert_landmarks(results.face_landmarks)
        left_hand_landmarks = self._convert_landmarks(results.left_hand_landmarks)
        right_hand_landmarks = self._convert_landmarks(results.right_hand_landmarks)
        
        # Update performance metrics
        process_time = time.time() - start_time
        self.processing_times.append(process_time)
        if len(self.processing_times) > 30:
            self.processing_times.pop(0)
        
        self.frame_count += 1
        
        return HolisticResults(
            pose_landmarks=pose_landmarks,
            face_landmarks=face_landmarks,
            left_hand_landmarks=left_hand_landmarks,
            right_hand_landmarks=right_hand_landmarks,
            timestamp=start_time,
            frame_number=self.frame_count
        )
    
    def get_performance_stats(self) -> dict:
        """
        Get current performance statistics.
        
        Returns:
            Dictionary with FPS, average processing time, etc.
        """
        if not self.processing_times:
            return {
                "fps": 0.0,
                "avg_process_time_ms": 0.0,
                "frames_processed": self.frame_count
            }
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        
        return {
            "fps": round(fps, 2),
            "avg_process_time_ms": round(avg_time * 1000, 2),
            "frames_processed": self.frame_count,
            "frame_skip_enabled": self.enable_frame_skip
        }
    
    def release(self):
        """Release MediaPipe resources."""
        if self.holistic:
            self.holistic.close()
            print("✅ HolisticProcessor resources released")
