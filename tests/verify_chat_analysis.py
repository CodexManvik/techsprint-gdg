import sys
import os
import json
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import Database
from engine.ai_engine import AIEngine

def test_chat_analysis():
    print("🚀 Starting verification...")
    
    # 1. Init DB
    if os.path.exists("interview_data.db"):
        os.remove("interview_data.db")
    
    db = Database()
    
    # 2. Create Session
    session_id = "test_session_123"
    db.create_session(session_id, "FAANG_Architect", "System Design", "Intermediate")
    
    # 3. Add Messages
    transcript = [
        {"role": "ai", "content": "Tell me about CAP theorem."},
        {"role": "user", "content": "CAP theorem means you can only have two out of three: Consistency, Availability, and Partition tolerance."},
        {"role": "ai", "content": "How would you choose between AP and CP?"},
        {"role": "user", "content": "It depends on the system requirements. Banking needs CP, social media AP."}
    ]
    
    for msg in transcript:
        db.add_message(session_id, msg["role"], msg["content"])
        
    print("✅ Chat history populated")
    
    # 4. Simulate Report Gen
    print("🤖 Triggering AI Report Generation (this calls the LLM)...")
    
    # Mock AI Engine to avoid real API call costs during verification if desired
    # But user wants real feature, so let's try with dev_mode=True first to verify logic
    ai = AIEngine(dev_mode=True) 
    
    chat_history = db.get_messages(session_id)
    ai_report = ai.generate_feedback_report(chat_history)
    
    print(f"📊 AI Report Summary: {ai_report.get('summary')}")
    
    # 5. Update DB
    for msg_analysis in ai_report.get("detailed_analysis", []):
        if "id" in msg_analysis:
            db.update_message_analysis(
                msg_analysis["id"], 
                msg_analysis.get("rating"), 
                msg_analysis.get("feedback"), 
                msg_analysis.get("improved_answer")
            )
            
    # 6. Verify DB Content
    updated_messages = db.get_messages(session_id)
    user_msgs = [m for m in updated_messages if m['role'] == 'user']
    
    verified = True
    for m in user_msgs:
        print(f"   User Msg [{m['id']}]: Rating={m['rating']} | Improved='{m['improved_answer'][:30]}...'")
        if m['rating'] is None or m['improved_answer'] is None:
            verified = False
            
    if verified:
        print("✅ SUCCESS: Chat analysis saved to DB!")
    else:
        print("❌ FAILURE: Analysis missing in DB.")

if __name__ == "__main__":
    test_chat_analysis()
