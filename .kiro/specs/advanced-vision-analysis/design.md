# Design Document

## Overview

This design document outlines the architecture for upgrading The Interview Mirror's vision analysis system from basic facial tracking to comprehensive holistic body analysis. The system will leverage MediaPipe Holistic to track 543 landmarks (33 pose + 468 face + 42 hands) and implement advanced behavioral analysis including power posture detection, hand gesture intelligence, micro-expression stress signals, and anti-cheating mechanisms.

The design follows a modular architecture where the existing `VisionEngine` class is refactored into specialized analyzers, each responsible for a specific domain of behavioral analysis. All raw landmark data will pass through signal smoothing filters before analysis to ensure stable, production-quality metrics.

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/HTML)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Video Stream │  │  Metrics UI  │  │ AI Chat Box  │     │
│  └──────┬───────┘  └──────▲───────┘  └──────▲───────┘     │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
          │ WebSocket        │ JSON Metrics     │ AI Response
          ▼                  │                  │
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (app.py)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         WebSocket Handler (/ws/interview)            │  │
│  │  • Receives video frames & audio                     │  │
│  │  • Routes to appropriate engines                     │  │
│  │  • Aggregates results                                │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼──────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Vision Engine │  │  AI Engine   │  │ Audio Engine │   │
│  │  (Holistic)   │  │   (Gemini)   │  │  (Speech)    │   │
│  └────┬──────────┘  └──────────────┘  └──────────────┘   │
└───────┼─────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│              Vision Engine Architecture                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         HolisticProcessor (Core Pipeline)            │  │
│  │  • MediaPipe Holistic initialization                 │  │
│  │  • Frame preprocessing & optimization                │  │
│  │  • Landmark extraction (543 points)                  │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼──────────────────────────────────────────────────┐ │
│  │         SignalSmoother (Filtering Layer)             │ │
│  │  • One Euro Filter per landmark coordinate           │ │
│  │  • Adaptive smoothing based on velocity              │ │
│  │  • Jitter reduction                                  │ │
│  └────┬─────────────────────────────────────────────────┘ │
│       │                                                      │
│  ┌────▼──────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Posture     │  │   Gesture    │  │    Stress    │   │
│  │   Analyzer    │  │   Analyzer   │  │   Analyzer   │   │
│  └───────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐                                          │
│  │  Integrity   │                                          │
│  │   Checker    │                                          │
│  └──────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**HolisticProcessor**: Core pipeline that manages MediaPipe Holistic model, handles frame preprocessing, and extracts raw landmarks.

**SignalSmoother**: Applies One Euro Filter to all landmark coordinates to reduce camera jitter and produce stable metrics.

**PostureAnalyzer**: Analyzes shoulder alignment, slouch detection, arm crossing, and body stability.

**GestureAnalyzer**: Tracks hand movements, face-touching behavior, and gesture frequency.

**StressAnalyzer**: Monitors blink rate via Eye Aspect Ratio and lip compression patterns.

**IntegrityChecker**: Detects suspicious gaze patterns that indicate reading from notes.

## Components and Interfaces

### 1. HolisticProcessor Class

**Purpose**: Manages MediaPipe Holistic model and extracts raw landmarks from video frames.

**Location**: `engine/holistic_processor.py`

**Interface**:
```python
class HolisticProcessor:
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 enable_frame_skip: bool = True):
        """
        Initialize MediaPipe Holistic model.
        
        Args:
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            enable_frame_skip: Whether to skip frames under load
        """
        
    def process_frame(self, frame: np.ndarray) -> HolisticResults:
        """
        Process a single video frame and extract landmarks.
        
        Args:
            frame: BGR image from OpenCV (H x W x 3)
            
        Returns:
            HolisticResults containing pose, face, and hand landmarks
        """
        
    def should_skip_frame(self) -> bool:
        """
        Determine if current frame should be skipped based on performance.
        
        Returns:
            True if frame should be skipped
        """
        
    def release(self):
        """Release MediaPipe resources."""
```

