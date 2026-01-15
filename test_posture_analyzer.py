"""
Test script for PostureAnalyzer - specifically arms-crossed detection.
"""

import sys
import math
from engine.analyzers.posture_analyzer import PostureAnalyzer, Landmark, PostureMetrics


def create_test_landmarks(scenario: str):
    """Create synthetic pose landmarks for different scenarios."""
    
    # Base landmarks (33 points for MediaPipe Pose)
    landmarks = [Landmark(0.5, 0.5, 0, 1.0) for _ in range(33)]
    
    if scenario == "arms_open":
        # Normal sitting position - arms at sides
        landmarks[0] = Landmark(0.5, 0.3, 0, 1.0)   # Nose
        landmarks[11] = Landmark(0.35, 0.5, 0, 1.0)  # Left shoulder
        landmarks[12] = Landmark(0.65, 0.5, 0, 1.0)  # Right shoulder
        landmarks[13] = Landmark(0.30, 0.65, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.70, 0.65, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.25, 0.75, 0, 1.0) # Left wrist (left side)
        landmarks[16] = Landmark(0.75, 0.75, 0, 1.0) # Right wrist (right side)
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
        
    elif scenario == "arms_crossed":
        # Arms crossed in front of chest
        landmarks[0] = Landmark(0.5, 0.3, 0, 1.0)   # Nose
        landmarks[11] = Landmark(0.35, 0.5, 0, 1.0)  # Left shoulder
        landmarks[12] = Landmark(0.65, 0.5, 0, 1.0)  # Right shoulder
        landmarks[13] = Landmark(0.40, 0.60, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.60, 0.60, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.60, 0.58, 0, 1.0) # Left wrist (near RIGHT shoulder)
        landmarks[16] = Landmark(0.40, 0.58, 0, 1.0) # Right wrist (near LEFT shoulder)
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
        
    elif scenario == "hands_in_lap":
        # Hands resting in lap - should NOT trigger crossed
        landmarks[0] = Landmark(0.5, 0.3, 0, 1.0)   # Nose
        landmarks[11] = Landmark(0.35, 0.5, 0, 1.0)  # Left shoulder
        landmarks[12] = Landmark(0.65, 0.5, 0, 1.0)  # Right shoulder
        landmarks[13] = Landmark(0.30, 0.65, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.70, 0.65, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.45, 0.90, 0, 1.0) # Left wrist (in lap, below hips)
        landmarks[16] = Landmark(0.55, 0.90, 0, 1.0) # Right wrist (in lap, below hips)
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
        
    elif scenario == "gesturing":
        # One hand up gesturing - should NOT trigger crossed
        landmarks[0] = Landmark(0.5, 0.3, 0, 1.0)   # Nose
        landmarks[11] = Landmark(0.35, 0.5, 0, 1.0)  # Left shoulder
        landmarks[12] = Landmark(0.65, 0.5, 0, 1.0)  # Right shoulder
        landmarks[13] = Landmark(0.25, 0.45, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.70, 0.65, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.20, 0.35, 0, 1.0) # Left wrist (up, gesturing)
        landmarks[16] = Landmark(0.75, 0.75, 0, 1.0) # Right wrist (at side)
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
        
    elif scenario == "leaning_left":
        # Leaning left - shoulders tilted
        landmarks[0] = Landmark(0.5, 0.3, 0, 1.0)   # Nose
        landmarks[11] = Landmark(0.35, 0.45, 0, 1.0) # Left shoulder (higher)
        landmarks[12] = Landmark(0.65, 0.55, 0, 1.0) # Right shoulder (lower)
        landmarks[13] = Landmark(0.30, 0.65, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.70, 0.65, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.25, 0.75, 0, 1.0) # Left wrist
        landmarks[16] = Landmark(0.75, 0.75, 0, 1.0) # Right wrist
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
        
    elif scenario == "slouching":
        # Slouching - nose closer to shoulders
        landmarks[0] = Landmark(0.5, 0.45, 0, 1.0)   # Nose (lower than normal)
        landmarks[11] = Landmark(0.35, 0.5, 0, 1.0)  # Left shoulder
        landmarks[12] = Landmark(0.65, 0.5, 0, 1.0)  # Right shoulder
        landmarks[13] = Landmark(0.30, 0.65, 0, 1.0) # Left elbow
        landmarks[14] = Landmark(0.70, 0.65, 0, 1.0) # Right elbow
        landmarks[15] = Landmark(0.25, 0.75, 0, 1.0) # Left wrist
        landmarks[16] = Landmark(0.75, 0.75, 0, 1.0) # Right wrist
        landmarks[23] = Landmark(0.40, 0.85, 0, 1.0) # Left hip
        landmarks[24] = Landmark(0.60, 0.85, 0, 1.0) # Right hip
    
    return landmarks


def test_scenario(analyzer: PostureAnalyzer, scenario: str, expected_crossed: bool):
    """Test a specific scenario."""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario.upper().replace('_', ' ')}")
    print(f"Expected arms_crossed: {expected_crossed}")
    print(f"{'='*60}")
    
    landmarks = create_test_landmarks(scenario)
    
    # Run analysis multiple times to fill temporal buffer
    results = None
    for i in range(15):  # More than arms_crossed_frames (10)
        results = analyzer.analyze(landmarks, timestamp=float(i))
    
    # Print results
    print(f"\n📊 Results:")
    print(f"  Shoulder angle: {results.shoulder_angle:.2f}°")
    print(f"  Is leaning: {results.is_leaning}")
    print(f"  Is slouching: {results.is_slouching}")
    print(f"  Slouch score: {results.slouch_score:.2f}")
    print(f"  Arms crossed: {results.arms_crossed}")
    print(f"  Rocking score: {results.rocking_score:.2f}")
    print(f"  Shoulder stability: {results.shoulder_stability:.2f}")
    
    # Check if result matches expectation
    if results.arms_crossed == expected_crossed:
        print(f"\n✅ PASS - Arms crossed detection correct!")
    else:
        print(f"\n❌ FAIL - Expected arms_crossed={expected_crossed}, got {results.arms_crossed}")
    
    return results.arms_crossed == expected_crossed


def main():
    """Run all posture analyzer tests."""
    print("="*60)
    print("POSTURE ANALYZER TEST SUITE")
    print("="*60)
    
    analyzer = PostureAnalyzer(
        shoulder_angle_threshold=15.0,
        slouch_threshold=0.05,
        rock_threshold=0.02,
        arms_crossed_frames=10
    )
    
    # Test scenarios
    test_cases = [
        ("arms_open", False),
        ("arms_crossed", True),
        ("hands_in_lap", False),
        ("gesturing", False),
        ("leaning_left", False),
        ("slouching", False),
    ]
    
    results = []
    for scenario, expected in test_cases:
        analyzer.reset()  # Reset state between tests
        passed = test_scenario(analyzer, scenario, expected)
        results.append((scenario, passed))
    
    # Summary
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
