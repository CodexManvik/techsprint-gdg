"""
Test script for GestureAnalyzer - hand gesture and face-touching detection.
"""

import sys
import time
from engine.analyzers.gesture_analyzer import GestureAnalyzer, Landmark, GestureMetrics


def create_test_landmarks(scenario: str):
    """Create synthetic hand and face landmarks for different scenarios."""
    
    # Create 21 hand landmarks (MediaPipe Hands format)
    left_hand = [Landmark(0.3, 0.7, 0, 1.0) for _ in range(21)]  # Default left hand
    right_hand = [Landmark(0.7, 0.7, 0, 1.0) for _ in range(21)]  # Default right hand
    nose = Landmark(0.5, 0.3, 0, 1.0)  # Nose landmark
    shoulder_y = 0.5  # Shoulder Y-coordinate
    
    if scenario == "hands_down":
        # Hands at sides, no gestures
        left_hand[0] = Landmark(0.3, 0.8, 0, 1.0)   # Left wrist low
        left_hand[8] = Landmark(0.3, 0.85, 0, 1.0)  # Left index tip
        right_hand[0] = Landmark(0.7, 0.8, 0, 1.0)  # Right wrist low
        right_hand[8] = Landmark(0.7, 0.85, 0, 1.0) # Right index tip
        
    elif scenario == "face_touch_left":
        # Left hand touching face
        left_hand[0] = Landmark(0.4, 0.4, 0, 1.0)   # Left wrist near face
        left_hand[8] = Landmark(0.48, 0.32, 0, 1.0) # Left index tip near nose
        right_hand[0] = Landmark(0.7, 0.8, 0, 1.0)  # Right wrist low
        right_hand[8] = Landmark(0.7, 0.85, 0, 1.0) # Right index tip low
        
    elif scenario == "face_touch_right":
        # Right hand touching face
        left_hand[0] = Landmark(0.3, 0.8, 0, 1.0)   # Left wrist low
        left_hand[8] = Landmark(0.3, 0.85, 0, 1.0)  # Left index tip low
        right_hand[0] = Landmark(0.6, 0.4, 0, 1.0)  # Right wrist near face
        right_hand[8] = Landmark(0.52, 0.32, 0, 1.0) # Right index tip near nose
        
    elif scenario == "gesturing_left":
        # Left hand elevated and moving (gesturing)
        left_hand[0] = Landmark(0.2, 0.3, 0, 1.0)   # Left wrist above shoulders
        left_hand[8] = Landmark(0.15, 0.25, 0, 1.0) # Left index tip elevated
        right_hand[0] = Landmark(0.7, 0.8, 0, 1.0)  # Right wrist low
        right_hand[8] = Landmark(0.7, 0.85, 0, 1.0) # Right index tip low
        
    elif scenario == "gesturing_both":
        # Both hands elevated (dynamic speaker)
        left_hand[0] = Landmark(0.2, 0.3, 0, 1.0)   # Left wrist above shoulders
        left_hand[8] = Landmark(0.15, 0.25, 0, 1.0) # Left index tip elevated
        right_hand[0] = Landmark(0.8, 0.3, 0, 1.0)  # Right wrist above shoulders
        right_hand[8] = Landmark(0.85, 0.25, 0, 1.0) # Right index tip elevated
        
    elif scenario == "no_hands":
        # No hands visible
        left_hand = None
        right_hand = None
    
    return left_hand, right_hand, nose, shoulder_y


