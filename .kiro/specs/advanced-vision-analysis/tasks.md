# Implementation Plan

- [x] 1. Setup MediaPipe Holistic Infrastructure



  - Create `engine/holistic_processor.py` with MediaPipe Holistic initialization
  - Implement frame preprocessing and landmark extraction for 543 points (33 pose + 468 face + 42 hands)
  - Add frame skipping logic based on CPU load and FPS monitoring
  - Implement resource cleanup and error handling for model loading failures
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement Signal Smoothing Layer



  - Create `engine/signal_smoother.py` with One Euro Filter implementation
  - Initialize separate filter instances for each landmark's x, y, z coordinates
  - Implement adaptive smoothing that adjusts cutoff frequency based on landmark velocity
  - Add filter reset functionality for new sessions
  - Verify jitter reduction produces stable metrics with <10% variance for stationary subjects
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 3. Build Posture Analysis Engine
- [x] 3.1 Create PostureAnalyzer class structure


  - Create `engine/analyzers/posture_analyzer.py` with class skeleton
  - Define PostureMetrics dataclass with all required fields
  - Initialize configurable thresholds (shoulder_angle=15°, slouch=0.1, rock=0.02)
  - _Requirements: 2.1, 2.2_

- [x] 3.2 Implement shoulder alignment detection

  - Write `_calculate_shoulder_angle()` method using landmarks 11 and 12
  - Calculate angle using atan2(dy, dx) and convert to degrees
  - Flag "leaning" when angle exceeds 15 degrees threshold
  - _Requirements: 2.1, 2.2_


- [ ] 3.3 Implement slouch detection
  - Write `_detect_slouch()` method comparing nose (landmark 0) to shoulder average Y
  - Calculate vertical distance between nose and shoulder midpoint
  - Flag slouching when distance decreases by >0.1 normalized units
  - Track slouch severity score (0.0-1.0)
  - _Requirements: 2.3, 2.4_

- [x] 3.4 Implement arms-crossed detection

  - Write `_detect_arms_crossed()` method using wrist landmarks 15 and 16
  - Compare X-coordinates: flag when left_wrist.x > right_wrist.x
  - Add vertical range check to ensure wrists are near chest area
  - _Requirements: 2.6_


- [ ] 3.5 Implement rocking/stability detection
  - Write `_detect_rocking()` method tracking shoulder X-coordinates across frames
  - Maintain history buffer of last 30 shoulder positions
  - Calculate horizontal oscillation frequency and amplitude
  - Generate shoulder_stability score (1.0 = perfectly stable)
  - _Requirements: 2.5_


- [x] 3.6 Integrate all posture metrics

  - Implement main `analyze()` method that calls all sub-methods
  - Return comprehensive PostureMetrics dataclass
  - Add error handling for missing landmarks
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 4. Build Gesture Intelligence System
- [x] 4.1 Create GestureAnalyzer class structure


  - Create `engine/analyzers/gesture_analyzer.py` with class skeleton
  - Define GestureMetrics and GestureSummary dataclasses
  - Initialize thresholds (face_touch=0.1, gesture_height=0.1)
  - _Requirements: 3.1, 3.2_

- [x] 4.2 Implement face-touching detection

  - Write `_detect_face_touch()` method for both hands
  - Calculate Euclidean distance between index finger tip (landmark 8) and nose (landmark 1)
  - Flag face-touch when distance < 0.1 normalized units
  - Maintain cumulative face_touch_count
  - _Requirements: 3.1, 3.2_

- [x] 4.3 Implement gesture frequency tracking

  - Write `_count_active_gestures()` method tracking hand elevation
  - Detect when hands extend above shoulder line by >0.1 units
  - Track hand movement velocity between frames
  - Increment gesture counter for expressive movements
  - _Requirements: 3.3, 3.4_

- [x] 4.4 Implement gesture classification

  - Calculate gestures per minute from total count and session duration
  - Classify as "passive" (<5/min), "moderate" (5-15/min), or "dynamic" (>15/min)
  - Implement `get_session_summary()` for aggregate statistics
  - _Requirements: 3.5_

- [x] 4.5 Integrate gesture analysis

  - Implement main `analyze()` method combining all gesture metrics
  - Handle cases where hands are not visible
  - Return comprehensive GestureMetrics dataclass
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Build Stress Signal Detection
- [x] 5.1 Create StressAnalyzer class structure
  - Create `engine/analyzers/stress_analyzer.py` with class skeleton
  - Define StressMetrics dataclass with all stress indicators
  - Initialize thresholds (EAR=0.2, blink_rate=30/min, lip_compression=0.02)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.2 Implement Eye Aspect Ratio calculation
  - Write `_calculate_ear()` method using eye landmark distances
  - Use formula: EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
  - Calculate for both left and right eyes separately
  - _Requirements: 4.1_

