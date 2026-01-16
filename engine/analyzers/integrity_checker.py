"""
Anti-Cheating Integrity Checker

This module implements gaze pattern analysis to detect potential cheating behaviors:
- Gaze position tracking at speech onset
- Repeated pattern detection (looking at notes)
- Integrity scoring and warning system

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import time
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from collections import deque


@dataclass
class IntegrityMetrics:
    """Integrity analysis metrics for a single frame"""
    # Gaze tracking
    gaze_x: float  # Normalized X coordinate of gaze
    gaze_y: float  # Normalized Y coordinate of gaze
    gaze_cluster_id: Optional[int]  # Which cluster this gaze belongs to
    
    # Pattern detection
    cheat_flag_count: int  # Number of suspicious patterns detected
    integrity_warning: bool  # True if cheat_flag_count exceeds threshold
    
    # Scoring
    integrity_score: float  # 1.0 = clean, 0.0 = highly suspicious
    
    # Metadata
    suspicious_segments: List[Dict]  # List of suspicious time segments
    processing_time_ms: float
    timestamp: float


@dataclass
class IntegrityReport:
    """Comprehensive integrity report for entire session"""
    session_duration_minutes: float
    total_speech_onsets: int
    cheat_flag_count: int
    integrity_score: float
    integrity_assessment: str  # "clean", "suspicious", "highly_suspicious"
    suspicious_segments: List[Dict]
    gaze_clusters: List[Dict]  # Detected gaze clusters with frequencies
    recommendations: List[str]


class IntegrityChecker:
    """
    Analyzes gaze patterns to detect potential cheating behaviors.
    
    Tracks eye position at speech onset and detects repeated patterns
    that suggest reading from notes or external sources.
    """
    
    def __init__(self,
                 gaze_cluster_threshold: float = 0.05,
                 cheat_flag_threshold: int = 5,
                 min_cluster_frequency: int = 3):
        """
        Initialize integrity checker with configurable thresholds.
        
        Args:
            gaze_cluster_threshold: Distance threshold for clustering gaze positions
            cheat_flag_threshold: Number of flags before raising integrity warning
            min_cluster_frequency: Minimum visits to cluster to be suspicious
        """
        # Thresholds
        self.gaze_cluster_threshold = gaze_cluster_threshold
        self.cheat_flag_threshold = cheat_flag_threshold
        self.min_cluster_frequency = min_cluster_frequency
        
        # Gaze tracking
        self.gaze_history = deque(maxlen=300)  # Last 10 seconds at 30fps
        self.speech_onset_gazes = []  # Gaze positions at speech onset
        
        # Cluster tracking
        self.gaze_clusters = []  # List of detected clusters with their centers
        self.cluster_frequencies = {}  # How many times each cluster was visited
        
        # Integrity tracking
        self.cheat_flag_count = 0
        self.suspicious_segments = []
        self.total_speech_onsets = 0
        
        # Session tracking
        self.session_start_time = time.time()
        self.frame_count = 0
    
    def reset(self):
        """Reset analyzer state for new session"""
        self.gaze_history.clear()
        self.speech_onset_gazes.clear()
        self.gaze_clusters.clear()
        self.cluster_frequencies.clear()
        self.cheat_flag_count = 0
        self.suspicious_segments.clear()
        self.total_speech_onsets = 0
        self.session_start_time = time.time()
        self.frame_count = 0
    
    def _calculate_gaze_position(self, face_landmarks) -> Tuple[float, float]:
        """
        Calculate gaze position using eye landmark centroids.
        
        Args:
            face_landmarks: MediaPipe face landmarks (468 points)
            
        Returns:
            Tuple of (gaze_x, gaze_y) normalized coordinates
        """
        if not face_landmarks or len(face_landmarks) < 468:
            return (0.5, 0.5)  # Default center gaze
        
        # Left eye landmarks for gaze estimation
        left_eye_inner = face_landmarks[133]  # Inner corner
        left_eye_outer = face_landmarks[33]   # Outer corner
        left_eye_top = face_landmarks[159]    # Top
        left_eye_bottom = face_landmarks[145] # Bottom
        
        # Right eye landmarks for gaze estimation
        right_eye_inner = face_landmarks[362]  # Inner corner
        right_eye_outer = face_landmarks[263]  # Outer corner
        right_eye_top = face_landmarks[386]    # Top
        right_eye_bottom = face_landmarks[374] # Bottom
        
        # Calculate left eye centroid
        left_eye_x = (left_eye_inner.x + left_eye_outer.x) / 2.0
        left_eye_y = (left_eye_top.y + left_eye_bottom.y) / 2.0
        
        # Calculate right eye centroid
        right_eye_x = (right_eye_inner.x + right_eye_outer.x) / 2.0
        right_eye_y = (right_eye_top.y + right_eye_bottom.y) / 2.0
        
        # Average both eyes for gaze position
        gaze_x = (left_eye_x + right_eye_x) / 2.0
        gaze_y = (left_eye_y + right_eye_y) / 2.0
        
        return (float(gaze_x), float(gaze_y))
    
    def _find_or_create_cluster(self, gaze_x: float, gaze_y: float) -> int:
        """
        Find existing cluster or create new one for gaze position.
        
        Args:
            gaze_x: X coordinate of gaze
            gaze_y: Y coordinate of gaze
            
        Returns:
            Cluster ID
        """
        # Check if gaze belongs to existing cluster
        for i, cluster in enumerate(self.gaze_clusters):
            cluster_x, cluster_y = cluster['center']
            
            # Calculate distance to cluster center
            distance = math.sqrt(
                (gaze_x - cluster_x)**2 + 
                (gaze_y - cluster_y)**2
            )
            
            if distance < self.gaze_cluster_threshold:
                # Update cluster center (moving average)
                visits = cluster['visits']
                new_x = (cluster_x * visits + gaze_x) / (visits + 1)
                new_y = (cluster_y * visits + gaze_y) / (visits + 1)
                
                cluster['center'] = (new_x, new_y)
                cluster['visits'] += 1
                cluster['last_visit'] = time.time()
                
                return i
        
        # Create new cluster
        cluster_id = len(self.gaze_clusters)
        self.gaze_clusters.append({
            'center': (gaze_x, gaze_y),
            'visits': 1,
            'first_visit': time.time(),
            'last_visit': time.time()
        })
        
        return cluster_id
    
    def _detect_repeated_pattern(self, gaze_x: float, gaze_y: float, 
                                 speech_onset: bool) -> bool:
        """
        Detect if user repeatedly looks at same location at speech onset.
        
        Args:
            gaze_x: Current gaze X coordinate
            gaze_y: Current gaze Y coordinate
            speech_onset: Whether user just started speaking
            
        Returns:
            True if suspicious pattern detected
        """
        # Only track gaze at speech onset
        if not speech_onset:
            return False
        
        self.total_speech_onsets += 1
        
        # Record gaze position at speech onset
        self.speech_onset_gazes.append({
            'position': (gaze_x, gaze_y),
            'timestamp': time.time()
        })
        
        # Find or create cluster for this gaze
        cluster_id = self._find_or_create_cluster(gaze_x, gaze_y)
        
        # Track cluster frequency
        if cluster_id not in self.cluster_frequencies:
            self.cluster_frequencies[cluster_id] = 0
        self.cluster_frequencies[cluster_id] += 1
        
        # Check if this cluster is visited suspiciously often
        cluster_frequency = self.cluster_frequencies[cluster_id]
        
        if cluster_frequency >= self.min_cluster_frequency:
            # Check if this is a new cheat flag
            cluster = self.gaze_clusters[cluster_id]
            
            # Only flag if cluster is off-center (likely looking at notes)
            cluster_x, cluster_y = cluster['center']
            distance_from_center = math.sqrt(
                (cluster_x - 0.5)**2 + 
                (cluster_y - 0.5)**2
            )
            
            # Flag if looking significantly away from center (>0.2 units)
            if distance_from_center > 0.2:
                self.cheat_flag_count += 1
                
                # Record suspicious segment
                self.suspicious_segments.append({
                    'timestamp': time.time(),
                    'cluster_id': cluster_id,
                    'cluster_center': cluster['center'],
                    'frequency': cluster_frequency,
                    'distance_from_center': distance_from_center
                })
                
                print(f"🚨 Suspicious pattern detected! Cluster {cluster_id} at {cluster['center']}, "
                      f"frequency: {cluster_frequency}, flags: {self.cheat_flag_count}")
                
                return True
        
        return False
    
    def _calculate_integrity_score(self) -> float:
        """
        Calculate overall integrity score based on detected patterns.
        
        Returns:
            Integrity score from 0.0 (highly suspicious) to 1.0 (clean)
        """
        if self.total_speech_onsets == 0:
            return 1.0  # No data yet, assume clean
        
        # Base score starts at 1.0
        score = 1.0
        
        # Penalize for cheat flags
        # Each flag reduces score by 0.15
        flag_penalty = min(0.9, self.cheat_flag_count * 0.15)
        score -= flag_penalty
        
        # Penalize for high cluster concentration
        # If most speech onsets go to few clusters, it's suspicious
        if len(self.cluster_frequencies) > 0:
            max_cluster_frequency = max(self.cluster_frequencies.values())
            concentration_ratio = max_cluster_frequency / self.total_speech_onsets
            
            if concentration_ratio > 0.5:  # More than 50% to one cluster
                concentration_penalty = (concentration_ratio - 0.5) * 0.4
                score -= concentration_penalty
        
        # Ensure score stays in valid range
        score = max(0.0, min(1.0, score))
        
        return float(score)
    
    def analyze(self, face_landmarks, speech_onset: bool = False) -> IntegrityMetrics:
        """
        Analyze gaze patterns for integrity checking.
        
        Args:
            face_landmarks: MediaPipe face landmarks (468 points)
            speech_onset: Whether user just started speaking
            
        Returns:
            IntegrityMetrics with gaze analysis
        """
        start_time = time.time()
        self.frame_count += 1
        
        # Calculate gaze position
        gaze_x, gaze_y = self._calculate_gaze_position(face_landmarks)
        
        # Track gaze history
        self.gaze_history.append({
            'position': (gaze_x, gaze_y),
            'timestamp': time.time(),
            'speech_onset': speech_onset
        })
        
        # Detect repeated patterns at speech onset
        pattern_detected = self._detect_repeated_pattern(gaze_x, gaze_y, speech_onset)
        
        # Determine cluster ID for current gaze
        cluster_id = None
        if len(self.gaze_clusters) > 0:
            # Find closest cluster
            min_distance = float('inf')
            for i, cluster in enumerate(self.gaze_clusters):
                cluster_x, cluster_y = cluster['center']
                distance = math.sqrt(
                    (gaze_x - cluster_x)**2 + 
                    (gaze_y - cluster_y)**2
                )
                if distance < min_distance and distance < self.gaze_cluster_threshold:
                    min_distance = distance
                    cluster_id = i
        
        # Calculate integrity score
        integrity_score = self._calculate_integrity_score()
        
        # Determine if warning should be raised
        integrity_warning = self.cheat_flag_count >= self.cheat_flag_threshold
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        return IntegrityMetrics(
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            gaze_cluster_id=cluster_id,
            cheat_flag_count=self.cheat_flag_count,
            integrity_warning=integrity_warning,
            integrity_score=integrity_score,
            suspicious_segments=self.suspicious_segments.copy(),
            processing_time_ms=processing_time_ms,
            timestamp=time.time()
        )
    
    def get_session_report(self) -> IntegrityReport:
        """
        Generate comprehensive integrity report for entire session.
        
        Returns:
            IntegrityReport with session-wide analysis
        """
        session_duration = time.time() - self.session_start_time
        integrity_score = self._calculate_integrity_score()
        
        # Determine assessment level
        if integrity_score >= 0.8:
            assessment = "clean"
        elif integrity_score >= 0.5:
            assessment = "suspicious"
        else:
            assessment = "highly_suspicious"
        
        # Generate recommendations
        recommendations = []
        
        if self.cheat_flag_count > 0:
            recommendations.append(
                f"Detected {self.cheat_flag_count} instances of repeated gaze patterns at speech onset"
            )
        
        if len(self.cluster_frequencies) > 0:
            max_cluster_freq = max(self.cluster_frequencies.values())
            if max_cluster_freq > self.total_speech_onsets * 0.5:
                recommendations.append(
                    f"High concentration of gaze to single location ({max_cluster_freq}/{self.total_speech_onsets} speech onsets)"
                )
        
        if integrity_score < 0.5:
            recommendations.append(
                "Consider manual review of interview recording for potential integrity issues"
            )
        
        if len(recommendations) == 0:
            recommendations.append("No significant integrity concerns detected")
        
        # Format cluster information
        cluster_info = []
        for i, cluster in enumerate(self.gaze_clusters):
            cluster_info.append({
                'id': i,
                'center': cluster['center'],
                'visits': cluster['visits'],
                'frequency': self.cluster_frequencies.get(i, 0)
            })
        
        return IntegrityReport(
            session_duration_minutes=session_duration / 60.0,
            total_speech_onsets=self.total_speech_onsets,
            cheat_flag_count=self.cheat_flag_count,
            integrity_score=integrity_score,
            integrity_assessment=assessment,
            suspicious_segments=self.suspicious_segments.copy(),
            gaze_clusters=cluster_info,
            recommendations=recommendations
        )