def test_scenario(analyzer: GestureAnalyzer, scenario: str, expected_results: dict):
    """Test a specific gesture scenario."""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario.upper().replace('_', ' ')}")
    print(f"{'='*60}")
    
    left_hand, right_hand, nose, shoulder_y = create_test_landmarks(scenario)
    
    # Run analysis multiple times to simulate movement and build history
    results = None
    for i in range(10):  # Build up movement history
        # Simulate slight movement for gesture detection
        if scenario.startswith("gesturing") and left_hand:
            # Add slight movement to simulate gesturing
            movement = 0.01 * i  # Gradual movement
            left_hand[0].x += movement
            left_hand[8].x += movement
            
        if scenario == "gesturing_both" and right_hand:
            movement = 0.01 * i
            right_hand[0].x -= movement  # Move in opposite direction
            right_hand[8].x -= movement
        
        results = analyzer.analyze(
            left_hand_landmarks=left_hand,
            right_hand_landmarks=right_hand,
            nose_landmark=nose,
            shoulder_y=shoulder_y,
            timestamp=time.time()
        )
        
        time.sleep(0.1)  # Small delay to simulate real-time
    
    # Print results
    print(f"\n📊 Results:")
    print(f"  Left hand visible: {results.left_hand_visible}")
    print(f"  Right hand visible: {results.right_hand_visible}")
    print(f"  Face touch detected: {results.face_touch_detected}")
    print(f"  Face touch count: {results.face_touch_count}")
    print(f"  Active gestures: {results.active_gesture_count}")
    print(f"  Gesture frequency: {results.gesture_frequency:.2f}/min")
    print(f"  Activity level: {results.hand_activity_level}")
    print(f"  Left hand above shoulders: {results.left_hand_above_shoulders}")
    print(f"  Right hand above shoulders: {results.right_hand_above_shoulders}")
    
    # Check expectations
    passed = True
    for key, expected_value in expected_results.items():
        actual_value = getattr(results, key)
        if actual_value != expected_value:
            print(f"\n❌ FAIL - {key}: expected {expected_value}, got {actual_value}")
            passed = False
    
    if passed:
        print(f"\n✅ PASS - All expectations met!")
    
    return passed


def main():
    """Run all gesture analyzer tests."""
    print("="*60)
    print("GESTURE ANALYZER TEST SUITE")
    print("="*60)
    
    analyzer = GestureAnalyzer(
        face_touch_threshold=0.1,
        gesture_height_threshold=0.1,
        gesture_velocity_threshold=0.02
    )
    
    # Test scenarios with expected results
    test_cases = [
        ("hands_down", {
            "left_hand_visible": True,
            "right_hand_visible": True,
            "face_touch_detected": False,
            "left_hand_above_shoulders": False,
            "right_hand_above_shoulders": False,
            "hand_activity_level": "passive"
        }),
        
        ("face_touch_left", {
            "left_hand_visible": True,
            "right_hand_visible": True,
            "face_touch_detected": True,
            "left_hand_above_shoulders": False,
            "right_hand_above_shoulders": False
        }),
        
        ("face_touch_right", {
            "left_hand_visible": True,
            "right_hand_visible": True,
            "face_touch_detected": True,
            "left_hand_above_shoulders": False,
            "right_hand_above_shoulders": False
        }),
        
        ("gesturing_left", {
            "left_hand_visible": True,
            "right_hand_visible": True,
            "face_touch_detected": False,
            "left_hand_above_shoulders": True,
            "right_hand_above_shoulders": False
        }),
        
        ("gesturing_both", {
            "left_hand_visible": True,
            "right_hand_visible": True,
            "face_touch_detected": False,
            "left_hand_above_shoulders": True,
            "right_hand_above_shoulders": True
        }),
        
        ("no_hands", {
            "left_hand_visible": False,
            "right_hand_visible": False,
            "face_touch_detected": False,
            "left_hand_above_shoulders": False,
            "right_hand_above_shoulders": False
        })
    ]
    
    results = []
    for scenario, expected in test_cases:
        analyzer.reset()  # Reset state between tests
        passed = test_scenario(analyzer, scenario, expected)
        results.append((scenario, passed))
    
    # Test session summary
    print(f"\n{'='*60}")
    print("SESSION SUMMARY TEST")
    print(f"{'='*60}")
    
    summary = analyzer.get_session_summary()
    print(f"\n📈 Session Summary:")
    print(f"  Total face touches: {summary.total_face_touches}")
    print(f"  Total gestures: {summary.total_gestures}")
    print(f"  Average gestures/min: {summary.average_gestures_per_minute:.2f}")
    print(f"  Session duration: {summary.session_duration_minutes:.2f} min")
    print(f"  Classification: {summary.classification}")
    print(f"  Face touch frequency: {summary.face_touch_frequency:.2f}/min")
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for scenario, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {scenario.replace('_', ' ').title()}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed_count}/{total_count} tests passed")
    print(f"{'='*60}")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())