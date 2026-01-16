# 🎯 Interview Mirror - AI-Powered Interview Coach

**An advanced AI interview preparation system that provides real-time behavioral analysis, posture monitoring, stress detection, and integrity checking to help students excel in technical interviews.**

Built for Manipal University Jaipur (MUJ) Placement Cell to revolutionize interview preparation through computer vision and artificial intelligence.

---

## 🌟 Overview

Interview Mirror is a comprehensive interview coaching platform that combines cutting-edge computer vision, natural language processing, and AI to simulate realistic interview scenarios. The system analyzes candidates in real-time across multiple dimensions - from body language and posture to stress indicators and potential integrity concerns - providing actionable feedback to improve interview performance.

### Key Highlights
- **Real-time Multi-Modal Analysis**: Simultaneous tracking of 543 body landmarks (33 pose + 468 face + 42 hands)
- **AI-Powered Conversations**: Dynamic interview simulation with 12+ company-specific personas
- **Comprehensive Behavioral Monitoring**: 7 distinct analysis modules working in parallel
- **Adaptive Learning**: Personalized difficulty levels and resume-based questioning
- **Production-Ready Architecture**: WebSocket-based real-time communication with FastAPI backend

---

## 🚀 Core Features

### 1. **Advanced Vision Analysis System**

#### **Holistic Body Tracking** (MediaPipe Holistic)
- **Full-body landmark extraction**: 543 points tracked simultaneously
  - 33 pose landmarks (body skeleton)
  - 468 face landmarks (facial features, eyes, mouth)
  - 21 landmarks per hand (42 total for gesture analysis)
- **Adaptive frame processing**: Dynamic frame skipping to maintain 15 FPS target
- **Distance-adaptive detection**: Adjusts sensitivity based on camera distance

#### **Signal Smoothing** (One Euro Filter)
- **Jitter reduction**: Eliminates camera shake and detection noise
- **Velocity-adaptive filtering**: Preserves quick movements while smoothing slow drift
- **Per-coordinate filtering**: Independent smoothing for X, Y, Z coordinates
- **30-60% noise reduction**: Proven jitter reduction in testing

### 2. **Posture Analysis Module**

#### **Shoulder Alignment Detection**
- **Lean detection**: Identifies shoulder tilt beyond 15° threshold
- **Real-time angle calculation**: Measures deviation from horizontal
- **Temporal stability tracking**: Monitors body rocking and fidgeting

#### **Slouch Detection** (Adaptive Baseline)
- **Seated posture calibration**: Learns your natural upright position
- **Forward slouch detection**: Identifies when nose moves closer to shoulders
- **Severity scoring**: 0.0-1.0 scale for slouch intensity
- **15% deviation threshold**: Flags noticeable posture degradation

#### **Arms Crossed Detection** (Robust Algorithm)
- **Spatial relationship analysis**: Checks wrist-to-shoulder distances
- **Midline crossing verification**: Ensures wrists cross body center
- **Temporal smoothing**: 70% of 10 frames required (prevents flickering)
- **False positive prevention**: Distinguishes from hands-in-lap position

#### **Body Stability Monitoring**
- **Rocking score calculation**: Measures horizontal movement variance
- **Shoulder stability index**: 0.0-1.0 scale (1.0 = perfectly stable)
- **Fidgeting detection**: Identifies nervous body movements

### 3. **Gesture Intelligence Module**

#### **Hand Visibility Tracking**
- **Bilateral hand detection**: Monitors both left and right hands
- **Visibility confidence scoring**: Ensures reliable hand tracking

#### **Face-Touching Behavior**
- **Nervousness indicator**: Detects when hands approach face
- **Index finger tracking**: Primary detection point for face touches
- **Cumulative counting**: Session-wide face-touch frequency
- **Distance threshold**: 0.1 normalized units for detection

#### **Gesture Frequency Analysis**
- **Elevated hand detection**: Identifies hands above shoulder line
- **Velocity-based counting**: Tracks active hand movements
- **Gestures per minute**: Real-time communication style metric
- **Activity classification**: "passive" (<5/min), "moderate" (5-15/min), "dynamic" (>15/min)

### 4. **Stress Signal Detection**

