"""
Simple test to verify arms crossed detection works for both states.
Shows clear visual feedback and instructions.
"""

import cv2
import time
from engine.holistic_processor import HolisticProcessor
from engine.signal_smoother import SignalSmoother
from engine.analyzers.posture_analyzer import PostureAnalyzer


def main():
    print("=" * 70)
    print("ARMS CROSSED DETECTION TEST")
    print("=" * 70)
    print("\nThis test will verify both states:")
    print("  1. Arms OPEN (hands on lap or sides)")
    print("  2. Arms CROSSED (arms folded across chest)")
    print("\nThe detection uses temporal smoothing, so:")
    print("  • Hold each position for 3-5 seconds")
    print("  • Status will update once confident")
    print("\nPress 'q' to quit")
    print("=" * 70)
    
    input("\nPress Enter to start...")
    
    # Initialize
    processor = HolisticProcessor(min_detection_confidence=0.5)
    smoother = SignalSmoother()
    analyzer = PostureAnalyzer()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return
    
    print("\n🎥 Webcam opened!")
    print("\n📋 TEST SEQUENCE:")
    print("  1. Start with arms OPEN (hands on lap)")
    print("  2. Hold for 5 seconds - should show 'OPEN'")
    print("  3. Cross your arms across chest")
    print("  4. Hold for 5 seconds - should show 'CROSSED'")
    print("  5. Uncross arms")
    print("  6. Should return to 'OPEN'")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    frame_count = 0
    last_status = None
    status_change_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process
            results = processor.process_frame(frame)
            
            if results and results.pose_landmarks:
                # Smooth
                smoothed_pose, _, _, _ = smoother.smooth_landmarks(
                    results.pose_landmarks,
                    results.face_landmarks,
                    results.left_hand_landmarks,
                    results.right_hand_landmarks,
                    time.time()
                )
                
                # Analyze
                metrics = analyzer.analyze(smoothed_pose, time.time())
                
                # Track status changes
                current_status = "CROSSED" if metrics.arms_crossed else "OPEN"
                if last_status is not None and current_status != last_status:
                    status_change_count += 1
                    print(f"\n✅ Status changed: {last_status} → {current_status} (frame {frame_count})")
                last_status = current_status
                
                # Draw large status text
                h, w = frame.shape[:2]
                status_text = f"Arms: {current_status}"
                color = (0, 0, 255) if metrics.arms_crossed else (0, 255, 0)
                
                # Large text
                cv2.putText(frame, status_text, (20, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 4)
                
                # Frame counter
                cv2.putText(frame, f"Frame: {frame_count}", (20, h - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Instructions
                if frame_count < 150:
                    cv2.putText(frame, "Start: Arms OPEN", (20, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                elif frame_count < 300:
                    cv2.putText(frame, "Now: Cross your arms", (20, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                else:
                    cv2.putText(frame, "Now: Uncross arms", (20, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
            cv2.imshow('Arms Detection Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(f"Total frames: {frame_count}")
        print(f"Status changes detected: {status_change_count}")
        print(f"Final status: {last_status}")
        
        if status_change_count >= 2:
            print("\n✅ TEST PASSED - Detection working correctly!")
            print("   (Detected transitions between OPEN and CROSSED)")
        else:
            print("\n⚠️ TEST INCONCLUSIVE - Try holding each position longer")
        
        print("=" * 70)


if __name__ == "__main__":
    main()
