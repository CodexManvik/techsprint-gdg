"""
Live camera test for PostureAnalyzer with visual feedback.
Press 'q' to quit.
"""

import cv2
import mediapipe as mp
import time
from engine.analyzers.posture_analyzer import PostureAnalyzer, Landmark


def mediapipe_to_landmark(mp_landmark) -> Landmark:
    """Convert MediaPipe landmark to our Landmark format."""
    return Landmark(
        x=mp_landmark.x,
        y=mp_landmark.y,
        z=mp_landmark.z,
        visibility=mp_landmark.visibility if hasattr(mp_landmark, 'visibility') else 1.0
    )


def draw_metrics(frame, metrics, fps, is_calibrated):
    """Draw posture metrics on the frame."""
    h, w = frame.shape[:2]
    
    # Semi-transparent overlay for text background
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (450, 300), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    
    # Title
    cv2.putText(frame, "POSTURE ANALYSIS", (20, 40), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
    
    # Calibration status
    if not is_calibrated:
        cv2.putText(frame, "CALIBRATING... Sit upright!", (20, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    else:
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    y_offset = 100
    
    # Shoulder angle
    angle_color = (0, 0, 255) if metrics.is_leaning else (0, 255, 0)
    cv2.putText(frame, f"Shoulder Angle: {metrics.shoulder_angle:.1f}deg", 
                (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, angle_color, 2)
    y_offset += 30
    
    # Leaning status
    lean_text = "LEANING!" if metrics.is_leaning else "Level"
    lean_color = (0, 0, 255) if metrics.is_leaning else (0, 255, 0)
    cv2.putText(frame, f"Status: {lean_text}", 
                (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, lean_color, 2)
    y_offset += 30
    
    # Slouch detection
    slouch_color = (0, 165, 255) if metrics.is_slouching else (0, 255, 0)
    slouch_text = f"Slouching: {'YES' if metrics.is_slouching else 'NO'} ({metrics.slouch_score:.2f})"
    cv2.putText(frame, slouch_text, 
                (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, slouch_color, 2)
    y_offset += 30
    
    # Arms crossed - BIG INDICATOR
    if metrics.arms_crossed:
        cv2.putText(frame, "ARMS CROSSED!", 
                    (20, y_offset), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 3)
        # Also draw a big warning box
        cv2.rectangle(frame, (w-250, 10), (w-10, 80), (0, 0, 255), 3)
        cv2.putText(frame, "ARMS", (w-230, 40), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, "CROSSED!", (w-230, 65), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Arms: Open", 
                    (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    y_offset += 30
    
    # Stability
    stability_color = (0, 255, 0) if metrics.shoulder_stability > 0.8 else (0, 165, 255)
    cv2.putText(frame, f"Stability: {metrics.shoulder_stability:.2f}", 
                (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, stability_color, 2)
    y_offset += 30
    
    # Rocking score
    rock_color = (0, 0, 255) if metrics.rocking_score > 0.5 else (0, 255, 0)
    cv2.putText(frame, f"Rocking: {metrics.rocking_score:.2f}", 
                (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, rock_color, 2)
    
    # Instructions
    cv2.putText(frame, "Press 'q' to quit", (20, h - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame


def main():
    """Run live camera test."""
    print("="*60)
    print("LIVE POSTURE ANALYZER TEST")
    print("="*60)
    print("\nInitializing camera and MediaPipe...")
    
    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
    
    # Initialize PostureAnalyzer
    analyzer = PostureAnalyzer(
        shoulder_angle_threshold=15.0,
        slouch_threshold=0.05,
        rock_threshold=0.02,
        arms_crossed_frames=10
    )
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera")
        return 1
    
    print("✅ Camera opened successfully")
    print("\nInstructions:")
    print("  1. SIT UPRIGHT for the first few seconds (calibration)")
    print("  2. Then try slouching forward to test detection")
    print("  3. Try crossing your arms")
    print("  4. Try leaning left/right")
    print("  - Press 'q' to quit")
    print("\n" + "="*60 + "\n")
    
    # FPS calculation
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not read frame")
            break
        
        # Flip frame horizontally for mirror view
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = pose.process(rgb_frame)
        
        # Draw pose landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # Convert to our Landmark format
            pose_landmarks = [
                mediapipe_to_landmark(lm) 
                for lm in results.pose_landmarks.landmark
            ]
            
            # Analyze posture
            metrics = analyzer.analyze(pose_landmarks, time.time())
            
            # Check if calibrated
            is_calibrated = analyzer.baseline_nose_shoulder_dist is not None
            
            # Draw metrics on frame
            frame = draw_metrics(frame, metrics, fps, is_calibrated)
        else:
            # No pose detected
            cv2.putText(frame, "No pose detected - step back from camera", 
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Calculate FPS
        frame_count += 1
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
        
        # Show frame
        cv2.imshow('Posture Analyzer - Live Test', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n✅ Test completed")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
    
    print(f"\nFinal stats:")
    print(f"  Average FPS: {fps:.1f}")
    print(f"  Total frames: {frame_count}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
