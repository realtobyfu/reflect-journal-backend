from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app import models
from app.firebase import verify_firebase_token, firebase_initialized

settingscl= get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not firebase_initialized:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase authentication not configured"
        )
    
    try:
        # Verify Firebase ID token
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        if not firebase_uid or not email:
            raise credentials_exception
            
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        raise credentials_exception

    # Get or create user in local database
    user = db.query(models.User).filter(models.User.firebase_uid == firebase_uid).first()
    
    if not user:
        # Create user on first login
        username = email.split('@')[0]
        user = models.User(
            email=email,
            username=username,
            firebase_uid=firebase_uid,
            hashed_password='',  # Not used with Firebase auth
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user 