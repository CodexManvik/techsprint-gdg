import mediapipe as mp
print(f"Mediapipe version: {mp.__version__}")
try:
    print(f"Solutions: {mp.solutions}")
    print(f"Holistic: {mp.solutions.holistic}")
    print("✅ Mediapipe seems OK")
except AttributeError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