- [x] 5.3 Implement blink detection
  - Write `_detect_blink()` method comparing EAR to threshold (0.2)
  - Increment blink counter when EAR drops below threshold
  - Prevent double-counting by tracking eye state (open/closed)
  - Calculate blinks per minute from cumulative count and elapsed time
  - _Requirements: 4.2_

- [x] 5.4 Implement cognitive load detection
  - Flag high_cognitive_load when blink_rate exceeds 30/min
  - Track blink rate history for trend analysis
  - _Requirements: 4.3_

- [x] 5.5 Implement lip compression detection
  - Write `_calculate_lip_distance()` using upper (landmark 13) and lower (landmark 14) lip
  - Calculate Euclidean distance between lip landmarks
  - Write `_detect_lip_pursing()` checking sustained compression
  - Flag lip pursing when distance <0.02 for >3 seconds while not speaking
  - Track lip_purse_duration
  - _Requirements: 4.4, 4.5_

- [x] 5.6 Implement stress level classification
  - Combine blink rate and lip pursing into overall stress_level
  - Classify as "low", "moderate", or "high" based on multiple indicators
  - Integrate main `analyze()` method with is_speaking parameter
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Build Anti-Cheating Integrity Checker
- [x] 6.1 Create IntegrityChecker class structure
  - Create `engine/analyzers/integrity_checker.py` with class skeleton
  - Define IntegrityMetrics and IntegrityReport dataclasses
  - Initialize thresholds (gaze_cluster=0.05, cheat_flag=5)
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6.2 Implement gaze position estimation
  - Write `_calculate_gaze_position()` using eye landmark centroids
  - Average positions of left and right eye inner/outer corners
  - Return normalized (x, y) gaze coordinates
  - _Requirements: 5.1_

- [x] 6.3 Implement repeated pattern detection
  - Write `_detect_repeated_pattern()` tracking gaze at speech onset
  - Maintain history of gaze positions when user starts speaking
  - Cluster gaze positions within 0.05 normalized units
  - Increment cheat_flag when same cluster is repeatedly targeted
  - _Requirements: 5.2_

- [x] 6.4 Implement integrity warning system
  - Flag integrity_warning when cheat_flag_count exceeds 5
  - Track suspicious_segments with timestamps
  - Calculate integrity_score (1.0 = clean, 0.0 = highly suspicious)
  - Implement `get_session_report()` for final integrity assessment
  - _Requirements: 5.3, 5.4_

- [x] 6.5 Integrate integrity analysis
  - Implement main `analyze()` method with speech_onset parameter
  - Handle cases where face landmarks are insufficient
  - Return comprehensive IntegrityMetrics dataclass
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 7. Refactor and Integrate VisionEngine
- [ ] 7.1 Refactor existing VisionEngine class
  - Update `engine/vision_engine.py` to use new architecture
  - Initialize all sub-components (HolisticProcessor, SignalSmoother, all Analyzers)
  - Maintain backward compatibility with existing analyze_frame() interface
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7.2 Implement comprehensive frame analysis pipeline
  - Update `analyze_frame()` to accept raw frame instead of landmarks
  - Add is_speaking and speech_onset parameters
  - Call HolisticProcessor to extract landmarks
  - Apply SignalSmoother to all landmarks
  - Call all analyzers in sequence
  - Aggregate results into ComprehensiveMetrics dataclass
  - _Requirements: 7.1, 7.2_

- [ ] 7.3 Implement session summary generation
  - Write `get_session_summary()` method aggregating all analyzer summaries
  - Calculate percentages (slouch_percentage, arms_crossed_percentage, etc.)
  - Include gesture summary, stress averages, and integrity report
  - Return comprehensive SessionSummary dataclass
  - _Requirements: 7.2_

- [ ] 7.4 Add performance monitoring
  - Track processing_time_ms for each frame
  - Monitor FPS and trigger frame skipping when needed
  - Log performance metrics for optimization
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 7.5 Implement resource cleanup
  - Write `release()` method to free all resources
  - Close MediaPipe model properly
  - Clear all analyzer state
  - _Requirements: 7.1_

