import sys
import os
import requests
import uuid
import time

# Base URL (assuming local server running)
BASE_URL = "http://localhost:8000"

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def test_auth_flow():
    log("🚀 Starting Auth Flow Verification...")

    # 1. Register User
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "secure_password_123"
    full_name = "Test User"
    
    log(f"Attempting to register: {email}")
    try:
        reg_res = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name
        })
        if reg_res.status_code != 200:
            log(f"Registration failed: {reg_res.text}", "ERROR")
            return
        log("✅ Registration Successful")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        return

    # 2. Login
    log("Attempting login...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": password
    })
    
    if login_res.status_code != 200:
        log(f"Login failed: {login_res.text}", "ERROR")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("✅ Login Successful, Token acquired")

    # 3. Check /auth/me
    me_res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if me_res.status_code == 200:
        log(f"✅ Verified User: {me_res.json()['email']}")
    else:
        log(f"❌ Failed to get user info: {me_res.text}", "ERROR")

    # 4. Start Interview (Protected)
    log("Starting Interview Session...")
    start_res = requests.post(f"{BASE_URL}/api/start-interview", json={
        "persona": "FAANG_Architect",
        "difficulty": "Junior",
        "topic": "System Design"
    }, headers=headers)
    
    if start_res.status_code == 200:
        session_id = start_res.json()["session_id"]
        log(f"✅ Session Started: {session_id}")
    else:
        log(f"❌ Failed to start session: {start_res.text}", "ERROR")
        return

    # 5. Check History
    log("Checking User History...")
    history_res = requests.get(f"{BASE_URL}/api/history", headers=headers)
    if history_res.status_code == 200:
        sessions = history_res.json()
        if len(sessions) > 0 and sessions[0]['session_id'] == session_id:
             log(f"✅ History verified. Found {len(sessions)} sessions.")
        else:
             log(f"⚠️ History empty or mismatch. Data: {sessions}", "WARN")
    else:
        log(f"❌ Failed to get history: {history_res.text}", "ERROR")

    log("🎉 Auth Flow Verification Complete!")

if __name__ == "__main__":
    # Ensure server is running for this test
    try:
        requests.get(f"{BASE_URL}/")
        test_auth_flow()
    except:
        log("Server not running @ localhost:8000. Start uvicorn first.", "ERROR")
