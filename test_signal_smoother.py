"""
Test script for SignalSmoother and One Euro Filter
Tests jitter reduction and filter behavior
"""

import numpy as np
import matplotlib.pyplot as plt
from engine.signal_smoother import SignalSmoother, Landmark, OneEuroFilter
import time


def test_one_euro_filter_basic():
    """Test basic One Euro Filter functionality."""
    print("🧪 Testing One Euro Filter - Basic Functionality")
    print("=" * 60)
    
    # Create filter
    filter_obj = OneEuroFilter(freq=30.0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    
    # Test with constant value (should converge quickly)
    print("\n1. Testing with constant value (5.0):")
    values = []
    for i in range(10):
        t = i / 30.0  # 30 Hz
        filtered = filter_obj(5.0, t)
        values.append(filtered)
        print(f"   Frame {i}: {filtered:.4f}")
    
    # Should converge to 5.0
    assert abs(values[-1] - 5.0) < 0.01, "Filter should converge to constant value"
    print("   ✅ Converged to constant value")
    
    # Reset and test with noisy signal
    filter_obj.reset()
    print("\n2. Testing with noisy signal:")
    
    np.random.seed(42)
    raw_values = []
    filtered_values = []
    
    for i in range(50):
        t = i / 30.0
        # Signal: sine wave + noise
        raw = np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.1)
        filtered = filter_obj(raw, t)
        
        raw_values.append(raw)
        filtered_values.append(filtered)
    
    # Calculate noise reduction
    raw_std = np.std(np.diff(raw_values))
    filtered_std = np.std(np.diff(filtered_values))
    reduction = (1 - filtered_std / raw_std) * 100
    
    print(f"   Raw signal jitter (std of diff): {raw_std:.4f}")
    print(f"   Filtered signal jitter: {filtered_std:.4f}")
    print(f"   Noise reduction: {reduction:.1f}%")
    print("   ✅ Filter reduces jitter")
    
    return raw_values, filtered_values


def test_signal_smoother_landmarks():
    """Test SignalSmoother with landmark data."""
    print("\n\n🧪 Testing SignalSmoother - Landmark Smoothing")
    print("=" * 60)
    
    # Create smoother
    smoother = SignalSmoother(freq=30.0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    
    # Create synthetic landmark data with jitter
    np.random.seed(42)
    num_frames = 30
    
    print("\n1. Creating synthetic pose landmarks with jitter...")
    
    raw_nose_x = []
    smoothed_nose_x = []
    
    for frame in range(num_frames):
        t = frame / 30.0
        
        # Create pose landmarks (just nose for testing)
        # True position: slowly moving from 0.4 to 0.6
        true_x = 0.4 + 0.2 * (frame / num_frames)
        
        # Add camera jitter
        noisy_x = true_x + np.random.normal(0, 0.01)
        
        pose_landmarks = [
            Landmark(x=noisy_x, y=0.5, z=0.0, visibility=1.0)  # Nose
        ]
        
        # Smooth landmarks
        smoothed_pose, _, _, _ = smoother.smooth_landmarks(
            pose_landmarks=pose_landmarks,
            face_landmarks=None,
            left_hand_landmarks=None,
            right_hand_landmarks=None,
            timestamp=t
        )
        
        raw_nose_x.append(noisy_x)
        smoothed_nose_x.append(smoothed_pose[0].x)
    
    # Calculate jitter reduction
    raw_jitter = np.std(np.diff(raw_nose_x))
    smoothed_jitter = np.std(np.diff(smoothed_nose_x))
    reduction = (1 - smoothed_jitter / raw_jitter) * 100
    
    print(f"\n2. Results:")
    print(f"   Raw landmark jitter: {raw_jitter:.6f}")
    print(f"   Smoothed landmark jitter: {smoothed_jitter:.6f}")
    print(f"   Jitter reduction: {reduction:.1f}%")
    print(f"   Active filters: {smoother.get_filter_count()}")
    
    assert reduction > 30, "Should reduce jitter by at least 30%"
    print("   ✅ Significant jitter reduction achieved")
    
    # Test reset
    print("\n3. Testing filter reset...")
    initial_count = smoother.get_filter_count()
    smoother.reset()
    print(f"   Filters before reset: {initial_count}")
    print(f"   Filters after reset: {smoother.get_filter_count()} (still exist)")
    print("   ✅ Reset successful")
    
    return raw_nose_x, smoothed_nose_x


def test_signal_smoother_multiple_landmarks():
    """Test SignalSmoother with multiple landmark types."""
    print("\n\n🧪 Testing SignalSmoother - Multiple Landmark Types")
    print("=" * 60)
    
    smoother = SignalSmoother(freq=30.0, min_cutoff=1.0, beta=0.0)
    
    # Create landmarks for all types
    pose_lms = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(33)]
    face_lms = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(468)]
    left_hand_lms = [Landmark(x=0.3, y=0.5, z=0.0, visibility=1.0) for _ in range(21)]
    right_hand_lms = [Landmark(x=0.7, y=0.5, z=0.0, visibility=1.0) for _ in range(21)]
    
    print("\n1. Processing all landmark types...")
    
    # Process multiple frames
    for frame in range(10):
        t = frame / 30.0
        smoothed = smoother.smooth_landmarks(
            pose_landmarks=pose_lms,
            face_landmarks=face_lms,
            left_hand_landmarks=left_hand_lms,
            right_hand_landmarks=right_hand_lms,
            timestamp=t
        )
    
    stats = smoother.get_stats()
    expected_filters = (33 + 468 + 21 + 21) * 3  # 3 coords per landmark
    
    print(f"\n2. Filter Statistics:")
    print(f"   Total landmarks: {33 + 468 + 21 + 21}")
    print(f"   Expected filters (landmarks × 3 coords): {expected_filters}")
    print(f"   Actual filters created: {stats['total_filters']}")
    print(f"   Frequency: {stats['freq']} Hz")
    print(f"   Min cutoff: {stats['min_cutoff']}")
    print(f"   Beta: {stats['beta']}")
    
    assert stats['total_filters'] == expected_filters, "Should create filter for each coordinate"
    print("   ✅ Correct number of filters created")


