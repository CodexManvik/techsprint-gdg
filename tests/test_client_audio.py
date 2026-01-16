import asyncio
import websockets
import json
import base64
import pyaudio
import wave
import io

# Audio Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5  # Duration of each answer
INPUT_DEVICE_INDEX = 1

async def record_and_send(websocket):
    p = pyaudio.PyAudio()
    
    input("Press Enter to start recording your answer (5 seconds)...")
    print(f"🔴 Recording using Device {INPUT_DEVICE_INDEX}...")
    
    print("🔴 Recording...")
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=INPUT_DEVICE_INDEX,
                    frames_per_buffer=CHUNK)

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("✅ Recording stopped.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Convert raw PCM audio to a generic WAV container in memory
    # (Google Speech Recognition needs the WAV headers to know the format)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    wav_bytes = wav_buffer.getvalue()
    
    # Encode to Base64 string for JSON transmission
    audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')

    # Send payload
    payload = {
        "audio_data": audio_b64,
        # Sending dummy landmarks so the Vision Engine doesn't crash
        "landmarks": [{"x": 0.5, "y": 0.5, "z": 0.0}] * 478 
    }
    
    print("-> Sending audio to AI Recruiter...")
    await websocket.send(json.dumps(payload))

async def start_interview():
    uri = "ws://localhost:8000/ws/interview"
    async with websockets.connect(uri) as websocket:
        print("\n--- 🎤 Voice Interview Started ---")
        
        while True:
            # 1. Record and Send
            await record_and_send(websocket)
            
            # 2. Receive Response
            print("Waiting for response...")
            response = await websocket.recv()
            data = json.loads(response)
            
            # 3. Display Results
            metrics = data['metrics']
            print("\n" + "="*40)
            print(f"📝 You said: \"{data.get('transcript', 'No text detected')}\"")
            print(f"🔊 Volume: {metrics.get('volume')} | ⚡ Speed: {metrics.get('wpm')} WPM")
            print(f"🤖 AI Reply: {data['reply']}")
            print("="*40 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(start_interview())
    except KeyboardInterrupt:
        print("\nExiting...")