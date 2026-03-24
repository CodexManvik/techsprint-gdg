"""
Backend Configuration Management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator, Field
from typing import Literal
import secrets
import logging
import os

logger = logging.getLogger(__name__)

_jwt_secret_logged = False


class Settings(BaseSettings):
    """Application configuration with environment variable support"""
    
    # ===== LLM Configuration =====
    LLM_PROVIDER: Literal["ollama"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3.5:latest"
    LLM_TIMEOUT: float = 5.0
    LLM_MAX_RETRIES: int = 2
    LLM_STREAM_ENABLED: bool = True
    LLM_TEMPERATURE: float = 0.5
    LLM_TOP_P: float = 0.9
    LLM_MAX_NEW_TOKENS: int = 128
    LLM_JSON_MODE: bool = True
    MAX_CONTEXT_MESSAGES: int = 8
    
    # ===== Redis Configuration =====
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TTL: int = 3600  # 1 hour session TTL
    
    # ===== Database =====
    DB_PATH: str = "interview_data.db"
    
    # Deprecated compatibility key (ignored by runtime; kept to avoid .env validation failures)
    GOOGLE_API_KEY: str | None = None
    
    # ===== Authentication =====
    JWT_SECRET: str = ""  # Must be set in production, auto-generated in dev
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    WS_AUTH_REQUIRED: bool = True
    
    # ===== Application =====
    ENV: Literal["development", "production"] = "development"
    DEBUG: bool = Field(default=False)  # Secure default: False
    CORS_ORIGINS: str = "http://localhost:3000"  # Comma-separated list
    
    @model_validator(mode='after')
    def validate_security_settings(self):
        """Enforce security requirements for production"""
        global _jwt_secret_logged

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
                if not _jwt_secret_logged:
                    logger.warning("Auto-generated JWT_SECRET for %s environment", self.ENV)
                    _jwt_secret_logged = True
        
        # DEBUG follows ENV only if not explicitly set by user
        # Check if DEBUG was set from environment variable
        if 'DEBUG' not in os.environ:
            # User didn't set DEBUG, derive from ENV
            if self.ENV == "development":
                self.DEBUG = True
            else:
                self.DEBUG = False
        # else: preserve user's explicit DEBUG setting

        # Boundaries for generation and context settings
        self.MAX_CONTEXT_MESSAGES = max(2, min(self.MAX_CONTEXT_MESSAGES, 32))
        self.LLM_TEMPERATURE = max(0.0, min(self.LLM_TEMPERATURE, 2.0))
        self.LLM_TOP_P = max(0.0, min(self.LLM_TOP_P, 1.0))
        self.LLM_MAX_NEW_TOKENS = max(16, min(self.LLM_MAX_NEW_TOKENS, 1024))
        
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
