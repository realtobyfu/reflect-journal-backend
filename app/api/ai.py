# app/api/ai.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app import models, auth
from app.database import get_db
from app.services.ai_service import ai_service

router = APIRouter()

@router.get("/prompts/daily", response_model=List[Dict])
def get_daily_prompts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get personalized daily journal prompts"""
    prompts = ai_service.generate_daily_prompts(current_user, db)
    return prompts

@router.post("/entries/{entry_id}/analyze")
def analyze_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Analyze sentiment and emotions of a journal entry"""
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Perform sentiment analysis
    analysis = ai_service.analyze_sentiment(entry.content)
    
    # Update entry with sentiment score
    entry.mood_score = analysis["sentiment_score"]
    db.commit()
    
    return {
        "entry_id": entry_id,
        "analysis": analysis
    }

@router.post("/entries/{entry_id}/reflect")
def get_reflection(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get AI reflection response for an entry"""
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    reflection = ai_service.generate_reflection_response(entry)
    
    return {
        "entry_id": entry_id,
        "reflection": reflection
    }

@router.get("/insights")
def get_writing_insights(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get comprehensive insights about user's writing patterns"""
    insights = ai_service.get_writing_insights(current_user.id, db)
    return insights

@router.get("/themes")
def get_themes(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Extract themes from recent entries"""
    entries = db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    ).order_by(models.JournalEntry.created_at.desc()).limit(limit).all()
    
    if not entries:
        return {"themes": [], "message": "No entries found"}
    
    themes = ai_service.extract_themes(entries)
    
    return {
        "themes": themes,
        "entries_analyzed": len(entries)
    }