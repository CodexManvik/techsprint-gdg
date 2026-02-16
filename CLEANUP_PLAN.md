# Redundant Files Cleanup Plan

## 🗑️ Files to DELETE (Test/Debug Scripts)

### Development Test Files (No longer needed)
- `baseline.py` - Old baseline test script
- `check_bcrypt.py` - Bcrypt verification test
- `check_mp.py` - MediaPipe check
- `diag.py` - Diagnostics script
- `verify_chat.py` - Chat verification test
- `backend_requirements.txt` - Duplicate of requirements.txt content

### Old Test Files (Superseded by new test_setup.py)
- `test_client.py` - Old client test
- `test_client_audio.py` - Old audio test
- `test_google_cloud.py` - Google Cloud test
- `tests/verify_auth_flow.py` - Auth flow verification
- `tests/verify_chat_analysis.py` - Chat analysis test

**Total**: 11 files to remove

## ✅ Files to KEEP

### Core Backend
- `app.py` - Old backend (keep for now during migration)
- `database.py` - Database layer (will migrate later)
- `backend/` - New refactored backend
- `engine/` - Legacy engines (keep until fully migrated)

### Frontend (DO NOT TOUCH)
- `frontend/` - Main React frontend
- `interview-mirror-frontend/` - Second frontend

### Infrastructure
- `.env`, `.env.example` - Config
- `requirements.txt` - Dependencies
- `google_credentials.json` - GCP credentials
- `interview_data.db` - Database
- `ffmpeg.exe`, `ffprobe.exe` - Audio processing
- `readme.md`, `BACKEND_README.md` - Documentation
- `test_setup.py` - NEW test script

### Archives
- `Shader Reminder (Community).zip` - ? (ask user if needed)
