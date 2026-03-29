"""
Authentication Routes

Handles user registration, login, and JWT token management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from engine.auth import AuthEngine, Token, TokenData
from backend.db.repository import get_db, DatabaseRepository
from backend.core.cache import redis_cache
from backend.config.settings import settings
import uuid
import re
import asyncio
import logging
import time
from collections import defaultdict, deque

router = APIRouter()
logger = logging.getLogger(__name__)

# Auth engine instance
auth_engine = AuthEngine()
_rate_lock = asyncio.Lock()
_local_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


async def _enforce_rate_limit(
    *,
    key: str,
    limit: int,
    window_sec: int,
    detail: str,
) -> None:
    now = time.time()

    # Prefer Redis if available so limits are shared across app instances.
    if redis_cache.enabled and redis_cache.redis is not None:
        try:
            count = await redis_cache.redis.incr(key)
            if count == 1:
                await redis_cache.redis.expire(key, window_sec)
            if int(count) > limit:
                raise HTTPException(status_code=429, detail=detail)
            return
        except HTTPException:
            raise
        except Exception:
            logger.warning("Redis rate limiter unavailable, falling back to local buckets")

    async with _rate_lock:
        bucket = _local_rate_buckets[key]
        cutoff = now - window_sec
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail=detail)
        bucket.append(now)


class UserRegister(BaseModel):
    email: EmailStr  # Pydantic email validation
    password: str
    full_name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Enforce password complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


@router.post("/register")
async def register(
    user: UserRegister,
    request: Request,
    db: DatabaseRepository = Depends(get_db),
):
    """Register a new user"""
    client_ip = request.client.host if request.client else "unknown"
    await _enforce_rate_limit(
        key=f"rate:register:{client_ip}",
        limit=settings.AUTH_REGISTER_RATE_LIMIT,
        window_sec=settings.AUTH_RATE_LIMIT_WINDOW_SEC,
        detail="Too many registration attempts. Please try again later.",
    )

    # Advisory check (still useful for fast-path rejection)
    existing_user = await db.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_pwd = auth_engine.get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    try:
        created = await db.create_user(user_id, user.email, hashed_pwd, user.full_name)
        if created:
            return {"message": "User created successfully", "user_id": user_id}
        # Repository returns False on duplicate email.
        raise HTTPException(status_code=409, detail="Email already registered")
    except HTTPException:
        raise
    except Exception:
        # Other unexpected database errors - log but don't expose details
        logger.exception("Database error during user registration")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseRepository = Depends(get_db)
):
    """
    Login endpoint using OAuth2 password flow.
    
    Username field expects email address.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_scope = form_data.username.strip().lower()
    await _enforce_rate_limit(
        key=f"rate:login:{client_ip}:{user_scope}",
        limit=settings.AUTH_LOGIN_RATE_LIMIT,
        window_sec=settings.AUTH_RATE_LIMIT_WINDOW_SEC,
        detail="Too many login attempts. Please try again later.",
    )

    user = await db.get_user_by_email(form_data.username)
    if not user or not auth_engine.verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_engine.create_access_token(
        data={"sub": user['id'], "email": user['email']}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(auth_engine.get_current_user)):
    """Get current authenticated user info"""
    return current_user
