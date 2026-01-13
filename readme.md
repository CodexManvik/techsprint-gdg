# 🤖 The Interview Mirror (MUJ TechSprint)

**An AI-powered Interview Coach that "sees" and "hears" you.**
Built for the Manipal University Jaipur Placement Cell to help students practice technical interviews with real-time body language analysis.

## 🚀 Features
* **Real-time Vision Analysis:** Tracks Eye Contact, Fidgeting, and Head Gestures (Nodding/Shaking) using **Google MediaPipe**.
* **Conversational AI:** Simulates aggressive (Dell) or behavioral (Deloitte) recruiter personas using **Google Gemini 1.5**.
* **Resume Integration:** Upload a PDF resume, and the AI generates questions based on your specific projects.
* **Voice Interaction:** Speak your answers naturally; the system transcribes and analyzes speech rate (WPM) and volume.

---

## 🛠️ Setup Instructions

### 1. Clone & Install Dependencies
```bash
git clone <your-repo-url>
cd <your-repo-folder>

# Create virtual environment (Optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install libraries
pip install -r requirements.txt

# Make a .env file and add your google api key
GOOGLE_API_KEY=your_actual_api_key_here

# Download and place the ffmpeg.exe and ffmprobe.exe file in the root folder 
https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build.7z

# Run Backend using 
uvicorn app:app --reload

# Run Frontend in a different terminal using 
cd frontend
python -m http.server 3000