**Data Structures**:
```python
@dataclass
class HolisticResults:
    pose_landmarks: Optional[List[Landmark]]  # 33 points
    face_landmarks: Optional[List[Landmark]]  # 468 points
    left_hand_landmarks: Optional[List[Landmark]]  # 21 points
    right_hand_landmarks: Optional[List[Landmark]]  # 21 points
    timestamp: float
    frame_number: int
    
@dataclass
class Landmark:
    x: float  # Normalized 0.0-1.0
    y: float  # Normalized 0.0-1.0
    z: float  # Depth (relative scale)
    visibility: float  # Confidence 0.0-1.0
```

### 2. SignalSmoother Class

**Purpose**: Apply One Euro Filter to landmark coordinates to reduce jitter.

**Location**: `engine/signal_smoother.py`

**Interface**:
```python
class SignalSmoother:
    def __init__(self, 
                 freq: float = 30.0,
                 min_cutoff: float = 1.0,
                 beta: float = 0.0,
                 d_cutoff: float = 1.0):
        """
        Initialize One Euro Filter for each coordinate.
        
        Args:
            freq: Sampling frequency (Hz)
            min_cutoff: Minimum cutoff frequency
            beta: Speed coefficient
            d_cutoff: Cutoff for derivative
        """
        
    def smooth_landmarks(self, 
                        landmarks: List[Landmark], 
                        timestamp: float) -> List[Landmark]:
        """
        Apply smoothing filter to all landmarks.
        
        Args:
            landmarks: Raw landmark list
            timestamp: Current timestamp in seconds
            
        Returns:
            Smoothed landmark list
        """
        
    def reset(self):
        """Reset all filter states."""
```

**Implementation Notes**:
- Maintain separate filter instances for each landmark's x, y, z coordinates
- Use lazy initialization (create filters on first use)
- Store filter state in dictionary keyed by landmark index

### 3. PostureAnalyzer Class

**Purpose**: Analyze body posture including shoulder alignment, slouching, and arm position.

**Location**: `engine/analyzers/posture_analyzer.py`

**Interface**:
```python
class PostureAnalyzer:
    def __init__(self, 
                 shoulder_angle_threshold: float = 15.0,
                 slouch_threshold: float = 0.1,
                 rock_threshold: float = 0.02):
        """
        Initialize posture analysis thresholds.
        
        Args:
            shoulder_angle_threshold: Max shoulder tilt in degrees
            slouch_threshold: Vertical distance change for slouch
            rock_threshold: Horizontal movement for rocking detection
        """
        
    def analyze(self, results: HolisticResults) -> PostureMetrics:
        """
        Analyze posture from holistic landmarks.
        
        Args:
            results: Smoothed holistic results
            
        Returns:
            PostureMetrics containing all posture indicators
        """
        
    def _calculate_shoulder_angle(self, 
                                  left_shoulder: Landmark, 
                                  right_shoulder: Landmark) -> float:
        """Calculate angle of line between shoulders."""
        
    def _detect_slouch(self, 
                      nose: Landmark, 
                      shoulders: Tuple[Landmark, Landmark]) -> bool:
        """Detect if user is slouching."""
        
    def _detect_arms_crossed(self, 
                            left_wrist: Landmark, 
                            right_wrist: Landmark) -> bool:
        """Detect if arms are crossed."""
        
    def _detect_rocking(self, shoulders: Tuple[Landmark, Landmark]) -> float:
        """Calculate rocking/fidgeting score."""
```

**Data Structures**:
```python
@dataclass
class PostureMetrics:
    shoulder_angle: float  # Degrees from horizontal
    is_leaning: bool  # Angle > threshold
    is_slouching: bool  # Nose too close to shoulders
    slouch_score: float  # 0.0-1.0 severity
    arms_crossed: bool  # Wrists crossed
    rocking_score: float  # Horizontal instability
    shoulder_stability: float  # 0.0-1.0 (1.0 = stable)
    timestamp: float
```

### 4. GestureAnalyzer Class

**Purpose**: Track hand gestures and face-touching behavior.

**Location**: `engine/analyzers/gesture_analyzer.py`

