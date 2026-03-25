# 🤖 The Interview Mirror (MUJ TechSprint)

**An AI-powered Interview Coach that "sees" and "hears" you.**

Built for the Manipal University Jaipur Placement Cell to help students practice technical interviews with real-time body language analysis, conversational AI, and personalized feedback.

---

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Backend Architecture](#backend-architecture-deep-dive)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [Environment Configuration](#environment-configuration)
- [API Documentation](#api-documentation)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**The Interview Mirror** is a comprehensive AI-powered interview preparation platform that combines:
- **Computer Vision Analysis** - Real-time body language feedback using MediaPipe
- **LLM-powered Conversations** - Dynamic interview simulations with multiple recruiter personas
- **Voice Processing** - Automatic speech-to-text and prosody analysis (speaking rate, volume)
- **Resume Integration** - AI generates context-aware questions from your PDF resume
- **Session Persistence** - Full interview history and performance reports

The system is designed to provide actionable feedback on both technical answers and non-verbal communication patterns critical for interview success.

---

## 🚀 Key Features

### 1. **Real-time Vision Analysis**
- Detects **eye contact patterns** (looking at camera vs away)
- Identifies **fidgeting behavior** (hand movements, posture shifts)
- Recognizes **head gestures** (nodding for agreement, shaking for doubt)
- Uses **Google MediaPipe** for lightweight, accurate pose/hand detection
- Provides real-time feedback overlay on video feed

### 2. **Conversational AI with Personas**
- Multiple recruiter **personas**: Aggressive (Dell, Amazon), Behavioral (Deloitte, Accenture), Technical (Google, Meta)
- **Circuit breaker pattern** ensures graceful degradation when LLM is unavailable
- **Context-aware responses** that adapt to user answers and interview flow
- Supports both **streaming** (real-time token delivery) and **non-streaming** chat modes
- **Multi-turn conversation** memory with automatic context management

### 3. **Resume Processing**
- Upload PDF resumes and the AI extracts project details
- Generates **personalized technical questions** based on your experience
- Maintains conversation history within session context
- Handles multiple file uploads with proper validation

### 4. **Voice Interaction & Analysis**
- **Automatic speech-to-text** transcription (Google Cloud Speech API)
- **Prosody metrics**: Speaking rate (WPM), volume levels, speech pace
- **Text-to-speech responses** with persona-specific voice characteristics
- **Audio quality metrics** to identify mic/background noise issues

### 5. **Session Management & Analytics**
- **Interview history** with full session transcripts
- **Performance reports** with scores on:
  - Eye contact consistency
  - Answer quality and relevance
  - Speech patterns and clarity
  - Overall confidence indicators
- **Redis caching** for fast session retrieval
- **SQLite persistence** for long-term data storage

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/Vue)                    │
│              Video Feed + WebSocket Connection              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬──────────────┐
        │                         │              │
    ┌───▼────────┐      ┌────────▼────────┐   ┌─▼──────────┐
    │   WebSocket│      │   REST API      │   │ Video      │
    │   Routes   │      │   Routes        │   │ Processing│
    └───┬────────┘      └────────┬────────┘   └─┬──────────┘
        │                        │              │
        └────────────┬───────────┴──────────────┘
                     │
        ┌────────────▼──────────────────────┐
        │    FastAPI Application Core       │
        │   (CORS, Middleware, Routing)    │
        └────────────┬──────────────────────┘
                     │
    ┌────────────────┼─────────────┬───────────────┐
    │                │             │               │
┌───▼──────┐  ┌─────▼──────┐ ┌───▼────┐  ┌──────▼────┐
│Interview │  │Interview   │ │Circuit │  │Redis Cache│
│Engine    │  │Analyzer    │ │Breaker │  │(Sessions) │
└───┬──────┘  └─────┬──────┘ └───┬────┘  └──────┬────┘
    │               │            │               │
    │        ┌──────▼────────┐   │               │
    │        │ LLM Client    │   │               │
    │        │(Ollama/Gemini)│◄──┘               │
    │        └──────┬────────┘                   │
    │               │                            │
    └───────┬───────┼────────────────┬───────────┘
            │       │                │
        ┌───▼───┬──▼───┬────────┬───▼────┐
        │SQLite ├─────┤ Google  │ Ollama │
        │ DB    │Redis │ APIs   │ Server │
        └───────┴──────┴────────┴────────┘
```

---

## 🔧 Backend Architecture (Deep Dive)

### **1. Technology Stack**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.120+ | Async HTTP server with automatic OpenAPI docs |
| **ASGI Server** | Uvicorn | High-performance ASGI application server |
| **Database** | SQLite (aiosqlite) | Persistent session storage with async I/O |
| **Cache** | Redis | Fast session state retrieval and real-time data |
| **LLM** | Ollama (Primary), Google Gemini (Fallback) | Conversation engine |
| **HTTP Client** | httpx | Async HTTP with connection pooling |
| **Authentication** | JWT (PyJWT + Passlib) | Stateless user authentication |
| **Settings** | Pydantic Settings | Centralized environment configuration |

### **2. Directory Structure**

```
backend/
├── main.py                          # FastAPI factory & lifespan management
├── __init__.py
│
├── api/                             # Request/Response handlers
│   ├── routes/
│   │   ├── auth.py                 # Authentication (register, login, JWT)
│   │   ├── sessions.py             # Interview session lifecycle
│   │   ├── websocket.py            # Real-time voice/video WebSocket
│   │   └── __init__.py
│   └── __init__.py
│
├── config/                          # Configuration management
│   ├── settings.py                 # Pydantic BaseSettings + validation
│   └── __init__.py
│
├── core/                            # Business logic & core services
│   ├── cache.py                    # Redis cache manager (JSON serialization)
│   ├── __init__.py
│   │
│   ├── llm/                        # Large Language Model abstraction
│   │   ├── base.py                 # Abstract LLMClient interface
│   │   ├── ollama.py               # Ollama-specific implementation
│   │   ├── circuit_breaker.py      # Fault tolerance pattern
│   │   └── __init__.py
│   │
│   └── interview/                  # Interview orchestration
│       ├── engine.py               # InterviewEngine main class
│       ├── analyzer.py             # Body language analysis
│       └── __init__.py
│
└── db/                              # Data persistence
    ├── repository.py               # Async database operations
    └── __init__.py
```

### **3. Core Modules Explained**

#### **A. FastAPI Application Factory** (`main.py`)

The application uses FastAPI's **lifespan context manager** for robust startup/shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP PHASE
    await init_db()                    # Initialize SQLite with schema
    await redis_cache.connect()        # Connect to Redis
    llm_client = OllamaClient()       # Initialize LLM HTTP client
    interview_engine = InterviewEngine()
    
    yield  # ← Application serves requests here
    
    # SHUTDOWN PHASE
    await close_db()
    await llm_client.close()
    await redis_cache.close()
```

**Why lifespan?**
- Single source of truth for resource initialization
- Guaranteed cleanup on graceful shutdown
- Prevents resource leaks and orphaned connections
- Type-safe dependency injection

#### **B. Configuration Management** (`config/settings.py`)

Uses **Pydantic Settings** for environment-aware configuration:

```python
class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: Literal["ollama", "gemini"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    
    # Session Caching
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # 1 hour
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    
    # Environment-aware validation
    @model_validator(mode='after')
    def validate_security_settings(self):
        if self.ENV == "production" and not self.JWT_SECRET:
            raise ValueError("JWT_SECRET required in production")
```

**Benefits:**
- Type-safe configuration with validation
- Automatic `.env` file loading
- Environment-specific settings (dev vs production)
- No hardcoded secrets in code

#### **C. Asynchronous Database Repository** (`db/repository.py`)

Uses **aiosqlite** for non-blocking database operations:

```python
class DatabaseRepository:
    async def connect(self):
        self._connection = await aiosqlite.connect(self.db_path)
        
        # Enable Write-Ahead Logging for better concurrency
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA synchronous=NORMAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        
        await self._init_schema()
```

**Schema includes:**
- Users (email, hashed password, profile)
- Sessions (interviewer persona, difficulty, topic, metadata)
- Transcripts (message history per session)
- Performance Metrics (eye contact %, fidgeting score, speech rate)

**Why async SQLite?**
- Non-blocking I/O prevents thread pool saturation
- Better throughput for high-concurrency scenarios
- Integrates seamlessly with FastAPI's async ecosystem

#### **D. Redis Session Cache** (`core/cache.py`)

Provides **fast session state retrieval** with automatic expiration:

```python
class RedisCache:
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session from cache (TTL: 1 hour)"""
        if not self.enabled:
            return None
        
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    async def set_session(self, session_id: str, session_data: dict):
        """Cache session with automatic expiration"""
        await self.redis.setex(
            f"session:{session_id}",
            self.ttl,
            json.dumps(session_data)
        )
```

**Session data cached:**
- Current message history
- User preferences (persona, difficulty)
- Analysis metrics (eye contact, fidgeting scores)
- TTL: 1 hour (configurable)

**Why Redis?**
- Sub-millisecond latency for frequently accessed data
- Automatic key expiration (no manual cleanup)
- Persistence options for crash recovery
- Single source of truth during active sessions

#### **E. LLM Abstraction Layer** (`core/llm/`)

**Base Interface** (`base.py`):
```python
class LLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """Send messages and get completion"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verify LLM service is running"""
        pass
```

**Ollama Implementation** (`ollama.py`):
```python
class OllamaClient(LLMClient):
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            ),
            timeout=httpx.Timeout(settings.LLM_TIMEOUT)
        )
    
    async def chat(self, messages: list[dict], stream: bool = False):
        """Support both streaming and non-streaming modes"""
        if stream:
            return self._stream_chat(payload)  # AsyncIterator[str]
        else:
            return await self._complete_chat(payload)  # str
```

**Features:**
- **Connection pooling** (max 10 concurrent requests)
- **Streaming support** for real-time token delivery
- **Timeout handling** (default 5s, configurable)
- **Graceful error messages** for connection failures

#### **F. Circuit Breaker Pattern** (`core/llm/circuit_breaker.py`)

Prevents cascading failures when LLM is down:

```python
class CircuitBreaker:
    """
    States:
      CLOSED      → Normal operation
      OPEN        → Failing, reject requests
      HALF_OPEN   → Testing recovery
    """
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() > self.last_failure_time + self.recovery_timeout:
                # Try to recover
                self.state = CircuitState.HALF_OPEN
            else:
                # Still failing, return fallback
                return self.fallback_message
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise
```

**Benefits:**
- Automatic fallback when LLM unavailable
- Prevents repeated requests to failing service
- Auto-recovery after timeout period
- Graceful degradation for users

#### **G. Interview Engine** (`core/interview/engine.py`)

Main orchestration service for interview sessions:

```python
class InterviewEngine:
    async def start_session(
        self,
        session_id: str,
        persona: str,
        difficulty: str,
        topic: str,
        resume_context: Optional[str] = None
    ) -> str:
        """
        1. Sanitize inputs (prevent prompt injection)
        2. Build system prompt with persona + difficulty
        3. Inject resume context if provided
        4. Generate opening question
        5. Cache session in Redis
        """
        # Anti-prompt-injection measures
        resume_context = self._sanitize_prompt(resume_context)
        
        # Protect concurrent access
        async with self.sessions_lock:
            self.sessions[session_id] = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": opening_question}
            ]
        
        return opening_question
    
    async def answer_question(
        self,
        session_id: str,
        user_answer: str
    ) -> str:
        """
        1. Retrieve message history from session
        2. Append user's answer
        3. Request feedback from LLM
        4. Generate next question
        5. Update session history
        """
        async with self.sessions_lock:
            messages = self.sessions.get(session_id, [])
        
        # Add user response to history
        messages.append({"role": "user", "content": user_answer})
        
        # Get LLM feedback + next question
        response = await self.llm.chat(messages)
        
        # Update session
        messages.append({"role": "assistant", "content": response})
        async with self.sessions_lock:
            self.sessions[session_id] = messages
        
        return response
```

**Features:**
- **Thread-safe session management** with asyncio locks
- **Context window management** to prevent token overflow
- **Prompt injection prevention** with input sanitization
- **Session persistence** (memory + Redis + SQLite)

### **4. API Routes**

#### **Authentication Routes** (`api/routes/auth.py`)

```python
POST /auth/register
  Request:  { email, password, full_name }
  Response: { user_id, token, expires_in }
  
  Security: 
    - Password must be 8+ chars with uppercase, lowercase, digit, special char
    - Passwords hashed with bcrypt
    - Email validation with Pydantic EmailStr

POST /auth/login
  Request:  { email, password }
  Response: { token, token_type: "bearer", expires_in }

GET /auth/me
  Headers:  Authentication: Bearer <token>
  Response: { user_id, email, full_name }
```

#### **Session Management Routes** (`api/routes/sessions.py`)

```python
POST /api/start-interview
  Request:  {
    persona: "Dell" | "Deloitte" | "Google",
    difficulty: "beginner" | "intermediate" | "advanced",
    topic: "DSA" | "System Design" | "OOP",
    resume_text?: "PDF text...",
    custom_instructions?: "Focus on..."
  }
  Response: { session_id, opening_question }
  
  Flow:
    1. Validate user (JWT token)
    2. Generate session ID (UUID)
    3. Create DB record
    4. Initialize interview engine
    5. Return first question

POST /api/answer/{session_id}
  Request:  { user_answer: string }
  Response: { feedback, next_question, metrics }
  
  Flow:
    1. Retrieve session from Redis/SQLite
    2. Validate answer format
    3. Send to LLM with conversation history
    4. Calculate metrics (speech rate, confidence)
    5. Persist to database

GET /api/sessions
  Response: [ SessionSummary ]
  
  Returns:
    - All user's sessions with metadata
    - Total interviews count
    - Average performance score
    
GET /api/sessions/{session_id}
  Response: {
    session_id,
    persona,
    difficulty,
    duration,
    messages: [ transcript ],
    metrics: { eye_contact%, fidgeting_score, speech_rate_wpm }
  }

GET /api/config/options
  Response: {
    personas: ["Dell", "Google", "Deloitte", ...],
    difficulties: ["beginner", "intermediate", "advanced"],
    topics: ["DSA", "System Design", "Behavioral", ...]
  }
```

#### **WebSocket Route** (`api/routes/websocket.py`)

```python
WS /ws/{session_id}
  Connection Flow:
    1. Validate JWT token from query params
    2. Accept WebSocket connection
    3. Start listening for:
       - Video frames (base64 encoded)
       - Audio chunks (PCM bytes)
       - Text messages
    4. Process media in real-time
    5. Send back analytics every 100ms
  
  Outgoing Messages:
    {
      type: "vision_analysis" | "audio_metrics" | "interim_transcript",
      data: { eye_contact%, fidgeting_score, speech_rate_wpm, ... }
    }
```

---

## 🛠️ Setup Instructions

### **Prerequisites**
- **Python 3.11+** (async/await features)
- **Node.js 18+** (frontend)
- **Redis 7.0+** (optional but recommended for production)
- **Ollama** (for local LLM, or use Google Gemini API)
- **FFmpeg** (audio processing)
- **.env file** with API keys and configuration

### **Step 1: Clone & Create Virtual Environment**

```bash
# Clone repository
git clone <repo-url>
cd techsprint-gdg

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+
```

### **Step 2: Install Dependencies**

```bash
# Install Python packages
pip install -r requirements.txt

# Key packages that will be installed:
#  - fastapi (async web framework)
#  - uvicorn (ASGI server)
#  - pydantic-settings (configuration)
#  - aiosqlite (async database)
#  - redis[hiredis] (session cache)
#  - httpx (async HTTP client)
#  - PyJWT + passlib (authentication)
#  - google-cloud-speech/texttospeech (audio)
```

### **Step 3: Install System Dependencies**

#### **FFmpeg** (Required for audio processing)

**Windows:**
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract `ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build.7z`
3. Place `ffmpeg.exe` and `ffprobe.exe` in project root or add to PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

**Linux (Fedora):**
```bash
sudo dnf install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
ffprobe -version
```

#### **Ollama** (For local LLM, optional)

Download from: https://ollama.ai

After installation, pull a model:
```bash
ollama pull qwen3.5:4b  # ~2GB, recommended
# OR
ollama pull mistral  # ~4GB, more powerful
```

Start Ollama server:
```bash
ollama serve  # Runs on http://localhost:11434
```

### **Step 4: Create .env File**

Create `.env` in project root:

```env
# ===== Environment =====
ENV=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000

# ===== LLM Configuration =====
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
LLM_TIMEOUT=5.0
LLM_MAX_RETRIES=2

# ===== Redis (Optional) =====
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600

# ===== Database =====
DB_PATH=interview_data.db

# ===== Authentication =====
JWT_SECRET=your_secret_key_change_me_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ===== Google Cloud (Fallback, Optional) =====
GOOGLE_API_KEY=your_actual_api_key_here
```

**For Production .env:**
```env
ENV=production
DEBUG=false
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Generate secure JWT secret
JWT_SECRET=<output from: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Use production Redis
REDIS_URL=redis://:password@redis.prod.internal:6379

# Use Google Gemini API
LLM_PROVIDER=gemini
GOOGLE_API_KEY=<your-api-key>
```

---

## ▶️ Running the Application

### **Development Mode (with Hot Reload)**

```bash
# Terminal 1: Start FastAPI backend
python -m uvicorn backend.main:app --reload --port 8000

# Expected output:
# ✓ 🚀 Starting Interview Mirror Backend...
# ✓ ✅ Database connected: interview_data.db
# ✓ ✅ Redis connected: redis://localhost:6379
# ✓ ✅ LLM Connected: qwen3.5:4b @ http://localhost:11434
# ✓ ✅ Interview Engine initialized
# ✓ ✅ Backend startup complete
# 
# INFO:     Uvicorn running on http://0.0.0.0:8000

# Terminal 2: Start React frontend
cd frontend
npm install
npm run dev

# Expected output:
# VITE v5.0.0  ready in 245 ms
# ➜  Local:   http://localhost:3000
```

**Access the application:**
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

### **Production Mode (Docker)**

```bash
# Build Docker image
docker build -t interview-mirror:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e ENV=production \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e REDIS_URL=redis://redis:6379 \
  -v ./interview_data.db:/app/interview_data.db \
  --network interview-mirror \
  interview-mirror:latest
```

---

## 🔐 Environment Configuration

### **Development Settings**

```python
settings = Settings(
    ENV="development",
    DEBUG=True,
    LLM_PROVIDER="ollama",
    OLLAMA_BASE_URL="http://localhost:11434",
    REDIS_ENABLED=True,
    CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
)
```

**Features enabled:**
- Hot reload on file changes
- Detailed error messages in API responses
- CORS allows localhost origins
- Fallback to in-memory sessions if Redis unavailable

### **Production Settings**

```python
settings = Settings(
    ENV="production",
    DEBUG=False,
    CORS_ORIGINS="https://yourdomain.com",
    JWT_SECRET="<strong-random-key>",
    REDIS_ENABLED=True,
    REDIS_URL="redis://:password@prod-redis:6379"
)
```

**Security enforced:**
- CORS wildcard (`*`) not allowed
- JWT_SECRET randomized
- All errors sanitized (no stack traces to clients)
- Database encryption enabled
- HTTPS enforced for cookies

---

## 📚 API Documentation

### **Interactive API Docs**

Navigate to: `http://localhost:8000/docs`

This provides **Swagger UI** with:
- All endpoints with descriptions
- Request/response schemas
- "Try it out" functionality
- Authentication token input

### **Complete API Reference**

#### **Authentication**

```bash
# Register new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

Response:
{
  "user_id": "uuid-string",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 1440
}

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!"

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1440
}
```

#### **Session Management**

```bash
# Get available interview options
curl http://localhost:8000/api/config/options

Response:
{
  "personas": ["Dell", "Google", "Deloitte", "Amazon"],
  "difficulties": ["beginner", "intermediate", "advanced"],
  "topics": ["DSA", "System Design", "OOP", "Behavioral"]
}

# Start interview session
TOKEN="your_jwt_token"
curl -X POST http://localhost:8000/api/start-interview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "persona": "Google",
    "difficulty": "advanced",
    "topic": "System Design",
    "resume_text": "Years of experience building distributed systems..."
  }'

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "opening_question": "Tell me about a system you designed that handles high concurrency. What were the bottlenecks and how did you solve them?"
}

# Answer question in session
curl -X POST http://localhost:8000/api/answer/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_answer": "We built a real-time messaging system using Kafka for event streaming..."
  }'

Response:
{
  "feedback": "Strong answer! You clearly understand distributed systems. One suggestion: mention monitoring and alerting metrics.",
  "next_question": "How would you handle database failover in your architecture?",
  "metrics": {
    "answer_quality_score": 8.5,
    "technical_depth": "advanced",
    "communication_clarity": 8.0
  }
}

# Retrieve session transcript
curl http://localhost:8000/api/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "persona": "Google",
  "difficulty": "advanced",
  "duration": 1245,
  "messages": [
    {"role": "assistant", "content": "Tell me about..."},
    {"role": "user", "content": "We built..."},
    ...
  ],
  "metrics": {
    "eye_contact_percentage": 78,
    "fidgeting_score": 2.3,
    "speech_rate_wpm": 145,
    "overall_confidence_score": 7.8
  }
}

# List all user sessions
curl http://localhost:8000/api/sessions \
  -H "Authorization: Bearer $TOKEN"

Response:
[
  {
    "session_id": "...",
    "persona": "Google",
    "topic": "System Design",
    "created_at": "2026-03-24T10:30:00Z",
    "duration": 1245,
    "performance_score": 7.8
  },
  ...
]
```

---

## 👨‍💻 Development Guide

### **Project Structure Best Practices**

1. **Async-First Design**
   - All I/O operations must be `async`
   - Use `asyncio.Lock()` for shared state
   - Never use `time.sleep()` (use `asyncio.sleep()`)

2. **Type Safety**
   - All functions must have type hints
   - Use Pydantic models for request/response validation
   - Enable mypy in CI/CD

3. **Error Handling**
   - Custom exceptions inherit from `Exception`
   - HTTP exceptions with proper status codes
   - Log errors with context (user_id, session_id, etc.)

4. **Security**
   - Validate all user inputs (Pydantic)
   - Sanitize prompts for LLM (prevent injection)
   - Hash passwords with bcrypt
   - Use HTTPS in production
   - Include CSRF tokens for state-changing operations

### **Adding New Routes**

```python
# backend/api/routes/my_feature.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from engine.auth import AuthEngine, TokenData
from backend.db.repository import DatabaseRepository, get_db

router = APIRouter()
auth_engine = AuthEngine()

class MyRequest(BaseModel):
    field1: str
    field2: int

@router.post("/my-endpoint")
async def my_endpoint(
    req: MyRequest,
    current_user: TokenData = Depends(auth_engine.get_current_user),
    db: DatabaseRepository = Depends(get_db)
):
    """
    My endpoint description.
    
    Args:
        req: Request payload
        current_user: Authenticated user (auto-injected)
        db: Database repository (auto-injected)
    
    Returns:
        Response data
    """
    # Validation happens automatically with Pydantic
    
    # Access user info
    user_id = current_user.user_id
    
    # Database operations
    result = await db.query_something(user_id)
    
    return { "status": "success", "data": result }
```

Then register in `backend/main.py`:

```python
from backend.api.routes import my_feature

app.include_router(
    my_feature.router,
    prefix="/api",
    tags=["My Feature"]
)
```

### **Adding New Database Tables**

Edit `backend/db/repository.py`:

```python
async def _init_schema(self):
    """Initialize database schema"""
    await self._connection.executescript("""
    CREATE TABLE IF NOT EXISTS my_table (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_my_table_user 
    ON my_table(user_id, created_at DESC);
    """)
```

### **Testing**

```bash
# Run test suite
pytest tests/

# With coverage
pytest --cov=backend tests/

# Specific test file
pytest tests/test_interview_engine.py -v
```

**Test structure:**
```python
# tests/test_interview_engine.py
import pytest
from backend.core.interview.engine import InterviewEngine

@pytest.mark.asyncio
async def test_start_session():
    engine = InterviewEngine()
    
    result = await engine.start_session(
        session_id="test-123",
        persona="Google",
        difficulty="advanced",
        topic="System Design"
    )
    
    assert "system" in result.lower() or "design" in result.lower()

@pytest.mark.asyncio
async def test_answer_question():
    engine = InterviewEngine()
    
    await engine.start_session(...)
    response = await engine.answer_question(..., "My answer")
    
    assert len(response) > 0
```

---

## 🐛 Troubleshooting

### **"LLM Connection Failed"**

```
⚠️ LLM Connection Failed - Circuit breaker will handle fallback
```

**Solutions:**
1. Ensure Ollama is running: `ollama serve`
2. Check OLLAMA_BASE_URL in .env matches actual server
3. Verify model exists: `ollama list`
4. Check firewall/network: `curl http://localhost:11434/api/tags`
5. Fallback to Gemini: Set `LLM_PROVIDER=gemini` with `GOOGLE_API_KEY`

### **"Redis Connection Failed"**

```
⚠️ Redis connection failed
Falling back to database-only session storage
```

**Solutions:**
1. Check Redis is running: `redis-cli ping` (should return PONG)
2. Verify REDIS_URL in .env
3. For development, disable Redis: `REDIS_ENABLED=false`
4. In production, use managed Redis (AWS ElastiCache, etc.)

### **"Database Locked"**

```
sqlite3.OperationalError: database is locked
```

**Causes:** Multiple processes accessing database simultaneously

**Solutions:**
1. Enable WAL mode (already in code):
   ```sql
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;
   ```
2. Set proper connection pooling
3. Use single database instance

### **"CORS Error: No 'Access-Control-Allow-Origin' Header"**

**Solution:**
Update `CORS_ORIGINS` in .env to include frontend URL:
```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### **"Token Expired or Invalid"**

```
HTTPException: 401 Unauthorized - Invalid or expired token
```

**Solutions:**
1. Re-login to get fresh token
2. Check JWT_SECRET is consistent (don't change between restarts)
3. Verify token format: `Bearer <token>`
4. Check JWT_EXPIRE_MINUTES setting

### **"Speech Recognition Not Working"**

**Solutions:**
1. Check microphone permissions (browser may prompt)
2. Test audio: `curl http://localhost:8000/api/audio-test`
3. Ensure Google Cloud credentials: `GOOGLE_API_KEY` set
4. Check audio quality (reduce background noise)

### **Performance Issues**

**Optimize for high concurrency:**

1. **Database**: Enable WAL + connection pooling
   ```python
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;
   ```

2. **LLM**: Reduce timeout or batch requests
   ```env
   LLM_TIMEOUT=10.0
   LLM_MAX_RETRIES=1
   ```

3. **Redis**: Monitor memory with `redis-cli INFO stats`
   ```env
   REDIS_MAXMEMORY=1gb
   REDIS_MAXMEMORY_POLICY=allkeys-lru
   ```

4. **Uvicorn**: Increase worker processes
   ```bash
   uvicorn backend.main:app --workers 4 --port 8000
   ```

---

## 📊 Monitoring & Logging

### **View Logs**

```bash
# All backend logs with timestamps
tail -f backend.log

# Filter by level
grep "ERROR" backend.log
grep "WARNING" backend.log

# Real-time JSON logs (if centralized logging configured)
tail -f /var/log/interview-mirror/app.log | jq .
```

### **Health Check Endpoint**

```bash
curl http://localhost:8000/

Response:
{
  "status": "Online",
  "version": "4.0-Refactored",
  "llm_provider": "ollama",
  "llm_model": "qwen3.5:4b"
}
```

### **Redis Monitoring**

```bash
# Open Redis CLI
redis-cli

# Monitor connections
 > INFO stats

# View cached sessions
> KEYS session:*
> GET session:your-session-id
> TTL session:your-session-id  # Time to expiration
```

### **Database Monitoring**

```bash
# Open SQLite CLI
sqlite3 interview_data.db

# View schema
sqlite> .schema

# Count active sessions
sqlite> SELECT COUNT(*) FROM sessions WHERE status='active';

# User statistics
sqlite> SELECT COUNT(DISTINCT user_id) FROM sessions;
```

---

## 📝 Contributing

### **Code Style**

- Use **Black** for code formatting
  ```bash
  pip install black
  black backend/
  ```

- Use **isort** for import organization
  ```bash
  pip install isort
  isort backend/
  ```

- Use **mypy** for type checking
  ```bash
  pip install mypy
  mypy backend/
  ```

### **Commit Guidelines**

```
<type>: <subject>

<body>

<footer>

type: feat|fix|docs|style|refactor|test|chore
subject: 50 chars max, imperative mood
body: Explain what and why, not how
footer: Reference issues, breaking changes
```

**Examples:**
```
feat: add circuit breaker to LLM client

Implements fault tolerance pattern to gracefully handle
LLM service outages. Prevents cascading failures and
provides automatic recovery.

Closes #42
```

```
fix: prevent prompt injection in interview engine

Sanitize user inputs before sending to LLM to prevent
prompt injection attacks. Add regex validation layer.

Security: high
```

---

## 📄 License

This project is built for the Manipal University Jaipur Placement Cell.

---

## 🤝 Support

**For issues, questions, or suggestions:**
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Email: tech@muj-placement.edu
- Discord: [Join Community](https://discord.gg/your-server)