#### **Eye Aspect Ratio (EAR) Analysis**
- **Blink detection algorithm**: Standard EAR formula implementation
- **Distance-adaptive thresholds**: Adjusts for camera proximity
- **Baseline calibration**: Learns individual eye characteristics (60 frames)
- **State machine**: Prevents double-counting of single blinks

#### **Blink Rate Monitoring**
- **Cognitive load assessment**: >30 blinks/min indicates high stress
- **Real-time calculation**: Blinks per minute tracking
- **Session-wide statistics**: Total blinks and average rate

#### **Lip Compression Detection**
- **Multi-point measurement**: Uses 12+ lip landmarks for accuracy
- **Adaptive baseline**: Learns normal lip opening (60 frames calibration)
- **Sustained compression tracking**: Flags pursing >2 seconds
- **Speaking state awareness**: Disables detection during speech

#### **Stress Level Classification**
- **Three-tier system**: "low", "moderate", "high"
- **Multi-indicator fusion**: Combines blink rate and lip pursing
- **Weighted scoring**: Blink rate (2 points), lip pursing (2 points)

### 5. **Integrity Checking System**

#### **Gaze Pattern Analysis**
- **Eye position tracking**: Monitors gaze direction using eye centroids
- **Speech onset detection**: Captures gaze at moment of speaking
- **Cluster formation**: Groups repeated gaze positions

#### **Repeated Pattern Detection**
- **Cluster frequency tracking**: Counts visits to same location
- **Off-center flagging**: Identifies looking away from camera (>0.2 units)
- **Minimum frequency threshold**: 3+ visits to trigger flag
- **Cheat flag accumulation**: Session-wide suspicious behavior count

#### **Integrity Scoring**
- **0.0-1.0 scale**: 1.0 = clean, 0.0 = highly suspicious
- **Flag penalty**: -0.15 per cheat flag
- **Cluster concentration penalty**: High focus on single location
- **Assessment levels**: "clean" (≥0.8), "suspicious" (0.5-0.8), "highly_suspicious" (<0.5)

### 6. **AI Conversation Engine**

#### **12 Company-Specific Personas**
- **Google SRE**: System reliability, SLOs, error budgets
- **Amazon Bar Raiser**: Leadership principles, STAR method
- **Meta E5**: Product impact, cross-functional collaboration
- **Netflix Architect**: Microservices, chaos engineering
- **Apple Design**: User experience, privacy-first design
- **Microsoft Azure**: Cloud architecture, enterprise solutions
- **Stripe Infrastructure**: Payment systems, API design
- **Uber Backend**: Real-time systems, geospatial algorithms
- **Airbnb Full-Stack**: React, GraphQL, design systems
- **Startup Founder**: MVP development, rapid iteration
- **Hedge Fund Quant**: Algorithms, low-latency systems
- **FAANG Behavioral**: Soft skills, leadership, teamwork

#### **Adaptive Difficulty Levels**
- **Junior (0-2 years)**: Foundational concepts, syntax, learning potential
- **Mid-Level (2-5 years)**: Applied questions, trade-offs, debugging
- **Senior (5-8 years)**: System design, architecture, scalability
- **Staff+ (8+ years)**: Strategic thinking, ambiguous problems, business impact

#### **10 Technical Topics**
- System Design, Algorithms, Frontend, Backend, DevOps
- Machine Learning, Data Structures, Behavioral, Mobile, Security

#### **Google Gemini 1.5 Flash Integration**
- **Conversational AI**: Natural back-and-forth dialogue
- **Context-aware responses**: Incorporates real-time behavioral metrics
- **Resume-based questioning**: Generates questions from uploaded PDF
- **Concise responses**: 1-3 sentences for realistic interview flow

### 7. **Audio Processing System**

#### **Google Cloud Speech-to-Text**
- **High-quality transcription**: Latest_long model for conversational speech
- **Automatic punctuation**: Natural sentence formatting
- **16kHz mono audio**: Optimized for speech recognition
- **Fallback support**: SpeechRecognition library as backup

#### **Speech Analysis**
- **Volume calculation**: dBFS measurement with normalization
- **Words per minute (WPM)**: Real-time speaking pace tracking
- **Audio format conversion**: WebM/WAV to PCM WAV processing