**Interface**:
```python
class GestureAnalyzer:
    def __init__(self, 
                 face_touch_threshold: float = 0.1,
                 gesture_height_threshold: float = 0.1):
        """
        Initialize gesture analysis parameters.
        
        Args:
            face_touch_threshold: Distance for face-touch detection
            gesture_height_threshold: Height above shoulders for gesture
        """
        
    def analyze(self, results: HolisticResults) -> GestureMetrics:
        """
        Analyze hand gestures and movements.
        
        Args:
            results: Smoothed holistic results
            
        Returns:
            GestureMetrics containing gesture indicators
        """
        
    def _detect_face_touch(self, 
                          hand_landmarks: List[Landmark], 
                          face_landmarks: List[Landmark]) -> bool:
        """Check if fingertips are near face."""
        
    def _count_active_gestures(self, 
                              hand_landmarks: List[Landmark], 
                              shoulder_y: float) -> int:
        """Count expressive hand movements."""
        
    def get_session_summary(self) -> GestureSummary:
        """Get aggregate gesture statistics for session."""
```

**Data Structures**:
```python
@dataclass
class GestureMetrics:
    left_hand_visible: bool
    right_hand_visible: bool
    face_touch_detected: bool  # Either hand
    face_touch_count: int  # Cumulative
    active_gesture_count: int  # Current frame
    gesture_frequency: float  # Gestures per minute
    hand_activity_level: str  # "passive", "moderate", "dynamic"
    timestamp: float
    
@dataclass
class GestureSummary:
    total_face_touches: int
    total_gestures: int
    average_gestures_per_minute: float
    classification: str  # "passive", "moderate", "dynamic"
```

### 5. StressAnalyzer Class

**Purpose**: Detect stress indicators through blink rate and lip compression.

**Location**: `engine/analyzers/stress_analyzer.py`

**Interface**:
```python
class StressAnalyzer:
    def __init__(self, 
                 ear_threshold: float = 0.2,
                 blink_rate_threshold: float = 30.0,
                 lip_compression_threshold: float = 0.02):
        """
        Initialize stress detection parameters.
        
        Args:
            ear_threshold: Eye Aspect Ratio for blink detection
            blink_rate_threshold: Blinks per minute for stress
            lip_compression_threshold: Lip distance for pursing
        """
        
    def analyze(self, results: HolisticResults, 
                is_speaking: bool) -> StressMetrics:
        """
        Analyze stress indicators from facial landmarks.
        
        Args:
            results: Smoothed holistic results
            is_speaking: Whether user is currently speaking
            
        Returns:
            StressMetrics containing stress indicators
        """
        
    def _calculate_ear(self, eye_landmarks: List[Landmark]) -> float:
        """Calculate Eye Aspect Ratio."""
        
    def _detect_blink(self, ear: float) -> bool:
        """Detect if current frame shows a blink."""
        
    def _calculate_lip_distance(self, face_landmarks: List[Landmark]) -> float:
        """Calculate distance between upper and lower lip."""
        
    def _detect_lip_pursing(self, lip_distance: float, 
                           is_speaking: bool) -> bool:
        """Detect sustained lip compression."""
```

**Data Structures**:
```python
@dataclass
class StressMetrics:
    left_ear: float  # Eye Aspect Ratio
    right_ear: float
    blink_detected: bool
    blink_count: int  # Cumulative
    blink_rate: float  # Per minute
    high_cognitive_load: bool  # Rate > threshold
    lip_distance: float
    lip_pursing_detected: bool
    lip_purse_duration: float  # Seconds
    stress_level: str  # "low", "moderate", "high"
    timestamp: float
```

### 6. IntegrityChecker Class

**Purpose**: Detect suspicious gaze patterns indicating note-reading.

**Location**: `engine/analyzers/integrity_checker.py`

**Interface**:
```python
class IntegrityChecker:
    def __init__(self, 
                 gaze_cluster_threshold: float = 0.05,
                 cheat_flag_threshold: int = 5):
        """
        Initialize integrity checking parameters.
        
        Args:
            gaze_cluster_threshold: Distance for same-location detection
            cheat_flag_threshold: Flags before warning
        """
        
    def analyze(self, results: HolisticResults, 
                speech_onset: bool) -> IntegrityMetrics:
        """
        Analyze gaze patterns for suspicious behavior.
        
        Args:
            results: Smoothed holistic results
            speech_onset: Whether user just started speaking
            
        Returns:
            IntegrityMetrics containing integrity indicators
        """
        
    def _calculate_gaze_position(self, face_landmarks: List[Landmark]) -> Tuple[float, float]:
        """Estimate gaze direction from eye landmarks."""
        
    def _detect_repeated_pattern(self, gaze_pos: Tuple[float, float]) -> bool:
        """Check if gaze repeatedly goes to same location."""
        
    def get_session_report(self) -> IntegrityReport:
        """Generate integrity report for session."""
```

