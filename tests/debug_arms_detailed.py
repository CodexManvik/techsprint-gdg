"""
Detailed arms crossed detection debugging with visual feedback.
Shows exact landmark positions and detection logic step-by-step.
"""

import cv2
import time
import math
from engine.holistic_processor import HolisticProcessor
from engine.signal_smoother import SignalSmoother
from engine.analyzers.posture_analyzer import PostureAnalyzer, Landmark


def draw_debug_info(frame, pose_landmarks, arms_crossed, debug_data):
    """Draw detailed debug information on frame."""
    h, w = frame.shape[:2]
    
    if pose_landmarks is None:
        return
    
    # Draw landmarks
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    
    ls = pose_landmarks[LEFT_SHOULDER]
    rs = pose_landmarks[RIGHT_SHOULDER]
    lw = pose_landmarks[LEFT_WRIST]
    rw = pose_landmarks[RIGHT_WRIST]
    lh = pose_landmarks[LEFT_HIP]
    rh = pose_landmarks[RIGHT_HIP]
    
    # Draw shoulder line
    cv2.line(frame, 
             (int(ls.x * w), int(ls.y * h)),
             (int(rs.x * w), int(rs.y * h)),
             (0, 255, 0), 2)
    
    # Draw wrists
    cv2.circle(frame, (int(lw.x * w), int(lw.y * h)), 10, (255, 0, 0), -1)
    cv2.circle(frame, (int(rw.x * w), int(rw.y * h)), 10, (0, 0, 255), -1)
    
    # Draw shoulder center
    cx = (ls.x + rs.x) / 2.0
    cy = (ls.y + rs.y) / 2.0
    cv2.circle(frame, (int(cx * w), int(cy * h)), 8, (255, 255, 0), -1)
    
    # Draw torso box
    min_sx = min(ls.x, rs.x)
    max_sx = max(ls.x, rs.x)
    shoulder_y = cy
    hip_y = (lh.y + rh.y) / 2.0
    
    cv2.rectangle(frame,
                  (int(min_sx * w), int(shoulder_y * h)),
                  (int(max_sx * w), int(hip_y * h)),
                  (255, 255, 255), 1)
    
    # Display debug data
    y_offset = 30
    line_height = 25
    
    cv2.putText(frame, f"Arms: {'CROSSED' if arms_crossed else 'OPEN'}", 
                (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                (0, 0, 255) if arms_crossed else (0, 255, 0), 2)
    y_offset += line_height
    
    for key, value in debug_data.items():
        color = (0, 255, 0) if value else (0, 0, 255)
        if isinstance(value, float):
            text = f"{key}: {value:.3f}"
            color = (255, 255, 255)
        else:
            text = f"{key}: {value}"
        
        cv2.putText(frame, text, (10, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y_offset += line_height


def detect_arms_with_debug(left_wrist, right_wrist, left_shoulder, right_shoulder, 
                           left_hip, right_hip):
    """Arms detection with detailed debug output."""
    
    debug_data = {}
    
    # Visibility check
    debug_data['LW_vis'] = left_wrist.visibility
    debug_data['RW_vis'] = right_wrist.visibility
    
    if (left_wrist.visibility < 0.5 or right_wrist.visibility < 0.5):
        debug_data['CHECK_vis'] = False
        return False, debug_data
    
    debug_data['CHECK_vis'] = True
    
    # Calculate body midline and dimensions
    shoulder_cx = (left_shoulder.x + right_shoulder.x) / 2.0
    shoulder_cy = (left_shoulder.y + right_shoulder.y) / 2.0
    shoulder_width = abs(right_shoulder.x - left_shoulder.x)
    
    # Torso vertical bounds
    hip_y = (left_hip.y + right_hip.y) / 2.0
    
    # Check 1: Wrists cross midline
    midline_tolerance = shoulder_width * 0.1
    lw_crosses = left_wrist.x > (shoulder_cx - midline_tolerance)
    rw_crosses = right_wrist.x < (shoulder_cx + midline_tolerance)
    check1 = lw_crosses and rw_crosses
    
    debug_data['LW_x'] = left_wrist.x
    debug_data['RW_x'] = right_wrist.x
    debug_data['midline'] = shoulder_cx
    debug_data['CHECK_1_cross'] = check1
    
    if not check1:
        return False, debug_data
    
    # Check 2: Wrists close together
    wrist_distance = math.hypot(
        left_wrist.x - right_wrist.x,
        left_wrist.y - right_wrist.y
    )
    check2 = wrist_distance < (shoulder_width * 0.5)
    
    debug_data['wrist_dist'] = wrist_distance
    debug_data['max_dist'] = shoulder_width * 0.5
    debug_data['CHECK_2_close'] = check2
    
    if not check2:
        return False, debug_data
    
    # Check 3: Wrists at torso height
    lw_at_torso = shoulder_cy < left_wrist.y < hip_y
    rw_at_torso = shoulder_cy < right_wrist.y < hip_y
    check3 = lw_at_torso and rw_at_torso
    
    debug_data['LW_y'] = left_wrist.y
    debug_data['RW_y'] = right_wrist.y
    debug_data['shoulder_y'] = shoulder_cy
    debug_data['hip_y'] = hip_y
    debug_data['CHECK_3_height'] = check3
    
    if not check3:
        return False, debug_data
    
    # Check 4: Wrists in front
    lw_dist_to_center = math.hypot(left_wrist.x - shoulder_cx, left_wrist.y - shoulder_cy)
    rw_dist_to_center = math.hypot(right_wrist.x - shoulder_cx, right_wrist.y - shoulder_cy)
    max_distance = shoulder_width * 2.0
    check4 = (lw_dist_to_center < max_distance and rw_dist_to_center < max_distance)
    
    debug_data['LW_center_dist'] = lw_dist_to_center
    debug_data['RW_center_dist'] = rw_dist_to_center
    debug_data['max_center_dist'] = max_distance
    debug_data['CHECK_4_front'] = check4
    
    return check4, debug_data


def main():
    print("=" * 70)
    print("DETAILED ARMS CROSSED DEBUG")
    print("=" * 70)
    print("\nThis will show:")
    print("  • Exact wrist and shoulder positions")
    print("  • All detection conditions (A, B, C)")
    print("  • Final score and decision")
    print("\nPress 'q' to quit")
    print("=" * 70)
    
    input("\nPress Enter to start...")
    
    # Initialize components
    processor = HolisticProcessor(min_detection_confidence=0.5)
    smoother = SignalSmoother()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return
    
    print("\n🎥 Webcam opened! Starting debug...")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process frame
            results = processor.process_frame(frame)
            
            if results and results.pose_landmarks:
                # Smooth landmarks
                smoothed_pose, _, _, _ = smoother.smooth_landmarks(
                    results.pose_landmarks,
                    results.face_landmarks,
                    results.left_hand_landmarks,
                    results.right_hand_landmarks,
                    time.time()
                )
                
                pose = smoothed_pose
                
                # Get key landmarks
                LEFT_SHOULDER = 11
                RIGHT_SHOULDER = 12
                LEFT_WRIST = 15
                RIGHT_WRIST = 16
                LEFT_HIP = 23
                RIGHT_HIP = 24
                
                # Run debug detection
                arms_crossed, debug_data = detect_arms_with_debug(
                    pose[LEFT_WRIST],
                    pose[RIGHT_WRIST],
                    pose[LEFT_SHOULDER],
                    pose[RIGHT_SHOULDER],
                    pose[LEFT_HIP],
                    pose[RIGHT_HIP]
                )
                
                # Draw debug visualization
                draw_debug_info(frame, pose, arms_crossed, debug_data)
            
            # Show frame
            cv2.imshow('Arms Detection Debug', frame)
            
            # Handle key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n✅ Debug session completed")


if __name__ == "__main__":
    main()
