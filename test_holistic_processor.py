"""
Test script for HolisticProcessor
Tests MediaPipe Holistic integration with webcam or test image
"""

import cv2
import numpy as np
from engine.holistic_processor import HolisticProcessor
import time


def test_with_webcam():
    """Test HolisticProcessor with live webcam feed."""
    print("🎥 Testing HolisticProcessor with webcam...")
    print("Press 'q' to quit\n")
    
    # Initialize processor
    processor = HolisticProcessor(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        enable_frame_skip=True,
        target_fps=15.0
    )
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Could not read frame")
                break
            
            # Process frame
            results = processor.process_frame(frame)
            frame_count += 1
            
            # Display results
            print(f"\n--- Frame {results.frame_number} ---")
            print(f"Timestamp: {results.timestamp:.3f}s")
            print(f"Pose landmarks: {'✅ Detected' if results.pose_landmarks else '❌ Not detected'} "
                  f"({len(results.pose_landmarks) if results.pose_landmarks else 0} points)")
            print(f"Face landmarks: {'✅ Detected' if results.face_landmarks else '❌ Not detected'} "
                  f"({len(results.face_landmarks) if results.face_landmarks else 0} points)")
            print(f"Left hand: {'✅ Detected' if results.left_hand_landmarks else '❌ Not detected'} "
                  f"({len(results.left_hand_landmarks) if results.left_hand_landmarks else 0} points)")
            print(f"Right hand: {'✅ Detected' if results.right_hand_landmarks else '❌ Not detected'} "
                  f"({len(results.right_hand_landmarks) if results.right_hand_landmarks else 0} points)")
            
            # Show performance stats every 30 frames
            if frame_count % 30 == 0:
                stats = processor.get_performance_stats()
                print(f"\n📊 Performance Stats:")
                print(f"   FPS: {stats['fps']}")
                print(f"   Avg Process Time: {stats['avg_process_time_ms']}ms")
                print(f"   Frames Processed: {stats['frames_processed']}")
                print(f"   Frame Skip: {'Enabled' if stats['frame_skip_enabled'] else 'Disabled'}")
            
            # Draw on frame for visualization
            display_frame = frame.copy()
            
            # Draw pose landmarks if detected
            if results.pose_landmarks:
                # Draw shoulders (landmarks 11 and 12)
                h, w = frame.shape[:2]
                left_shoulder = results.pose_landmarks[11]
                right_shoulder = results.pose_landmarks[12]
                
                ls_x, ls_y = int(left_shoulder.x * w), int(left_shoulder.y * h)
                rs_x, rs_y = int(right_shoulder.x * w), int(right_shoulder.y * h)
                
                cv2.circle(display_frame, (ls_x, ls_y), 10, (0, 255, 0), -1)
                cv2.circle(display_frame, (rs_x, rs_y), 10, (0, 255, 0), -1)
                cv2.line(display_frame, (ls_x, ls_y), (rs_x, rs_y), (0, 255, 0), 2)
                
                # Draw nose (landmark 0)
                nose = results.pose_landmarks[0]
                nose_x, nose_y = int(nose.x * w), int(nose.y * h)
                cv2.circle(display_frame, (nose_x, nose_y), 8, (255, 0, 0), -1)
            
            # Add status text
            status_text = f"FPS: {processor.get_performance_stats()['fps']:.1f}"
            cv2.putText(display_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow('HolisticProcessor Test', display_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    
    finally:
        # Cleanup
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 Final Stats:")
        print(f"   Total frames: {frame_count}")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Average FPS: {avg_fps:.2f}")
        
        cap.release()
        cv2.destroyAllWindows()
        processor.release()
        print("\n✅ Test completed successfully!")


def test_with_static_image():
    """Test HolisticProcessor with a static test image."""
    print("🖼️ Testing HolisticProcessor with static image...")
    
    # Create a simple test image (black frame)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Initialize processor
    processor = HolisticProcessor()
    
    # Process frame
    results = processor.process_frame(test_frame)
    
    print(f"\n--- Results ---")
    print(f"Frame number: {results.frame_number}")
    print(f"Pose landmarks: {len(results.pose_landmarks) if results.pose_landmarks else 0}")
    print(f"Face landmarks: {len(results.face_landmarks) if results.face_landmarks else 0}")
    print(f"Left hand: {len(results.left_hand_landmarks) if results.left_hand_landmarks else 0}")
    print(f"Right hand: {len(results.right_hand_landmarks) if results.right_hand_landmarks else 0}")
    
    # Test landmark structure
    if results.pose_landmarks:
        print(f"\n✅ Sample pose landmark (nose):")
        nose = results.pose_landmarks[0]
        print(f"   x: {nose.x:.4f}")
        print(f"   y: {nose.y:.4f}")
        print(f"   z: {nose.z:.4f}")
        print(f"   visibility: {nose.visibility:.4f}")
    
    processor.release()
    print("\n✅ Static image test completed!")


def test_performance():
    """Test processing performance with multiple frames."""
    print("⚡ Testing HolisticProcessor performance...")
    
    processor = HolisticProcessor(enable_frame_skip=False)
    
    # Create test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Process 100 frames
    num_frames = 100
    start_time = time.time()
    
    for i in range(num_frames):
        results = processor.process_frame(test_frame)
        if (i + 1) % 20 == 0:
            print(f"Processed {i + 1}/{num_frames} frames...")
    
    elapsed = time.time() - start_time
    fps = num_frames / elapsed
    
    stats = processor.get_performance_stats()
    
    print(f"\n📊 Performance Results:")
    print(f"   Frames processed: {num_frames}")
    print(f"   Total time: {elapsed:.2f}s")
    print(f"   Average FPS: {fps:.2f}")
    print(f"   Avg process time: {stats['avg_process_time_ms']:.2f}ms")
    
    processor.release()
    print("\n✅ Performance test completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("HolisticProcessor Test Suite")
    print("=" * 60)
    
    # Run tests
    print("\n1️⃣ Running static image test...")
    test_with_static_image()
    
    print("\n" + "=" * 60)
    print("\n2️⃣ Running performance test...")
    test_performance()
    
    print("\n" + "=" * 60)
    print("\n3️⃣ Running webcam test...")
    print("   (This will open your webcam - press 'q' to quit)")
    
    response = input("\nStart webcam test? (y/n): ")
    if response.lower() == 'y':
        test_with_webcam()
    else:
        print("⏭️ Skipping webcam test")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