**Data Structures**:
```python
@dataclass
class IntegrityMetrics:
    gaze_x: float  # Normalized gaze position
    gaze_y: float
    suspicious_pattern_detected: bool
    cheat_flag_count: int  # Cumulative
    integrity_warning: bool  # Count > threshold
    confidence: float  # 0.0-1.0
    timestamp: float
    
@dataclass
class IntegrityReport:
    total_flags: int
    suspicious_segments: List[Tuple[float, float]]  # (start, end) times
    integrity_score: float  # 0.0-1.0 (1.0 = clean)
    recommendation: str
```

### 7. Enhanced VisionEngine Class

**Purpose**: Orchestrate all analyzers and provide unified interface.

**Location**: `engine/vision_engine.py` (refactored)

**Interface**:
```python
class VisionEngine:
    def __init__(self):
        """Initialize all sub-components."""
        self.holistic_processor = HolisticProcessor()
        self.signal_smoother = SignalSmoother()
        self.posture_analyzer = PostureAnalyzer()
        self.gesture_analyzer = GestureAnalyzer()
        self.stress_analyzer = StressAnalyzer()
        self.integrity_checker = IntegrityChecker()
        
    def analyze_frame(self, frame: np.ndarray, 
                     is_speaking: bool = False,
                     speech_onset: bool = False) -> ComprehensiveMetrics:
        """
        Perform complete analysis on a video frame.
        
        Args:
            frame: BGR image from OpenCV
            is_speaking: Whether user is currently speaking
            speech_onset: Whether user just started speaking
            
        Returns:
            ComprehensiveMetrics containing all analysis results
        """
        
    def get_session_summary(self) -> SessionSummary:
        """Get aggregate statistics for entire session."""
        
    def release(self):
        """Release all resources."""
```

**Data Structures**:
```python
@dataclass
class ComprehensiveMetrics:
    # Legacy compatibility
    eye_contact_score: float
    fidget_score: float
    is_smiling: bool
    is_stressed: bool
    
    # New metrics
    posture: PostureMetrics
    gestures: GestureMetrics
    stress: StressMetrics
    integrity: IntegrityMetrics
    
    # Meta
    processing_time_ms: float
    frame_number: int
    timestamp: float
    
@dataclass
class SessionSummary:
    duration_seconds: float
    total_frames_processed: int
    average_fps: float
    
    # Posture summary
    slouch_percentage: float
    average_shoulder_angle: float
    arms_crossed_percentage: float
    
    # Gesture summary
    gesture_summary: GestureSummary
    
    # Stress summary
    average_blink_rate: float
    high_stress_percentage: float
    
    # Integrity summary
    integrity_report: IntegrityReport
```

## Data Models

### Landmark Index Reference

**Pose Landmarks (33 points)**:
- 0: Nose
- 11: Left Shoulder
- 12: Right Shoulder
- 15: Left Wrist
- 16: Right Wrist
- 23: Left Hip
- 24: Right Hip

**Face Landmarks (468 points)**:
- 1: Nose tip
- 33: Left eye inner corner
- 133: Left eye outer corner
- 263: Right eye inner corner
- 362: Right eye outer corner
- 13: Upper lip center
- 14: Lower lip center
- 61: Left mouth corner
- 291: Right mouth corner

**Hand Landmarks (21 points per hand)**:
- 0: Wrist
- 4: Thumb tip
- 8: Index finger tip
- 12: Middle finger tip
- 16: Ring finger tip
- 20: Pinky tip

### Database Schema Extensions

Extend `InterviewSession` to store new metrics:

```python
class InterviewSession:
    # Existing fields...
    
    # New fields for advanced metrics
    posture_history: List[PostureMetrics] = []
    gesture_history: List[GestureMetrics] = []
    stress_history: List[StressMetrics] = []
    integrity_history: List[IntegrityMetrics] = []
    
    def log_comprehensive_metrics(self, metrics: ComprehensiveMetrics):
        """Store all metrics for later analysis."""
        
    def get_comprehensive_report(self) -> Dict:
        """Generate detailed report with all metrics."""
```

