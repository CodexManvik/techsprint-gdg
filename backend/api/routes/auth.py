"""
Authentication Routes

Handles user registration, login, and JWT token management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from engine.auth import AuthEngine, Token, TokenData
from database import Database
import uuid

router = APIRouter()

# Global instances (TODO: Move to dependency injection)
db = Database()
auth_engine = AuthEngine()


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


@router.post("/register")
async def register(user: UserRegister):
    """Register a new user"""
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth_engine.get_password_hash(user.password)
    user_id = str(uuid.uuid4())
    
    if db.create_user(user_id, user.email, hashed_pwd, user.full_name):
        return {"message": "User created successfully", "user_id": user_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint using OAuth2 password flow.
    
    Username field expects email address.
    """
    user = db.get_user_by_email(form_data.username)
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
