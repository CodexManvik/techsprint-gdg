"""
Authentication Routes

Handles user registration, login, and JWT token management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from engine.auth import AuthEngine, Token, TokenData
from backend.db.repository import get_db, DatabaseRepository
import uuid
import re
import aiosqlite

router = APIRouter()

# Auth engine instance
auth_engine = AuthEngine()


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
async def register(user: UserRegister, db: DatabaseRepository = Depends(get_db)):
    """Register a new user"""
    # Advisory check (still useful for fast-path rejection)
    existing_user = await db.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_pwd = auth_engine.get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    # Rely on DB unique constraint as source of truth
    try:
        created = await db.create_user(user_id, user.email, hashed_pwd, user.full_name)
        if created:
            return {"message": "User created successfully", "user_id": user_id}
        else:
            # Should not reach here if IntegrityError is raised properly
            raise HTTPException(status_code=500, detail="Failed to create user")
    except aiosqlite.IntegrityError:
        # Database constraint violation (duplicate email)
        raise HTTPException(status_code=409, detail="Email already registered")
    except Exception as e:
        # Other unexpected database errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseRepository = Depends(get_db)
):
    """
    Login endpoint using OAuth2 password flow.
    
    Username field expects email address.
    """
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
