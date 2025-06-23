# app/api/analytics.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from app import models, auth
from app.database import get_db

router = APIRouter()

@router.get("/analytics/mood-trends")
def get_mood_trends(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get mood trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get daily mood scores
    daily_scores = db.query(
        func.date(models.JournalEntry.created_at).label('date'),
        func.avg(models.JournalEntry.mood_score).label('avg_score'),
        func.count(models.JournalEntry.id).label('entry_count')
    ).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.created_at >= start_date,
        models.JournalEntry.mood_score.isnot(None)
    ).group_by(
        func.date(models.JournalEntry.created_at)
    ).order_by('date').all()
    
    # Format for chart
    labels = []
    scores = []
    
    for score in daily_scores:
        labels.append(score.date.strftime('%b %d'))
        scores.append(round(score.avg_score, 2) if score.avg_score else 0)
    
    return {
        "labels": labels,
        "datasets": [{
            "label": "Mood Score",
            "data": scores,
            "borderColor": "rgb(59, 130, 246)",
            "backgroundColor": "rgba(59, 130, 246, 0.1)"
        }]
    }

@router.get("/analytics/writing-frequency")
def get_writing_frequency(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get writing frequency heatmap data"""
    # Get all entries for the user
    entries = db.query(
        models.JournalEntry.created_at
    ).filter(
        models.JournalEntry.user_id == current_user.id
    ).all()
    
    # Create heatmap data: hour -> day of week -> count
    heatmap_data = defaultdict(lambda: defaultdict(int))
    
    for entry in entries:
        hour = entry.created_at.hour
        day_of_week = entry.created_at.weekday()
        # Convert Monday=0 to Sunday=0 format
        day_of_week = (day_of_week + 1) % 7
        heatmap_data[hour][day_of_week] += 1
    
    # Convert to regular dict for JSON serialization
    return {
        str(hour): dict(days) for hour, days in heatmap_data.items()
    }

@router.get("/analytics/word-frequency")
def get_word_frequency(
    limit: int = Query(50, description="Number of top words to return"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get most frequently used words"""
    # Get all entries
    entries = db.query(models.JournalEntry.content).filter(
        models.JournalEntry.user_id == current_user.id
    ).all()
    
    # Common words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'is', 'am', 'are', 'was', 'were', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'i', 'me', 'my', 'we', 'us', 'our', 'you', 'your', 'he',
        'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
        'now', 'also', 'as', 'there', 'when', 'where', 'why', 'how', 'all',
        'both', 'each', 'if'
    }
    
    # Count word frequencies
    word_count = defaultdict(int)
    
    for entry in entries:
        words = entry.content.lower().split()
        for word in words:
            # Clean word of punctuation
            word = ''.join(c for c in word if c.isalnum())
            if word and len(word) > 3 and word not in stop_words:
                word_count[word] += 1
    
    # Get top words
    top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return {
        "words": [
            {"text": word, "size": count}
            for word, count in top_words
        ]
    }

@router.get("/analytics/entry-statistics")
def get_entry_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get comprehensive entry statistics"""
    # Basic stats
    total_entries = db.query(func.count(models.JournalEntry.id)).filter(
        models.JournalEntry.user_id == current_user.id
    ).scalar()
    
    total_words = db.query(func.sum(models.JournalEntry.word_count)).filter(
        models.JournalEntry.user_id == current_user.id
    ).scalar() or 0
    
    avg_words_per_entry = total_words / total_entries if total_entries > 0 else 0
    
    # Get entries by month
    monthly_entries = db.query(
        func.strftime('%Y-%m', models.JournalEntry.created_at).label('month'),
        func.count(models.JournalEntry.id).label('count')
    ).filter(
        models.JournalEntry.user_id == current_user.id
    ).group_by('month').order_by('month').all()
    
    # Longest entry
    longest_entry = db.query(
        models.JournalEntry.id,
        models.JournalEntry.word_count,
        models.JournalEntry.created_at
    ).filter(
        models.JournalEntry.user_id == current_user.id
    ).order_by(models.JournalEntry.word_count.desc()).first()
    
    # Most productive day
    entries_by_day = db.query(
        func.strftime('%w', models.JournalEntry.created_at).label('day'),
        func.count(models.JournalEntry.id).label('count')
    ).filter(
        models.JournalEntry.user_id == current_user.id
    ).group_by('day').all()
    
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    most_productive_day = None
    max_count = 0
    
    for day_data in entries_by_day:
        if day_data.count > max_count:
            max_count = day_data.count
            most_productive_day = day_names[int(day_data.day)]
    
    return {
        "total_entries": total_entries,
        "total_words": total_words,
        "average_words_per_entry": round(avg_words_per_entry, 1),
        "longest_entry": {
            "id": longest_entry.id,
            "word_count": longest_entry.word_count,
            "date": longest_entry.created_at.strftime('%Y-%m-%d')
        } if longest_entry else None,
        "most_productive_day": most_productive_day,
        "monthly_entries": [
            {"month": entry.month, "count": entry.count}
            for entry in monthly_entries
        ]
    }

@router.get("/analytics/mood-distribution")
def get_mood_distribution(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get distribution of moods"""
    mood_counts = db.query(
        models.JournalEntry.mood,
        func.count(models.JournalEntry.id).label('count')
    ).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.mood.isnot(None)
    ).group_by(models.JournalEntry.mood).all()
    
    total = sum(mood.count for mood in mood_counts)
    
    return {
        "moods": [
            {
                "mood": mood.mood,
                "count": mood.count,
                "percentage": round((mood.count / total) * 100, 1) if total > 0 else 0
            }
            for mood in mood_counts
        ],
        "total": total
    }