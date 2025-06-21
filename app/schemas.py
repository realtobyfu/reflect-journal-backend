from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    first_name: str
    last_name: str
    password: str
    firebase_uid: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserUpdate(BaseModel):
    """Schema for updating user profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None

# Journal Entry schemas
class LocationData(BaseModel):
    lat: float
    lng: float
    place_name: str

class JournalEntryBase(BaseModel):
    content: str
    mood: Optional[str] = None
    location: Optional[LocationData] = None
    tags: List[str] = []

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None
    location: Optional[LocationData] = None
    tags: Optional[List[str]] = None

class AttachmentResponse(BaseModel):
    id: int
    type: str
    url: str
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class JournalEntry(JournalEntryBase):
    id: int
    user_id: int
    mood_score: Optional[float] = None
    weather: Optional[Dict[str, Any]] = None
    word_count: int
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True 