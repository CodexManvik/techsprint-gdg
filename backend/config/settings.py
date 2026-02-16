"""
Backend Configuration Management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application configuration with environment variable support"""
    
    # ===== LLM Configuration =====
    LLM_PROVIDER: Literal["ollama", "gemini"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3.5:latest"
    LLM_TIMEOUT: float = 5.0
    LLM_MAX_RETRIES: int = 2
    LLM_STREAM_ENABLED: bool = True
    
    # ===== Redis Configuration =====
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # 1 hour session TTL
    
    # ===== Database =====
    DB_PATH: str = "interview_data.db"
    
    # ===== Google Cloud (Fallback) =====
    GOOGLE_API_KEY: str | None = None
    
    # ===== Authentication =====
    JWT_SECRET: str = "your_jwt_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # ===== Application =====
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
