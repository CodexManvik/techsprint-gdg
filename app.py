from dotenv import load_dotenv
import os
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from engine.vision_engine import VisionEngine
from engine.ai_engine import AIEngine
from engine.audio_engine import AudioEngine
from pypdf import PdfReader
import io

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for hackathon/testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],
)

# Global AI Engine (Loaded once)
ai = AIEngine()
audio_processor = AudioEngine()

@app.get("/")
async def root():
    return {"status": "Online", "version": "2.0-Live"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        # Extract text using pypdf
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # Send text to AI Engine
        # This "primes" the AI with the resume before the interview starts
        intro_question = ai.load_resume(text)
        
        return {"status": "success", "intro": intro_question}
    except Exception as e:
        print(f"Resume Error: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/interview")
async def interview_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # CRITICAL FIX: Create a NEW VisionEngine for EACH user.
    # If we kept this global, User A's movements would mess up User B's fidget score.
    vision = VisionEngine()
    
    print("--- New Client Connected ---")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # MODE 1: LIVE TRACKING (Fast, no AI response)
            if payload.get("type") == "tracking":
                # Analyze landmarks
                metrics = vision.analyze_frame(payload['landmarks'])
                
                # Send back ONLY metrics (very fast)
                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    "metrics": metrics
                }))

            # MODE 2: INTERACTION (Audio sent, needs AI response)
            elif payload.get("type") == "conversation":
                print("Processing Audio...")
                
                # 1. Decode Audio
                audio_bytes = base64.b64decode(payload['audio_data'])
                audio_result = audio_processor.process_audio(audio_bytes)
                
                user_text = audio_result['text']
                
                # 2. Get Vision Metrics (Snapshot of the moment)
                metrics = vision.analyze_frame(payload['landmarks'])
                metrics["volume"] = audio_result['volume']
                metrics["wpm"] = audio_result['wpm']
                
                # 3. Get AI Reply
                ai_reply = "I couldn't hear you clearly."
                if user_text:
                    print(f"User said: {user_text}")
                    ai_reply = ai.get_response(user_text, metrics)
                
                # 4. Send Full Response
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "reply": ai_reply,
                    "transcript": user_text,
                    "metrics": metrics
                }))

    except WebSocketDisconnect:
        print("Client Disconnected")
    except Exception as e:
        print(f"Error: {e}")