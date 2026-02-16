import asyncio
import websockets
import json

# test_client.py

async def start_interview():
    uri = "ws://localhost:8000/ws/interview"
    async with websockets.connect(uri) as websocket:
        print("--- Interview Started (Type 'exit' to quit) ---")
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break

            # Send actual text + mock landmarks
            payload = {
                "text": user_input,
                "landmarks": [{"x": 0.5, "y": 0.5}] * 478 
            }
            
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            data = json.loads(response)
            
            metrics = data['metrics']
            print(f"\nAI Recruiter: {data['reply']}")
            print(f"--- Vision Metrics ---")
            print(f"Eye Contact: {metrics.get('eye_contact_score')}")
            print(f"Gesture: {metrics.get('head_gesture').upper()}")  # New!
            print(f"Smiling: {metrics.get('is_smiling')}")            # New!
            print(f"Fidget Score: {metrics.get('fidget_score')}\n")

asyncio.run(start_interview())