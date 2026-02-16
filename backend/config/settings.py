"""
Backend Configuration Management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator, Field
from typing import Literal
import secrets
import logging

logger = logging.getLogger(__name__)


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
    JWT_SECRET: str = ""  # Must be set in production, auto-generated in dev
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # ===== Application =====
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = Field(default=False)  # Secure default: False
    CORS_ORIGINS: str = "http://localhost:3000"  # Comma-separated list
    
    @model_validator(mode='after')
    def validate_security_settings(self):
        """Enforce security requirements for production"""
        # JWT_SECRET enforcement
        if self.ENV == "production":
            if not self.JWT_SECRET or self.JWT_SECRET == "your_jwt_secret_change_me":
                raise ValueError(
                    "JWT_SECRET must be explicitly set in production environment. "
                    "Set it in your .env file with a strong random value."
                )
        else:
            # Auto-generate for development
            if not self.JWT_SECRET or self.JWT_SECRET == "your_jwt_secret_change_me":
                self.JWT_SECRET = secrets.token_urlsafe(32)
                logger.warning(f"Auto-generated JWT_SECRET for {self.ENV} environment")
        
        # DEBUG follows ENV
        if self.ENV == "development":
            self.DEBUG = True
        else:
            self.DEBUG = False
        
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
