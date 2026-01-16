# Requirements Document

## Introduction

This specification defines the advanced vision analysis system for The Interview Mirror application. The system will upgrade from basic facial tracking to full-body holistic analysis, enabling detection of power posture, hand gestures, micro-expressions, and anti-cheating behaviors during mock interviews.

## Glossary

- **Vision System**: The MediaPipe-based computer vision pipeline that processes video frames to extract behavioral metrics
- **Holistic Model**: MediaPipe's unified model that tracks face (468 landmarks), pose (33 landmarks), and hands (21 landmarks per hand)
- **Posture Engine**: The subsystem that analyzes shoulder alignment, spine position, and body stability
- **Gesture Intelligence**: The subsystem that tracks hand movements and face-touching behaviors
- **Stress Signals**: Micro-movements like blink rate and lip compression that indicate cognitive load
- **Signal Smoothing**: Mathematical filtering applied to raw landmark coordinates to reduce jitter
- **One Euro Filter**: An adaptive low-pass filter that reduces noise while preserving responsiveness
- **Eye Aspect Ratio (EAR)**: A mathematical metric derived from eye landmark distances to detect blinks
- **Normalized Coordinates**: Landmark positions scaled to 0.0-1.0 range relative to frame dimensions
- **Backend API**: The FastAPI server that processes frames and returns analysis results

## Requirements

### Requirement 1: MediaPipe Holistic Integration

**User Story:** As a developer, I want to upgrade from FaceMesh to MediaPipe Holistic, so that the system can track full-body landmarks including shoulders, hands, and face simultaneously.

#### Acceptance Criteria

1. WHEN the Vision System initializes, THE Vision System SHALL load the MediaPipe Holistic model with minimum detection confidence of 0.5
2. WHEN a video frame is received, THE Vision System SHALL process the frame and extract pose landmarks, face landmarks, left hand landmarks, and right hand landmarks
3. WHEN processing performance degrades, THE Vision System SHALL skip alternate frames to maintain real-time performance
4. WHERE frame rate drops below 15 FPS, THE Vision System SHALL enable frame skipping automatically
5. WHEN landmarks are extracted, THE Vision System SHALL provide 33 pose landmarks, 468 face landmarks, and 21 landmarks per hand

### Requirement 2: Power Posture Analysis

**User Story:** As an interview candidate, I want real-time feedback on my posture, so that I can maintain confident body language throughout the interview.

#### Acceptance Criteria

1. WHEN shoulder landmarks are detected, THE Posture Engine SHALL calculate the angle between left shoulder (landmark 11) and right shoulder (landmark 12)
2. IF the shoulder angle exceeds 15 degrees, THEN THE Posture Engine SHALL flag a "leaning" posture warning
3. WHEN nose position (landmark 0) and shoulder average Y-coordinate are tracked, THE Posture Engine SHALL calculate vertical distance between them
4. IF the vertical distance decreases by more than 0.1 normalized units, THEN THE Posture Engine SHALL flag a "slouching" warning
5. WHILE tracking shoulder X-coordinates across frames, THE Posture Engine SHALL detect horizontal oscillations exceeding threshold epsilon
6. WHEN left wrist X-coordinate exceeds right wrist X-coordinate, THE Posture Engine SHALL flag "arms crossed" body language

### Requirement 3: Hand Gesture Intelligence

**User Story:** As an interviewer AI, I want to analyze hand gestures, so that I can assess the candidate's communication style and nervousness levels.

#### Acceptance Criteria

1. WHEN hand landmarks and face landmarks are both detected, THE Gesture Intelligence SHALL calculate Euclidean distance between index finger tip and nose landmark
2. IF the distance is less than 0.1 normalized units, THEN THE Gesture Intelligence SHALL increment the face-touching counter
3. WHILE hands are visible, THE Gesture Intelligence SHALL track hand movement frequency by comparing positions across frames
4. WHEN hand extends above shoulder line by more than 0.1 normalized units, THE Gesture Intelligence SHALL increment the gesture counter
5. WHEN the interview session ends, THE Gesture Intelligence SHALL calculate gesture frequency as gestures per minute and classify as "dynamic speaker" or "passive speaker"

