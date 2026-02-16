"""
FastAPI Application Factory for Interview Mirror Backend

This is the new entrypoint using the refactored backend architecture.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.core.cache import redis_cache
from backend.core.llm.ollama import OllamaClient  
from backend.core.interview.engine import InterviewEngine

# Global instances (initialized in lifespan)
interview_engine: InterviewEngine = None
llm_client: OllamaClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup/shutdown tasks:
    - Initialize Redis connection
    - Initialize LLM client
    - Create InterviewEngine instance
    - Cleanup on shutdown
    """
    # === STARTUP ===
    print("🚀 Starting Interview Mirror Backend...")
    
    # 1. Connect to Redis
    await redis_cache.connect()
    
    # 2. Initialize LLM client
    global llm_client, interview_engine
    llm_client = OllamaClient()
    
    # 3. Health check LLM
    llm_healthy = await llm_client.health_check()
    if llm_healthy:
        print(f"✅ LLM Connected: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")
    else:
        print(f"⚠️ LLM Connection Failed - Circuit breaker will handle fallback")
    
    # 4. Create interview engine
    interview_engine = InterviewEngine()
    print("✅ Interview Engine initialized")
    
    print("✅ Backend startup complete\n")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    print("\n🔄 Shutting down...")
    
    # Cleanup connections
    await llm_client.close()
    await redis_cache.close()
    await interview_engine.close()
    
    print("✅ Shutdown complete")


def create_app() -> FastAPI:
    """Factory function to create FastAPI application"""
    
    app = FastAPI(
        title="Interview Mirror API",
        description="AI-Powered Interview Coach with Real-Time Analysis",
        version="4.0-Refactored",
        lifespan=lifespan
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/")
    async def root():
        return {
            "status": "Online",
            "version": "4.0-Refactored",
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else "gemini-flash"
        }
    
    # Import and include routers
    from backend.api.routes import websocket, auth, sessions
    
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
    app.include_router(websocket.router, tags=["WebSocket"])
    
    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)
