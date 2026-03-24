"""
FastAPI Application Factory for Interview Mirror Backend

This is the new entrypoint using the refactored backend architecture.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.core.cache import redis_cache
from backend.core.llm.ollama import OllamaClient
from backend.core.interview.engine import InterviewEngine
from backend.db.repository import init_db, close_db, get_db
from backend.core.telemetry.metrics import metrics


logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
interview_engine: InterviewEngine = None
llm_client: OllamaClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup/shutdown tasks:
    - Initialize async database connection
    - Initialize Redis connection
    - Initialize LLM client
    - Create InterviewEngine instance
    - Cleanup on shutdown
    """
    # === STARTUP ===
    logger.info("Starting Interview Mirror Backend")

    # Warn if legacy root app.py still exists.
    if Path("app.py").exists():
        logger.warning("Legacy entrypoint app.py detected. Use backend.main:app for production runtime")
    
    # 1. Initialize async database
    await init_db()
    
    # 2. Connect to Redis
    await redis_cache.connect()
    
    # 3. Initialize LLM client
    global llm_client, interview_engine
    llm_client = OllamaClient()
    
    # 4. Health check LLM
    llm_healthy = await llm_client.health_check()
    if llm_healthy:
        logger.info("LLM connected model=%s base_url=%s", settings.OLLAMA_MODEL, settings.OLLAMA_BASE_URL)
    else:
        logger.warning("LLM connection check failed - circuit breaker will handle fallback")
    
    # 5. Create interview engine
    interview_engine = InterviewEngine()
    logger.info("Interview Engine initialized")
    
    logger.info("Backend startup complete")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    logger.info("Shutting down backend")
    
    # Cleanup connections
    await close_db()
    if llm_client is not None:
        await llm_client.close()
    await redis_cache.close()
    if interview_engine is not None:
        await interview_engine.close()
    
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Factory function to create FastAPI application"""
    
    app = FastAPI(
        title="Interview Mirror API",
        description="AI-Powered Interview Coach with Real-Time Analysis",
        version="4.0-Refactored",
        lifespan=lifespan
    )
    
    # CORS Middleware - Restrict origins (no wildcard in production)
    cors_origins = [
        origin.strip() 
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()  # Filter out empty strings
    ]
    
    # Prevent wildcard in production
    if settings.ENV == "production" and "*" in cors_origins:
        raise ValueError("CORS wildcard '*' is not allowed in production. Set CORS_ORIGINS in .env")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
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
            "llm_model": settings.OLLAMA_MODEL,
        }

    @app.get("/health")
    async def health():
        db = await get_db()
        redis_connected = await redis_cache.is_connected()
        llm_healthy = await llm_client.health_check() if llm_client else False
        breaker_snapshot = (
            await interview_engine.circuit_breaker.snapshot()
            if interview_engine
            else {
                "state": "uninitialized",
                "failure_count": 0,
                "failure_threshold": 0,
                "recovery_timeout": 0,
                "last_failure_time": 0.0,
                "total_calls": 0,
                "total_failures": 0,
                "open_transitions": 0,
            }
        )

        await metrics.incr("health_checks")
        telemetry = await metrics.snapshot()

        return {
            "status": "ok",
            "app": {
                "env": settings.ENV,
                "version": "4.0-Refactored",
            },
            "db": {
                "connected": db.is_connected(),
            },
            "redis": {
                "enabled": redis_cache.enabled,
                "connected": redis_connected,
            },
            "llm": {
                "provider": settings.LLM_PROVIDER,
                "healthy": llm_healthy,
            },
            "circuit_breaker": breaker_snapshot,
            "telemetry": telemetry,
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
    # Use import string for reload support
    if settings.DEBUG:
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