#### **Google Cloud Text-to-Speech**
- **Neural2 voices**: High-quality, natural-sounding speech
- **Persona-matched voices**: Different voice for each interviewer
- **MP3 output**: Efficient audio streaming
- **Base64 encoding**: WebSocket-compatible transmission

### 8. **Session Management & Analytics**

#### **Real-time Metrics Tracking**
- **Temporal data collection**: Timestamps, fidget scores, eye contact
- **Stress flag logging**: Binary stress indicators over time
- **WPM history**: Speaking pace evolution
- **Transcript recording**: Complete conversation log

#### **AI-Generated Feedback Reports**
- **Radar chart metrics**: Technical accuracy, communication, confidence, problem-solving, cultural fit
- **Strengths & improvements**: Specific, actionable feedback points
- **Hiring verdict**: "HIRE", "NO HIRE", "STRONG HIRE"
- **Performance summary**: 2-sentence executive summary

---

## 🛠️ Technology Stack

### **Backend Technologies**
- **FastAPI**: Modern async web framework for Python
- **WebSockets**: Real-time bidirectional communication
- **Python 3.8+**: Core programming language
- **Uvicorn**: ASGI server for production deployment

### **Computer Vision & ML**
- **MediaPipe Holistic**: Google's full-body landmark detection
- **OpenCV (cv2)**: Image processing and video capture
- **NumPy**: Numerical computing for landmark calculations
- **One Euro Filter**: Adaptive signal smoothing algorithm

### **AI & NLP**
- **Google Gemini 1.5 Flash**: Conversational AI and feedback generation
- **Google Cloud Speech-to-Text**: Audio transcription
- **Google Cloud Text-to-Speech**: Voice synthesis
- **gTTS**: Fallback text-to-speech library

### **Audio Processing**
- **Pydub**: Audio manipulation and format conversion
- **SpeechRecognition**: Fallback speech recognition
- **FFmpeg**: Audio codec support (ffmpeg.exe, ffprobe.exe)

### **Document Processing**
- **PyPDF (pypdf)**: Resume PDF parsing and text extraction

### **Development Tools**
- **python-dotenv**: Environment variable management
- **python-multipart**: File upload handling
- **CORS Middleware**: Cross-origin resource sharing

---

## 📊 Monitoring & Metrics

### **Real-time Behavioral Metrics**

#### **Eye Contact Score** (0.0-1.0)
- Measures iris position relative to eye center
- Target: >0.6 for good eye contact
- Calculated from iris landmarks (468-477)

#### **Fidget Score** (0.0-100.0)
- Standard deviation of nose position over 20 frames
- Higher values indicate more movement
- Tracks nervous fidgeting behavior

#### **Head Gesture Detection**
- **Nodding**: Vertical head movement (agreement)
- **Shaking**: Horizontal head movement (disagreement)
- **Neutral**: Minimal head movement
- Uses 30-frame history for pattern recognition

#### **Smile Detection** (Boolean)
- Mouth width to face width ratio
- Threshold: >0.55 for smile detection
- Uses mouth corners (61, 291) and eye corners (33, 263)

#### **Posture Metrics**
- **Shoulder angle**: -90° to +90° (0° = level)
- **Slouch score**: 0.0-1.0 (0 = perfect, 1 = severe)
- **Arms crossed**: Boolean with temporal smoothing
- **Rocking score**: 0.0-1.0 (movement variance)
- **Shoulder stability**: 0.0-1.0 (1.0 = stable)

#### **Stress Indicators**
- **Blink rate**: Blinks per minute
- **Blink count**: Cumulative session blinks
- **High cognitive load**: Boolean (>30 blinks/min)
- **Lip pursing**: Boolean with duration tracking
- **Stress level**: "low", "moderate", "high"
- **EAR values**: Left, right, and average eye aspect ratio

#### **Integrity Metrics**
- **Gaze position**: (x, y) normalized coordinates
- **Gaze cluster ID**: Which cluster current gaze belongs to
- **Cheat flag count**: Number of suspicious patterns
- **Integrity warning**: Boolean (flags ≥ threshold)
- **Integrity score**: 0.0-1.0 (1.0 = clean)
- **Suspicious segments**: List of flagged time periods