### Requirement 4: Advanced Stress Signal Detection

**User Story:** As a coach, I want to detect subtle stress indicators like blink rate and lip compression, so that I can provide targeted feedback on managing interview anxiety.

#### Acceptance Criteria

1. WHEN eye landmarks are detected, THE Vision System SHALL calculate Eye Aspect Ratio using the formula EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
2. WHEN EAR drops below 0.2 threshold, THE Vision System SHALL increment the blink counter
3. WHEN blink rate exceeds 30 blinks per minute, THE Vision System SHALL flag high cognitive load
4. WHEN upper lip landmark and lower lip landmark are detected, THE Vision System SHALL calculate the distance between them
5. IF lip distance remains below 0.02 normalized units for more than 3 consecutive seconds while not speaking, THEN THE Vision System SHALL flag "lip pursing" anxiety indicator

### Requirement 5: Anti-Cheating Integrity Check

**User Story:** As an interview administrator, I want to detect if candidates are reading from notes, so that I can ensure interview integrity.

#### Acceptance Criteria

1. WHEN speech onset is detected, THE Vision System SHALL record the average eye landmark position
2. WHEN eye position consistently moves to the same off-screen coordinate (within 0.05 normalized units) at speech onset, THE Vision System SHALL increment the cheat flag counter
3. IF cheat flag counter exceeds 5 occurrences in a single session, THEN THE Vision System SHALL raise an integrity warning
4. WHEN the session ends, THE Backend API SHALL include gaze pattern analysis in the final report

### Requirement 6: Signal Smoothing Implementation

**User Story:** As a developer, I want to apply mathematical smoothing to raw landmark data, so that metrics are stable and professional-looking without false positives from camera jitter.

#### Acceptance Criteria

1. WHEN raw landmark coordinates are extracted, THE Vision System SHALL apply One Euro Filter to X, Y, and Z coordinates
2. THE One Euro Filter SHALL be initialized with frequency of 30 Hz, minimum cutoff of 1.0, and beta of 0.0
3. WHEN landmark velocity increases, THE One Euro Filter SHALL adapt cutoff frequency to preserve responsiveness
4. WHEN smoothed coordinates are used for metric calculation, THE Vision System SHALL produce fidget scores with less than 10% variance for stationary subjects
5. THE Vision System SHALL maintain separate filter instances for each tracked landmark coordinate

### Requirement 7: Backend API Integration

**User Story:** As a frontend developer, I want RESTful endpoints that return comprehensive analysis results, so that I can display real-time feedback to users.

#### Acceptance Criteria

1. THE Backend API SHALL expose a POST endpoint at /analyze that accepts video frame uploads
2. WHEN a frame is received, THE Backend API SHALL return JSON containing shoulder_angle, slouch_flag, arms_crossed, face_touch_count, blink_rate, lip_purse_flag, and gaze_dart_flag
3. THE Backend API SHALL process frames and return results within 100 milliseconds for real-time feedback
4. WHEN WebSocket connection is active, THE Backend API SHALL stream analysis results at minimum 10 updates per second
5. THE Backend API SHALL integrate analysis results with the existing Gemini AI conversational engine

### Requirement 8: Performance Optimization

**User Story:** As a user, I want the vision analysis to run smoothly on standard hardware, so that I can practice interviews without lag or stuttering.

#### Acceptance Criteria

1. THE Vision System SHALL maintain minimum 15 FPS processing rate on hardware with 4GB RAM and dual-core CPU
2. WHEN CPU usage exceeds 80%, THE Vision System SHALL automatically reduce processing frequency
3. THE Vision System SHALL process frames asynchronously to avoid blocking the main application thread
4. WHEN multiple analysis modules are active, THE Vision System SHALL prioritize critical metrics (posture, face-touch) over secondary metrics (gesture frequency)
5. THE Vision System SHALL release GPU resources when not actively processing frames