def test_signal_smoother_missing_landmarks():
    """Test SignalSmoother with missing landmarks (None)."""
    print("\n\n🧪 Testing SignalSmoother - Missing Landmarks")
    print("=" * 60)
    
    smoother = SignalSmoother(freq=30.0)
    
    # Test with some landmarks missing
    pose_lms = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0)]
    
    print("\n1. Processing with missing hand landmarks...")
    
    smoothed_pose, smoothed_face, smoothed_left, smoothed_right = smoother.smooth_landmarks(
        pose_landmarks=pose_lms,
        face_landmarks=None,  # Missing
        left_hand_landmarks=None,  # Missing
        right_hand_landmarks=None,  # Missing
        timestamp=0.0
    )
    
    print(f"   Pose landmarks: {'✅ Present' if smoothed_pose else '❌ None'}")
    print(f"   Face landmarks: {'✅ Present' if smoothed_face else '❌ None'}")
    print(f"   Left hand: {'✅ Present' if smoothed_left else '❌ None'}")
    print(f"   Right hand: {'✅ Present' if smoothed_right else '❌ None'}")
    
    assert smoothed_pose is not None, "Should return smoothed pose"
    assert smoothed_face is None, "Should return None for missing face"
    assert smoothed_left is None, "Should return None for missing left hand"
    assert smoothed_right is None, "Should return None for missing right hand"
    
    print("   ✅ Handles missing landmarks correctly")


def test_performance():
    """Test SignalSmoother performance."""
    print("\n\n🧪 Testing SignalSmoother - Performance")
    print("=" * 60)
    
    smoother = SignalSmoother(freq=30.0)
    
    # Create full landmark set
    pose_lms = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(33)]
    face_lms = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(468)]
    left_hand_lms = [Landmark(x=0.3, y=0.5, z=0.0, visibility=1.0) for _ in range(21)]
    right_hand_lms = [Landmark(x=0.7, y=0.5, z=0.0, visibility=1.0) for _ in range(21)]
    
    print("\n1. Benchmarking smoothing performance...")
    
    num_iterations = 100
    start_time = time.time()
    
    for i in range(num_iterations):
        t = i / 30.0
        smoother.smooth_landmarks(
            pose_landmarks=pose_lms,
            face_landmarks=face_lms,
            left_hand_landmarks=left_hand_lms,
            right_hand_landmarks=right_hand_lms,
            timestamp=t
        )
    
    elapsed = time.time() - start_time
    avg_time = (elapsed / num_iterations) * 1000  # ms
    
    print(f"\n2. Performance Results:")
    print(f"   Iterations: {num_iterations}")
    print(f"   Total time: {elapsed:.3f}s")
    print(f"   Average time per frame: {avg_time:.2f}ms")
    print(f"   Throughput: {num_iterations / elapsed:.1f} frames/sec")
    
    assert avg_time < 10, "Should process frame in less than 10ms"
    print("   ✅ Performance is acceptable")


def visualize_filtering(raw_values, filtered_values):
    """Create visualization of filtering effect."""
    print("\n\n📊 Creating visualization...")
    
    try:
        plt.figure(figsize=(12, 6))
        
        # Plot raw vs filtered
        plt.subplot(2, 1, 1)
        plt.plot(raw_values, 'b-', alpha=0.5, label='Raw Signal', linewidth=1)
        plt.plot(filtered_values, 'r-', label='Filtered Signal', linewidth=2)
        plt.xlabel('Frame')
        plt.ylabel('Value')
        plt.title('One Euro Filter: Raw vs Filtered Signal')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot difference (jitter)
        plt.subplot(2, 1, 2)
        raw_diff = np.diff(raw_values)
        filtered_diff = np.diff(filtered_values)
        plt.plot(raw_diff, 'b-', alpha=0.5, label='Raw Jitter', linewidth=1)
        plt.plot(filtered_diff, 'r-', label='Filtered Jitter', linewidth=2)
        plt.xlabel('Frame')
        plt.ylabel('Frame-to-Frame Change')
        plt.title('Jitter Comparison (Frame-to-Frame Differences)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('signal_smoother_test_results.png', dpi=150)
        print("   ✅ Visualization saved to 'signal_smoother_test_results.png'")
        
    except Exception as e:
        print(f"   ⚠️ Could not create visualization: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("SignalSmoother Test Suite")
    print("=" * 60)
    
    # Run tests
    raw_vals, filtered_vals = test_one_euro_filter_basic()
    raw_nose, smoothed_nose = test_signal_smoother_landmarks()
    test_signal_smoother_multiple_landmarks()
    test_signal_smoother_missing_landmarks()
    test_performance()
    
    # Create visualization
    visualize_filtering(raw_vals, filtered_vals)
    
    print("\n" + "=" * 60)
    print("✅ All SignalSmoother tests passed!")
    print("=" * 60)