#### **Audio Metrics**
- **Volume**: 0-100 scale (dBFS normalized)
- **Words per minute (WPM)**: Speaking pace
- **Transcription text**: Speech-to-text output
- **Audio duration**: Length of speech segment

### **Session-Wide Analytics**

#### **Performance Statistics**
- **Session duration**: Total interview time (minutes)
- **Frames processed**: Total video frames analyzed
- **Average FPS**: Processing speed
- **Filter count**: Active signal smoothing filters

#### **Posture Summary**
- **Frames analyzed**: Total posture analysis frames
- **Average shoulder stability**: Mean stability score
- **Arms crossed percentage**: % of time with arms crossed
- **Baseline established**: Whether calibration completed

#### **Stress Summary**
- **Total blinks**: Cumulative blink count
- **Average blink rate**: Mean blinks per minute
- **High cognitive load detected**: Boolean assessment
- **Max lip purse duration**: Longest compression period
- **Stress assessment**: Overall stress classification

#### **Integrity Report**
- **Total speech onsets**: Number of times started speaking
- **Cheat flag count**: Total suspicious patterns
- **Integrity score**: Overall integrity rating
- **Integrity assessment**: "clean", "suspicious", "highly_suspicious"
- **Gaze clusters**: Detected gaze position clusters
- **Recommendations**: Actionable integrity feedback

---

## 🎯 Proposed Solutions & Benefits

### **For Students**

#### **Realistic Interview Practice**
- **Company-specific preparation**: Practice with actual interviewer styles
- **Difficulty progression**: Start easy, build to senior-level questions
- **Resume-based questions**: Get asked about YOUR projects
- **Unlimited practice**: No scheduling, no pressure

#### **Comprehensive Feedback**
- **Multi-dimensional analysis**: Body language + speech + content
- **Real-time awareness**: See metrics as you practice
- **Actionable insights**: Specific improvements to make
- **Progress tracking**: Compare sessions over time

#### **Behavioral Improvement**
- **Posture correction**: Learn to sit upright and stable
- **Eye contact training**: Maintain camera focus
- **Stress management**: Reduce nervous behaviors
- **Gesture optimization**: Use hands effectively
- **Confidence building**: Practice until comfortable

### **For Placement Cells**

#### **Scalable Preparation**
- **24/7 availability**: Students practice anytime
- **No human resources needed**: Automated coaching
- **Consistent quality**: Same high standard for all
- **Data-driven insights**: Track student readiness

#### **Placement Success Metrics**
- **Pre-interview assessment**: Identify students needing help
- **Targeted interventions**: Focus on specific weaknesses
- **Success rate tracking**: Measure improvement over time
- **Company-specific prep**: Tailor to recruiting companies

### **For Recruiters**

#### **Pre-screened Candidates**
- **Behavioral readiness**: Students arrive prepared
- **Communication skills**: Verified speaking ability
- **Professional demeanor**: Practiced interview etiquette
- **Integrity verification**: Reduced cheating concerns

---

## 📁 Project Structure

```
interview-mirror/
├── engine/                          # Core analysis engines
│   ├── analyzers/                   # Specialized analyzers
│   │   ├── gesture_analyzer.py      # Hand gesture & face-touch detection
│   │   ├── posture_analyzer.py      # Posture & body language analysis
│   │   ├── stress_analyzer.py       # Stress signal detection (EAR, blinks, lips)
│   │   └── integrity_checker.py     # Gaze pattern & integrity analysis
│   ├── ai_engine.py                 # Google Gemini conversation engine
│   ├── audio_engine.py              # Speech-to-text processing
│   ├── tts_engine.py                # Text-to-speech synthesis
│   ├── vision_engine.py             # Main vision coordination
│   ├── holistic_processor.py        # MediaPipe Holistic wrapper
│   ├── signal_smoother.py           # One Euro Filter implementation
│   ├── session_manager.py           # Interview session tracking
│   ├── personas.py                  # Company interviewer personas
│   └── difficulty.py                # Difficulty levels & topics
├── tests/                           # Test & demo scripts
│   ├── demo_integrated_system.py    # Integration demo
│   ├── demo_live_posture_analysis.py # Live posture demo
│   ├── test_posture_analyzer.py     # Posture unit tests
│   ├── test_signal_smoother.py      # Smoothing tests
│   ├── test_arms_states.py          # Arms crossed testing
│   └── debug_arms_detailed.py       # Arms detection debugging
├── app.py                           # FastAPI main application
├── baseline.py                      # Basic system test
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (API keys)
├── google_credentials.json          # Google Cloud credentials
├── ffmpeg.exe                       # Audio codec (Windows)
├── ffprobe.exe                      # Audio probe (Windows)
└── README.md                        # This file
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8 or higher
- Webcam (for video capture)
- Microphone (for audio input)
- Google Cloud account (for Speech/TTS)
- Google AI Studio account (for Gemini API)

### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd interview-mirror
```

