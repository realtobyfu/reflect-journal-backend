from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import JournalEntry, EmotionHistory, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/emotions", tags=["emotions"])

# Pydantic models for emotion system
class EmotionData(BaseModel):
    primary: dict = Field(..., description="Primary emotion with type and intensity")
    secondary: Optional[List[str]] = Field(None, description="Secondary emotions")
    energy: int = Field(..., ge=-50, le=50, description="Energy level from -50 to +50")
    context: Optional[dict] = Field(None, description="Context information")

class EmotionSuggestion(BaseModel):
    emotion: str
    intensity: int
    reason: str

class EmotionPattern(BaseModel):
    emotion: str
    frequency: int
    avg_intensity: float
    trend: str  # "increasing", "decreasing", "stable"

class EmotionHistoryResponse(BaseModel):
    patterns: List[EmotionPattern]
    recent_emotions: List[dict]
    insights: List[str]

@router.post("/entries/{entry_id}/emotions")
async def update_entry_emotions(
    entry_id: int,
    emotion_data: EmotionData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update emotions for a specific journal entry."""
    
    # Find the entry and verify ownership
    entry = db.query(JournalEntry).filter(
        and_(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Update entry with emotion data
    entry.emotions = emotion_data.dict()
    entry.energy_level = emotion_data.energy
    entry.updated_at = datetime.utcnow()
    
    # Store in emotion history for pattern analysis
    emotion_history = EmotionHistory(
        user_id=current_user.id,
        emotion_data=emotion_data.dict(),
        context={
            "entry_id": entry_id,
            "timestamp": datetime.utcnow().isoformat(),
            **(emotion_data.context or {})
        }
    )
    db.add(emotion_history)
    
    db.commit()
    db.refresh(entry)
    
    return {"message": "Emotions updated successfully", "entry_id": entry_id}

@router.get("/suggestions")
async def get_emotion_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[EmotionSuggestion]:
    """Get contextual emotion suggestions based on user history."""
    
    # Get recent emotion patterns (last 30 days)
    recent_emotions = db.query(EmotionHistory).filter(
        and_(
            EmotionHistory.user_id == current_user.id,
            EmotionHistory.created_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(desc(EmotionHistory.created_at)).limit(50).all()
    
    suggestions = []
    
    # Get current time context
    current_hour = datetime.now().hour
    
    # Time-based suggestions
    if 6 <= current_hour <= 10:
        suggestions.append(EmotionSuggestion(
            emotion="optimistic",
            intensity=70,
            reason="Morning hours are often associated with optimism"
        ))
    elif 17 <= current_hour <= 21:
        suggestions.append(EmotionSuggestion(
            emotion="reflective",
            intensity=60,
            reason="Evening is a natural time for reflection"
        ))
    
    # Pattern-based suggestions from recent history
    if recent_emotions:
        # Analyze common emotions from recent entries
        emotion_counts = {}
        for hist in recent_emotions:
            primary_emotion = hist.emotion_data.get("primary", {}).get("emotion")
            if primary_emotion:
                emotion_counts[primary_emotion] = emotion_counts.get(primary_emotion, 0) + 1
        
        # Suggest the most common emotion with moderate intensity
        if emotion_counts:
            most_common = max(emotion_counts, key=emotion_counts.get)
            suggestions.append(EmotionSuggestion(
                emotion=most_common,
                intensity=50,
                reason=f"You've been feeling {most_common} frequently lately"
            ))
    
    # Default suggestions if no history
    if not suggestions:
        suggestions = [
            EmotionSuggestion(emotion="content", intensity=60, reason="A good starting point"),
            EmotionSuggestion(emotion="curious", intensity=50, reason="Great for self-reflection"),
            EmotionSuggestion(emotion="grateful", intensity=70, reason="Positive emotional state")
        ]
    
    return suggestions[:3]  # Return top 3 suggestions

@router.get("/history")
async def get_emotion_history(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> EmotionHistoryResponse:
    """Get user's emotion history and patterns."""
    
    # Get emotion history for specified period
    start_date = datetime.utcnow() - timedelta(days=days)
    
    emotions = db.query(EmotionHistory).filter(
        and_(
            EmotionHistory.user_id == current_user.id,
            EmotionHistory.created_at >= start_date
        )
    ).order_by(desc(EmotionHistory.created_at)).all()
    
    if not emotions:
        return EmotionHistoryResponse(
            patterns=[],
            recent_emotions=[],
            insights=["Start tracking your emotions to see patterns and insights!"]
        )
    
    # Analyze patterns
    emotion_data = {}
    for emotion in emotions:
        primary = emotion.emotion_data.get("primary", {})
        emotion_type = primary.get("emotion")
        intensity = primary.get("intensity", 0)
        
        if emotion_type:
            if emotion_type not in emotion_data:
                emotion_data[emotion_type] = {"intensities": [], "count": 0}
            emotion_data[emotion_type]["intensities"].append(intensity)
            emotion_data[emotion_type]["count"] += 1
    
    # Create patterns
    patterns = []
    for emotion_type, data in emotion_data.items():
        avg_intensity = sum(data["intensities"]) / len(data["intensities"])
        patterns.append(EmotionPattern(
            emotion=emotion_type,
            frequency=data["count"],
            avg_intensity=round(avg_intensity, 1),
            trend="stable"  # TODO: Calculate actual trend
        ))
    
    # Sort by frequency
    patterns.sort(key=lambda x: x.frequency, reverse=True)
    
    # Recent emotions (last 7 days)
    recent = [e.emotion_data for e in emotions[:7]]
    
    # Generate insights
    insights = []
    if patterns:
        top_emotion = patterns[0]
        insights.append(f"Your most frequent emotion lately is '{top_emotion.emotion}' with an average intensity of {top_emotion.avg_intensity}")
        
        if len(patterns) > 1:
            insights.append(f"You've experienced {len(patterns)} different emotions in the last {days} days")
    
    return EmotionHistoryResponse(
        patterns=patterns,
        recent_emotions=recent,
        insights=insights
    )