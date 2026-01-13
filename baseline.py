import cv2
import mediapipe as mp
from google import genai
import os
from dotenv import load_dotenv

# 1. Setup New Gemini Client
load_dotenv()
# If this fails, double check your .env file has GOOGLE_API_KEY=your_key
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. Setup MediaPipe (Keep your current 0.10.14 version)
mp_face_mesh = mp.solutions.face_mesh
# refine_landmarks=True is essential for tracking iris (eye contact)
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) 
mp_drawing = mp.solutions.drawing_utils

def start_baseline():
    print("AI Recruiter: Testing API Connection...")
    try:
        # Changed model to 'gemini-1.5-flash' explicitly or try 'gemini-2.0-flash'
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents="You are a lead recruiter from Dell at MUJ. Give a 1-sentence welcome."
        )
        print(f"AI Recruiter: {response.text}")
    except Exception as e:
        print(f"Error connecting to Gemini: {e}")
        return

    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        success, image = cap.read()
        if not success: break

        # Process frame
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_image)

        # Draw Landmarks
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # This draws the green dots on the eyes (irises)
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0))
                )

        cv2.imshow('The Interview Mirror - Baseline', image)
        # Press ESC to exit
        if cv2.waitKey(5) & 0xFF == 27: break 

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_baseline()