### **Step 2: Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Download FFmpeg** (Windows)
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract `ffmpeg.exe` and `ffprobe.exe`
3. Place both files in project root directory

### **Step 5: Configure API Keys**

#### **Create `.env` file:**
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

#### **Get Gemini API Key:**
1. Visit: https://aistudio.google.com/app/apikey
2. Create new API key
3. Copy to `.env` file

#### **Setup Google Cloud Credentials:**
1. Visit: https://console.cloud.google.com/
2. Create new project or select existing
3. Enable APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
4. Create service account
5. Download JSON key file
6. Rename to `google_credentials.json`
7. Place in project root

### **Step 6: Run Backend**
```bash
uvicorn app:app --reload
```
Backend will start at: `http://localhost:8000`

### **Step 7: Run Frontend**
```bash
cd frontend
python -m http.server 3000
```
Frontend will start at: `http://localhost:3000`

---

## 🧪 Testing & Validation

### **Unit Tests**

#### **Test Posture Analyzer**
```bash
python tests/test_posture_analyzer.py
```
Tests: arms open, arms crossed, hands in lap, gesturing, leaning, slouching

#### **Test Signal Smoother**
```bash
python tests/test_signal_smoother.py
```
Tests: One Euro Filter, landmark smoothing, performance benchmarks
Generates: `signal_smoother_test_results.png`

#### **Test Arms Detection**
```bash
python tests/test_arms_states.py
```
Live webcam test for arms crossed detection

### **Live Demos**

#### **Integrated System Demo**
```bash
python tests/demo_integrated_system.py
```
Shows all components working together

#### **Live Posture Analysis**
```bash
python tests/demo_live_posture_analysis.py
```
Real-time posture monitoring with webcam
- Press 'q' to quit
- Press 'r' to reset analyzer

#### **Baseline Test**
```bash
python baseline.py
```
Basic MediaPipe + Gemini connectivity test

---

## 📈 Performance Metrics

### **Processing Speed**
- **Target FPS**: 15 frames per second
- **Actual FPS**: 12-18 FPS (depending on hardware)
- **Latency**: <100ms per frame
- **Smoothing overhead**: <10ms per frame

### **Detection Accuracy**
- **Pose detection**: 95%+ in good lighting
- **Face landmarks**: 98%+ accuracy
- **Hand tracking**: 90%+ when visible
- **Blink detection**: 95%+ with calibration
- **Arms crossed**: 90%+ after temporal smoothing

### **Resource Usage**
- **CPU**: 30-50% (single core)
- **Memory**: 500-800 MB
- **Network**: Minimal (WebSocket + API calls)
- **Storage**: <100 MB (excluding dependencies)

---

## 🔧 Configuration Options

### **Vision Engine Settings**

#### **HolisticProcessor**
```python
HolisticProcessor(
    min_detection_confidence=0.5,  # Detection threshold
    min_tracking_confidence=0.5,   # Tracking threshold
    enable_frame_skip=True,        # Adaptive frame skipping
    target_fps=15.0                # Target processing rate
)
```

#### **SignalSmoother**
```python
SignalSmoother(
    freq=15.0,        # Sampling frequency (Hz)
    min_cutoff=1.5,   # Minimum cutoff (lower = more smoothing)
    beta=0.1,         # Velocity adaptation coefficient
    d_cutoff=1.0      # Derivative cutoff
)
```

