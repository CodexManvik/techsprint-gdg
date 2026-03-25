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
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_SCORING_MODEL: str | None = None
    LLM_TIMEOUT: float = 5.0
    LLM_MAX_RETRIES: int = 2
    LLM_STREAM_ENABLED: bool = True
    LLM_TEMPERATURE: float = 0.5
    LLM_TOP_P: float = 0.9
    LLM_MAX_NEW_TOKENS: int = 128
    LLM_JSON_MODE: bool = True
    MAX_CONTEXT_MESSAGES: int = 8
    INTERVIEW_TEMPERATURE: float = 1.0
    INTERVIEW_TOP_P: float = 0.95
    INTERVIEW_TOP_K: int = 20
    INTERVIEW_MIN_P: float = 0.0
    INTERVIEW_PRESENCE_PENALTY: float = 1.5
    INTERVIEW_REPETITION_PENALTY: float = 1.0
    INTERVIEW_MAX_NEW_TOKENS: int = 320
    INTERVIEW_CONTEXT_MESSAGES: int = 14
    SCORING_TEMPERATURE: float = 1.0
    SCORING_TOP_P: float = 0.95
    SCORING_TOP_K: int = 20
    SCORING_MIN_P: float = 0.0
    SCORING_PRESENCE_PENALTY: float = 1.5
    SCORING_REPETITION_PENALTY: float = 1.0
    SCORING_MAX_NEW_TOKENS: int = 220
    SCORING_CONTEXT_MESSAGES: int = 6
    MAX_EYE_CONTACT_REMINDERS: int = 3
    REMINDER_COOLDOWN_SEC: int = 90
    SCORING_QUEUE_MAXSIZE: int = 1000
    
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
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"  # Comma-separated list
    
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
        self.INTERVIEW_CONTEXT_MESSAGES = max(4, min(self.INTERVIEW_CONTEXT_MESSAGES, 40))
        self.SCORING_CONTEXT_MESSAGES = max(2, min(self.SCORING_CONTEXT_MESSAGES, 20))
        self.LLM_TEMPERATURE = max(0.0, min(self.LLM_TEMPERATURE, 2.0))
        self.LLM_TOP_P = max(0.0, min(self.LLM_TOP_P, 1.0))
        self.LLM_MAX_NEW_TOKENS = max(16, min(self.LLM_MAX_NEW_TOKENS, 1024))
        self.INTERVIEW_TEMPERATURE = max(0.0, min(self.INTERVIEW_TEMPERATURE, 2.0))
        self.INTERVIEW_TOP_P = max(0.0, min(self.INTERVIEW_TOP_P, 1.0))
        self.INTERVIEW_TOP_K = max(1, min(self.INTERVIEW_TOP_K, 200))
        self.INTERVIEW_MIN_P = max(0.0, min(self.INTERVIEW_MIN_P, 1.0))
        self.INTERVIEW_PRESENCE_PENALTY = max(0.0, min(self.INTERVIEW_PRESENCE_PENALTY, 2.0))
        self.INTERVIEW_REPETITION_PENALTY = max(0.5, min(self.INTERVIEW_REPETITION_PENALTY, 2.0))
        self.INTERVIEW_MAX_NEW_TOKENS = max(64, min(self.INTERVIEW_MAX_NEW_TOKENS, 2048))
        self.SCORING_TEMPERATURE = max(0.0, min(self.SCORING_TEMPERATURE, 2.0))
        self.SCORING_TOP_P = max(0.0, min(self.SCORING_TOP_P, 1.0))
        self.SCORING_TOP_K = max(1, min(self.SCORING_TOP_K, 200))
        self.SCORING_MIN_P = max(0.0, min(self.SCORING_MIN_P, 1.0))
        self.SCORING_PRESENCE_PENALTY = max(0.0, min(self.SCORING_PRESENCE_PENALTY, 2.0))
        self.SCORING_REPETITION_PENALTY = max(0.5, min(self.SCORING_REPETITION_PENALTY, 2.0))
        self.SCORING_MAX_NEW_TOKENS = max(64, min(self.SCORING_MAX_NEW_TOKENS, 1024))
        self.MAX_EYE_CONTACT_REMINDERS = max(1, min(self.MAX_EYE_CONTACT_REMINDERS, 10))
        self.REMINDER_COOLDOWN_SEC = max(15, min(self.REMINDER_COOLDOWN_SEC, 600))
        self.SCORING_QUEUE_MAXSIZE = max(10, min(self.SCORING_QUEUE_MAXSIZE, 10000))
        
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
