from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app import models, schemas
from app.firebase import verify_firebase_token

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Verify Firebase ID token
    try:
        decoded = verify_firebase_token(token)
        uid = decoded.get('uid')
        email = decoded.get('email')
    except Exception:
        raise credentials_exception

    # Get or create local user
    user = db.query(models.User).filter(models.User.firebase_uid == uid).first()
    if not user:
        # First-time sign-in: create user record
        user = models.User(
            email=email,
            username=email.split('@')[0],
            hashed_password='',  # not used
            firebase_uid=uid,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user 