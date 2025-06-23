from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, nullable=True)  # Legacy field, keep for backwards compatibility
    mood_score = Column(Float, nullable=True)  # Legacy field
    emotions = Column(JSON, nullable=True)  # New multi-dimensional emotion system
    energy_level = Column(Integer, nullable=True)  # -50 to +50 range
    location = Column(JSON, nullable=True)  # {lat, lng, place_name}
    weather = Column(JSON, nullable=True)
    tags = Column(JSON, default=list)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="entries")
    attachments = relationship("Attachment", back_populates="entry", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    type = Column(String, nullable=False)  # 'photo', 'audio', etc.
    url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    entry = relationship("JournalEntry", back_populates="attachments")

class EmotionHistory(Base):
    __tablename__ = "emotion_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emotion_data = Column(JSON, nullable=False)  # Stores emotion entries for pattern analysis
    context = Column(JSON, nullable=True)  # Context information (location, time, etc)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")