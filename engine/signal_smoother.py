"""
Signal Smoothing using One Euro Filter for landmark jitter reduction.

The One Euro Filter is an adaptive low-pass filter that reduces noise while
preserving responsiveness to quick movements. It adjusts the cutoff frequency
based on the velocity of the signal.

Reference: Casiez et al., "1€ Filter: A Simple Speed-based Low-pass Filter"
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import math


@dataclass
class Landmark:
    """Single landmark point with normalized coordinates."""
    x: float  # Normalized 0.0-1.0
    y: float  # Normalized 0.0-1.0
    z: float  # Depth (relative scale)
    visibility: float  # Confidence 0.0-1.0


class OneEuroFilter:
    """
    One Euro Filter for a single scalar value.
    
    The filter adapts its cutoff frequency based on the velocity of the signal,
    providing smooth output for slow movements and quick response for fast movements.
    """
    
    def __init__(self, 
                 freq: float,
                 min_cutoff: float = 1.0,
                 beta: float = 0.0,
                 d_cutoff: float = 1.0):
        """
        Initialize One Euro Filter.
        
        Args:
            freq: Sampling frequency (Hz)
            min_cutoff: Minimum cutoff frequency (lower = more smoothing)
            beta: Speed coefficient (higher = more responsive to velocity)
            d_cutoff: Cutoff frequency for derivative
        """
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        # Internal state
        self.x_prev: Optional[float] = None
        self.dx_prev: Optional[float] = None
        self.t_prev: Optional[float] = None
    
    def _smoothing_factor(self, t_e: float, cutoff: float) -> float:
        """
        Calculate smoothing factor (alpha) for low-pass filter.
        
        Args:
            t_e: Sampling period
            cutoff: Cutoff frequency
            
        Returns:
            Smoothing factor (0.0-1.0)
        """
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)
    
    def __call__(self, x: float, t: Optional[float] = None) -> float:
        """
        Filter a new value.
        
        Args:
            x: New input value
            t: Timestamp (optional, uses current time if None)
            
        Returns:
            Filtered value
        """
        # Use current time if not provided
        if t is None:
            t = time.time()
        
        # Initialize on first call
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t
            return x
        
        # Calculate time delta
        t_e = t - self.t_prev
        
        # Avoid division by zero
        if t_e <= 0:
            return self.x_prev
        
        # Calculate derivative (velocity)
        dx = (x - self.x_prev) / t_e
        
        # Smooth the derivative
        alpha_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx_hat = alpha_d * dx + (1 - alpha_d) * self.dx_prev
        
        # Calculate adaptive cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        
        # Smooth the value
        alpha = self._smoothing_factor(t_e, cutoff)
        x_hat = alpha * x + (1 - alpha) * self.x_prev
        
        # Update state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        
        return x_hat
    
    def reset(self):
        """Reset filter state."""
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None


class SignalSmoother:
    """
    Applies One Euro Filter to landmark coordinates to reduce jitter.
    
    Maintains separate filter instances for each landmark's x, y, z coordinates.
    Uses lazy initialization to create filters only for detected landmarks.
    """
    
    def __init__(self, 
                 freq: float = 30.0,
                 min_cutoff: float = 1.0,
                 beta: float = 0.0,
                 d_cutoff: float = 1.0):
        """
        Initialize Signal Smoother with One Euro Filter parameters.
        
        Args:
            freq: Sampling frequency (Hz) - typically 15-30 for video
            min_cutoff: Minimum cutoff frequency (1.0 = moderate smoothing)
            beta: Speed coefficient (0.0 = no velocity adaptation)
            d_cutoff: Cutoff for derivative (1.0 = moderate smoothing)
        """
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        # Dictionary to store filters: {(landmark_type, index, coord): OneEuroFilter}
        # landmark_type: 'pose', 'face', 'left_hand', 'right_hand'
        # index: landmark index (0-32 for pose, 0-467 for face, etc.)
        # coord: 'x', 'y', or 'z'
        self.filters: Dict[tuple, OneEuroFilter] = {}
        
        print(f"✅ SignalSmoother initialized (freq={freq}Hz, min_cutoff={min_cutoff}, beta={beta})")
    
    def _get_filter(self, landmark_type: str, index: int, coord: str) -> OneEuroFilter:
        """
        Get or create a filter for a specific landmark coordinate.
        
        Args:
            landmark_type: Type of landmark ('pose', 'face', 'left_hand', 'right_hand')
            index: Landmark index
            coord: Coordinate ('x', 'y', 'z')
            
        Returns:
            OneEuroFilter instance
        """
        key = (landmark_type, index, coord)
        
        if key not in self.filters:
            self.filters[key] = OneEuroFilter(
                freq=self.freq,
                min_cutoff=self.min_cutoff,
                beta=self.beta,
                d_cutoff=self.d_cutoff
            )
        
        return self.filters[key]
    
    def _smooth_landmark_list(self, 
                              landmarks: Optional[List[Landmark]], 
                              landmark_type: str,
                              timestamp: float) -> Optional[List[Landmark]]:
        """
        Smooth a list of landmarks.
        
        Args:
            landmarks: List of landmarks to smooth
            landmark_type: Type of landmark for filter key
            timestamp: Current timestamp
            
        Returns:
            List of smoothed landmarks or None if input is None
        """
        if landmarks is None:
            return None
        
        smoothed = []
        for i, lm in enumerate(landmarks):
            # Get filters for this landmark's coordinates
            filter_x = self._get_filter(landmark_type, i, 'x')
            filter_y = self._get_filter(landmark_type, i, 'y')
            filter_z = self._get_filter(landmark_type, i, 'z')
            
            # Apply filtering
            smoothed_x = filter_x(lm.x, timestamp)
            smoothed_y = filter_y(lm.y, timestamp)
            smoothed_z = filter_z(lm.z, timestamp)
            
            # Create smoothed landmark
            smoothed.append(Landmark(
                x=smoothed_x,
                y=smoothed_y,
                z=smoothed_z,
                visibility=lm.visibility  # Don't smooth visibility
            ))
        
        return smoothed
    
    def smooth_landmarks(self, 
                        pose_landmarks: Optional[List[Landmark]],
                        face_landmarks: Optional[List[Landmark]],
                        left_hand_landmarks: Optional[List[Landmark]],
                        right_hand_landmarks: Optional[List[Landmark]],
                        timestamp: float) -> tuple:
        """
        Apply smoothing filter to all landmark sets.
        
        Args:
            pose_landmarks: Pose landmarks (33 points)
            face_landmarks: Face landmarks (468 points)
            left_hand_landmarks: Left hand landmarks (21 points)
            right_hand_landmarks: Right hand landmarks (21 points)
            timestamp: Current timestamp in seconds
            
        Returns:
            Tuple of (smoothed_pose, smoothed_face, smoothed_left_hand, smoothed_right_hand)
        """
        smoothed_pose = self._smooth_landmark_list(pose_landmarks, 'pose', timestamp)
        smoothed_face = self._smooth_landmark_list(face_landmarks, 'face', timestamp)
        smoothed_left_hand = self._smooth_landmark_list(left_hand_landmarks, 'left_hand', timestamp)
        smoothed_right_hand = self._smooth_landmark_list(right_hand_landmarks, 'right_hand', timestamp)
        
        return smoothed_pose, smoothed_face, smoothed_left_hand, smoothed_right_hand
    
    def reset(self):
        """Reset all filter states."""
        for filter_obj in self.filters.values():
            filter_obj.reset()
        print("✅ SignalSmoother filters reset")
    
    def get_filter_count(self) -> int:
        """
        Get the number of active filters.
        
        Returns:
            Number of filter instances created
        """
        return len(self.filters)
    
    def get_stats(self) -> dict:
        """
        Get statistics about the smoother.
        
        Returns:
            Dictionary with filter statistics
        """
        return {
            "total_filters": len(self.filters),
            "freq": self.freq,
            "min_cutoff": self.min_cutoff,
            "beta": self.beta,
            "d_cutoff": self.d_cutoff
        }