- [ ] 8. Update FastAPI Backend Integration
- [ ] 8.1 Update WebSocket handler for new metrics
  - Modify `/ws/interview/{session_id}` endpoint in `app.py`
  - Pass raw video frames to VisionEngine instead of landmarks
  - Add speech detection integration for is_speaking parameter
  - Stream comprehensive metrics to frontend
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8.2 Update session manager for new metrics
  - Extend `InterviewSession` class in `engine/session_manager.py`
  - Add storage for posture_history, gesture_history, stress_history, integrity_history
  - Implement `log_comprehensive_metrics()` method
  - Update `get_report_card()` to include all new metrics
  - _Requirements: 7.2_

- [ ] 8.3 Add configuration management
  - Create `config.py` with VisionConfig class
  - Define all thresholds and feature flags
  - Allow runtime configuration updates
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8.4 Implement graceful degradation
  - Add fallback logic when pose landmarks unavailable
  - Continue with face-only analysis if hands not detected
  - Return default metrics on processing errors
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 9. Update Frontend for New Metrics
- [ ] 9.1 Update HTML frontend metrics display
  - Modify `frontend/index.html` to show new posture metrics
  - Add UI elements for gesture frequency and face-touch count
  - Display stress indicators (blink rate, lip pursing)
  - Show integrity warnings when detected
  - _Requirements: 7.1, 7.2_

- [ ] 9.2 Update React frontend components
  - Modify `interview-mirror-frontend/src/App.jsx` Cockpit component
  - Add real-time visualization for shoulder angle and slouch detection
  - Create gesture activity indicator
  - Add stress level gauge
  - Display integrity score
  - _Requirements: 7.1, 7.2_

- [ ] 9.3 Implement results page enhancements
  - Update Results component to show comprehensive session summary
  - Add charts for posture trends over time (using Recharts)
  - Display gesture frequency analysis
  - Show stress pattern timeline
  - Include integrity report with recommendations
  - _Requirements: 7.2_

- [ ] 10. Performance Optimization
- [ ] 10.1 Implement frame skipping optimization
  - Add CPU usage monitoring
  - Automatically skip frames when CPU >80%
  - Maintain minimum 15 FPS target
  - _Requirements: 8.1, 8.2_

- [ ] 10.2 Optimize landmark processing
  - Use NumPy vectorized operations for distance calculations
  - Cache frequently accessed landmark positions
  - Implement lazy initialization for filters
  - _Requirements: 8.3, 8.4_

- [ ] 10.3 Add async processing
  - Move frame analysis to separate thread pool
  - Implement non-blocking WebSocket communication
  - Queue frames when processing falls behind
  - _Requirements: 8.3_

- [ ] 10.4 Profile and optimize bottlenecks
  - Add performance monitoring to all major operations
  - Identify and optimize slowest components
  - Ensure <100ms latency per frame
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 11. Testing and Validation
- [ ]* 11.1 Write unit tests for all analyzers
  - Test PostureAnalyzer with synthetic landmark data
  - Test GestureAnalyzer face-touch detection
  - Test StressAnalyzer EAR calculation and blink detection
  - Test IntegrityChecker pattern detection
  - Test SignalSmoother filter convergence
  - _Requirements: All_

- [ ]* 11.2 Create integration tests
  - Test end-to-end pipeline with pre-recorded video
  - Verify WebSocket metric streaming
  - Test session summary generation
  - Validate backward compatibility
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 11.3 Perform manual testing
  - Test posture detection by deliberately slouching and leaning
  - Test gesture tracking by touching face and waving hands
  - Test stress detection by blinking rapidly and pursing lips
  - Test integrity checker by reading from notes
  - Verify all metrics display correctly in UI
  - _Requirements: All_

- [ ]* 11.4 Performance testing
  - Run 1000-frame stress test and check for memory leaks
  - Measure sustained FPS on minimum hardware specs
  - Verify latency stays under 100ms
  - Test frame skipping under load
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Documentation and Deployment
- [ ] 12.1 Update requirements.txt
  - Add mediapipe>=0.10.0
  - Add scipy>=1.11.0 for signal processing
  - Add one-euro-filter>=0.1.0 or document custom implementation
  - Update opencv-python and numpy versions
  - _Requirements: All_

- [ ] 12.2 Create migration guide
  - Document breaking changes from old VisionEngine
  - Provide migration examples for existing code
  - Explain new metric structures
  - _Requirements: 7.1, 7.2_

- [ ] 12.3 Update README documentation
  - Document new features and capabilities
  - Add configuration options
  - Include hardware requirements
  - Provide troubleshooting guide
  - _Requirements: All_

- [ ] 12.4 Create API documentation
  - Document all new endpoints and WebSocket messages
  - Provide example requests and responses
  - Document metric data structures
  - Include integration examples
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
