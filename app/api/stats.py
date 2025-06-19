from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app import models, auth
from app.database import get_db

router = APIRouter()

@router.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get total entries
    total_entries = db.query(func.count(models.JournalEntry.id)).filter(
        models.JournalEntry.user_id == current_user.id
    ).scalar()
    
    # Get this week's word count
    week_start = datetime.utcnow() - timedelta(days=7)
    week_word_count = db.query(func.sum(models.JournalEntry.word_count)).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.created_at >= week_start
    ).scalar() or 0
    
    # Get current streak
    entries = db.query(models.JournalEntry.created_at).filter(
        models.JournalEntry.user_id == current_user.id
    ).order_by(models.JournalEntry.created_at.desc()).all()
    
    streak = 0
    if entries:
        current_date = datetime.utcnow().date()
        for entry in entries:
            entry_date = entry[0].date()
            if (current_date - entry_date).days == streak:
                streak += 1
            else:
                break
    
    # Get mood distribution
    mood_counts = db.query(
        models.JournalEntry.mood,
        func.count(models.JournalEntry.id)
    ).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.mood.isnot(None)
    ).group_by(models.JournalEntry.mood).all()
    
    return {
        "total_entries": total_entries,
        "week_word_count": week_word_count,
        "current_streak": streak,
        "mood_distribution": dict(mood_counts) if mood_counts else {}
    } 