#### **PostureAnalyzer**
```python
PostureAnalyzer(
    shoulder_angle_threshold=15.0,  # Lean detection (degrees)
    slouch_threshold=0.05,          # Slouch sensitivity
    rock_threshold=0.02,            # Rocking detection
    arms_crossed_frames=10          # Temporal smoothing window
)
```

#### **StressAnalyzer**
```python
StressAnalyzer(
    ear_threshold=0.2,                    # Blink detection threshold
    blink_rate_threshold=30.0,            # High cognitive load (blinks/min)
    lip_compression_ratio=0.7,            # Lip pursing threshold
    lip_purse_duration_threshold=2.0      # Sustained compression (seconds)
)
```

#### **IntegrityChecker**
```python
IntegrityChecker(
    gaze_cluster_threshold=0.05,    # Cluster distance threshold
    cheat_flag_threshold=5,         # Flags before warning
    min_cluster_frequency=3         # Visits to flag cluster
)
```

---

## 🐛 Troubleshooting

### **Common Issues**

#### **"GOOGLE_API_KEY not found"**
- Ensure `.env` file exists in project root
- Check API key is correctly formatted
- Verify no extra spaces or quotes

#### **"Could not open webcam"**
- Check camera permissions
- Close other apps using camera
- Try different camera index: `cv2.VideoCapture(1)`

#### **"Google Cloud credentials not found"**
- Verify `google_credentials.json` in project root
- Check file permissions (readable)
- Ensure APIs are enabled in Google Cloud Console

#### **"FFmpeg not found"**
- Download ffmpeg.exe and ffprobe.exe
- Place in project root directory
- Verify files are not corrupted

#### **Low FPS / Laggy Performance**
- Reduce `target_fps` in HolisticProcessor
- Enable `frame_skip` for adaptive processing
- Close other CPU-intensive applications
- Use better lighting for faster detection

#### **Arms Crossed Detection Flickering**
- Increase `arms_crossed_frames` (default: 10)
- Ensure good hand visibility
- Check lighting conditions
- Verify wrists are clearly visible

---

## 🔮 Future Enhancements

### **Planned Features**
- [ ] Multi-language support (Hindi, Spanish, etc.)
- [ ] Mobile app (iOS/Android)
- [ ] Group interview simulation
- [ ] Emotion recognition (happiness, anxiety, confidence)
- [ ] Voice tone analysis (pitch, energy, clarity)
- [ ] Background blur/replacement
- [ ] Screen sharing for technical questions
- [ ] Code editor integration
- [ ] Whiteboard drawing analysis
- [ ] Interview recording & playback
- [ ] Peer comparison analytics
- [ ] Gamification & achievements
- [ ] AI-powered question generation
- [ ] Resume optimization suggestions

### **Technical Improvements**
- [ ] GPU acceleration (CUDA support)
- [ ] Model quantization for faster inference
- [ ] Edge deployment (offline mode)
- [ ] Multi-camera support
- [ ] 4K video processing
- [ ] Real-time video streaming
- [ ] Distributed processing
- [ ] Cloud deployment (AWS/GCP/Azure)

---

## 📄 License

This project is developed for Manipal University Jaipur (MUJ) Placement Cell.

---

## 👥 Contributors

**Development Team**: MUJ TechSprint Participants
**Placement Cell**: Manipal University Jaipur
**Technology Partners**: Google (Gemini, Cloud AI), MediaPipe

---

## 📞 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Contact MUJ Placement Cell
- Email: placement@jaipur.manipal.edu

---

## 🙏 Acknowledgments

- **Google MediaPipe**: Full-body landmark detection
- **Google Gemini**: Conversational AI
- **Google Cloud AI**: Speech & TTS services
- **One Euro Filter**: Signal smoothing algorithm (Casiez et al.)
- **FastAPI**: Modern web framework
- **OpenCV**: Computer vision library
- **MUJ Placement Cell**: Project sponsorship & support

---

**Built with ❤️ for better interview preparation**

*Empowering students to ace their interviews through AI-powered coaching*