## Error Handling

### Graceful Degradation Strategy

1. **No Pose Landmarks**: Fall back to face-only analysis (legacy mode)
2. **No Hand Landmarks**: Disable gesture analysis, continue with posture
3. **Low Confidence**: Skip frame and use previous metrics
4. **Performance Issues**: Automatically enable frame skipping
5. **Model Load Failure**: Fall back to basic FaceMesh model

### Error Scenarios

```python
class VisionEngineError(Exception):
    """Base exception for vision engine errors."""
    
class ModelLoadError(VisionEngineError):
    """Failed to load MediaPipe model."""
    
class ProcessingTimeoutError(VisionEngineError):
    """Frame processing exceeded time limit."""
    
class InsufficientLandmarksError(VisionEngineError):
    """Not enough landmarks detected for analysis."""
```

### Error Handling Pattern

```python
def analyze_frame(self, frame: np.ndarray) -> ComprehensiveMetrics:
    try:
        # Process frame
        results = self.holistic_processor.process_frame(frame)
        
        if not results.pose_landmarks:
            # Graceful degradation
            return self._fallback_analysis(results)
            
        # Continue with full analysis...
        
    except ProcessingTimeoutError:
        logger.warning("Frame processing timeout, skipping")
        return self._get_last_valid_metrics()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return self._get_default_metrics()
```

## Testing Strategy

### Unit Tests

**Test Coverage Areas**:
1. **HolisticProcessor**: Mock MediaPipe, test landmark extraction
2. **SignalSmoother**: Test filter convergence and jitter reduction
3. **PostureAnalyzer**: Test angle calculations with known coordinates
4. **GestureAnalyzer**: Test face-touch detection with synthetic data
5. **StressAnalyzer**: Test EAR calculation and blink detection
6. **IntegrityChecker**: Test pattern detection with scripted gaze data

**Example Test**:
```python
def test_shoulder_angle_calculation():
    analyzer = PostureAnalyzer()
    
    # Perfect horizontal shoulders
    left = Landmark(x=0.3, y=0.5, z=0, visibility=1.0)
    right = Landmark(x=0.7, y=0.5, z=0, visibility=1.0)
    angle = analyzer._calculate_shoulder_angle(left, right)
    assert abs(angle) < 1.0  # Nearly 0 degrees
    
    # 15-degree tilt
    right_tilted = Landmark(x=0.7, y=0.55, z=0, visibility=1.0)
    angle = analyzer._calculate_shoulder_angle(left, right_tilted)
    assert 14.0 < angle < 16.0
```

### Integration Tests

1. **End-to-End Pipeline**: Feed pre-recorded video, verify all metrics
2. **WebSocket Flow**: Test frame upload and metric streaming
3. **Performance Test**: Measure FPS with all analyzers active
4. **Stress Test**: Process 1000 frames, check memory leaks

### Manual Testing Scenarios

1. **Posture Test**: Deliberately slouch, lean, cross arms - verify detection
2. **Gesture Test**: Touch face, wave hands - verify counting
3. **Stress Test**: Blink rapidly, purse lips - verify detection
4. **Integrity Test**: Look at notes repeatedly - verify flags

## Performance Considerations

### Optimization Strategies

1. **Frame Skipping**: Process every 2nd frame under load (30 FPS → 15 FPS)
2. **Lazy Initialization**: Create filters only for detected landmarks
3. **Vectorized Operations**: Use NumPy for batch calculations
4. **Caching**: Store previous frame results for interpolation
5. **Async Processing**: Run analysis in separate thread pool

### Performance Targets

- **Latency**: < 100ms per frame on standard hardware
- **Throughput**: Minimum 15 FPS sustained
- **Memory**: < 500MB total for vision engine
- **CPU**: < 80% on dual-core processor

### Profiling Points

```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.timings = defaultdict(list)
        
    def measure(self, operation: str):
        """Context manager for timing operations."""
        return TimingContext(self, operation)
        
    def get_report(self) -> Dict[str, float]:
        """Get average timing for each operation."""
        return {
            op: sum(times) / len(times) 
            for op, times in self.timings.items()
        }
```

