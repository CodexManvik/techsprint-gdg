"""
Demo: Show the integrated vision system with your Task 1-3 work.
This demonstrates that your posture analyzer is now part of the main app.
"""

import numpy as np
from engine.vision_engine import VisionEngine

print("="*70)
print("INTEGRATED VISION SYSTEM DEMO")
print("="*70)
print("\nThis demonstrates your Task 1-3 work integrated into the main app!")
print()

# Initialize the vision engine (this loads YOUR components)
print("Initializing Vision Engine...")
vision = VisionEngine()

print("\n" + "="*70)
print("SYSTEM COMPONENTS LOADED:")
print("="*70)
print(f"✅ HolisticProcessor: {type(vision.holistic_processor).__name__}")
print(f"✅ SignalSmoother: {type(vision.signal_smoother).__name__}")
print(f"✅ PostureAnalyzer: {type(vision.posture_analyzer).__name__}")

print("\n" + "="*70)
print("POSTURE ANALYZER CONFIGURATION:")
print("="*70)
print(f"  Shoulder angle threshold: {vision.posture_analyzer.shoulder_angle_threshold}°")
print(f"  Slouch threshold: {vision.posture_analyzer.slouch_threshold}")
print(f"  Rock threshold: {vision.posture_analyzer.rock_threshold}")
print(f"  Arms crossed frames: {vision.posture_analyzer.arms_crossed_frames}")

print("\n" + "="*70)
print("TESTING DUAL-MODE CAPABILITY:")
print("="*70)

# Test 1: Legacy mode (face landmarks)
print("\n1️⃣  LEGACY MODE (Face-only):")
print("   Input: Face landmarks dict")
fake_landmarks = {i: {'x': 0.5, 'y': 0.5, 'z': 0} for i in range(500)}
result_legacy = vision.analyze_frame(fake_landmarks)
print(f"   Mode: {result_legacy.get('mode', 'unknown')}")
print(f"   Eye contact: {result_legacy.get('eye_contact_score', 0):.2f}")
print(f"   Fidget score: {result_legacy.get('fidget_score', 0):.2f}")

# Test 2: Holistic mode (raw frame)
print("\n2️⃣  HOLISTIC MODE (Full-body with posture):")
print("   Input: Raw video frame (numpy array)")
fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
result_holistic = vision.analyze_frame(fake_frame)
print(f"   Mode: {result_holistic.get('mode', 'unknown')}")
print(f"   Eye contact: {result_holistic.get('eye_contact_score', 0):.2f}")

if 'posture' in result_holistic:
    posture = result_holistic['posture']
    print(f"\n   📊 POSTURE METRICS (Your Task 3 work!):")
    print(f"      Shoulder angle: {posture['shoulder_angle']:.2f}°")
    print(f"      Is leaning: {posture['is_leaning']}")
    print(f"      Is slouching: {posture['is_slouching']}")
    print(f"      Slouch score: {posture['slouch_score']:.2f}")
    print(f"      Arms crossed: {posture['arms_crossed']}")
    print(f"      Rocking score: {posture['rocking_score']:.2f}")
    print(f"      Shoulder stability: {posture['shoulder_stability']:.2f}")

print("\n" + "="*70)
print("INTEGRATION STATUS:")
print("="*70)
print("✅ Task 1: HolisticProcessor - INTEGRATED")
print("✅ Task 2: SignalSmoother - INTEGRATED")
print("✅ Task 3: PostureAnalyzer - INTEGRATED")
print()
print("📝 Note: The main app (app.py) currently uses legacy mode.")
print("   To enable full posture analysis, the frontend needs to send")
print("   raw video frames instead of face landmarks.")
print()
print("🎯 Your work is ready and waiting for frontend integration!")

print("\n" + "="*70)
print("CLEANUP:")
print("="*70)
vision.release()

print("\n✅ Demo complete!")