## Security and Privacy

### Data Handling

1. **No Storage**: Landmarks processed in-memory only
2. **No Recording**: Video frames not saved to disk
3. **Session Isolation**: Each session has independent state
4. **Secure Transmission**: WebSocket over TLS in production

### Privacy Considerations

1. **Consent**: User must explicitly enable camera
2. **Transparency**: Show which metrics are being tracked
3. **Control**: Allow disabling specific analyzers
4. **Deletion**: Clear all session data on completion

## Deployment Considerations

### Dependencies

```txt
# Add to requirements.txt
mediapipe>=0.10.0
opencv-python>=4.8.0
numpy>=1.24.0
scipy>=1.11.0  # For signal processing
one-euro-filter>=0.1.0  # Or custom implementation
```

### Configuration

```python
# config.py
class VisionConfig:
    # MediaPipe settings
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5
    ENABLE_SEGMENTATION = False  # Save CPU
    
    # Performance settings
    ENABLE_FRAME_SKIP = True
    TARGET_FPS = 15
    MAX_PROCESSING_TIME_MS = 100
    
    # Analysis thresholds
    SHOULDER_ANGLE_THRESHOLD = 15.0
    SLOUCH_THRESHOLD = 0.1
    FACE_TOUCH_THRESHOLD = 0.1
    EAR_THRESHOLD = 0.2
    BLINK_RATE_THRESHOLD = 30.0
    
    # Feature flags
    ENABLE_POSTURE_ANALYSIS = True
    ENABLE_GESTURE_ANALYSIS = True
    ENABLE_STRESS_ANALYSIS = True
    ENABLE_INTEGRITY_CHECK = True
```

### Hardware Requirements

**Minimum**:
- CPU: Dual-core 2.0 GHz
- RAM: 4GB
- Webcam: 720p @ 30fps

**Recommended**:
- CPU: Quad-core 2.5 GHz
- RAM: 8GB
- Webcam: 1080p @ 30fps
- GPU: Optional (MediaPipe can use GPU acceleration)

## Migration Path

### Phase 1: Parallel Implementation
- Keep existing `VisionEngine` functional
- Implement new components alongside
- Add feature flag to switch between old/new

### Phase 2: Gradual Rollout
- Enable new features one at a time
- Monitor performance metrics
- Collect user feedback

### Phase 3: Full Migration
- Remove legacy code
- Update all frontend references
- Update documentation

### Backward Compatibility

```python
class VisionEngine:
    def analyze_frame(self, landmarks_or_frame, **kwargs):
        """
        Backward compatible interface.
        
        Accepts either:
        - Old format: landmarks dict (legacy)
        - New format: raw frame (holistic)
        """
        if isinstance(landmarks_or_frame, dict):
            # Legacy mode
            return self._legacy_analyze(landmarks_or_frame)
        else:
            # New mode
            return self._holistic_analyze(landmarks_or_frame, **kwargs)
```

## Future Enhancements

### Potential Additions

1. **Voice-Posture Correlation**: Analyze if posture changes during speech
2. **Emotion Recognition**: Classify facial expressions (happy, nervous, confident)
3. **Attention Tracking**: Measure engagement through gaze focus
4. **Breathing Rate**: Estimate from shoulder movement patterns
5. **Energy Level**: Classify overall body language as energetic/lethargic
6. **Cultural Adaptation**: Adjust thresholds for different cultural norms

### Research Opportunities

1. **ML-Based Classification**: Train model to classify "good" vs "poor" interview posture
2. **Personalized Baselines**: Learn individual's normal behavior patterns
3. **Predictive Analytics**: Predict interview outcome from body language
4. **Real-time Coaching**: Provide live suggestions during interview

## References

- MediaPipe Holistic Documentation: https://google.github.io/mediapipe/solutions/holistic
- One Euro Filter Paper: Casiez et al., "1€ Filter: A Simple Speed-based Low-pass Filter"
- Eye Aspect Ratio: Soukupová & Čech, "Real-Time Eye Blink Detection"
- Posture Analysis: Ergonomics research on shoulder alignment
- Gesture Recognition: HCI research on hand tracking
