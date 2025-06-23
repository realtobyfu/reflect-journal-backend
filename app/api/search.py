# app/api/search.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text
from typing import List, Optional
from datetime import datetime
from app import models, schemas, auth
from app.database import get_db

router = APIRouter()

@router.get("/entries/search", response_model=List[schemas.JournalEntry])
def search_entries(
    q: Optional[str] = Query(None, description="Search query"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    has_location: Optional[bool] = Query(None, description="Filter entries with location"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: str = Query("created_at", description="Sort field: created_at, word_count, mood_score"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Advanced search for journal entries with multiple filters
    """
    query = db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    )
    
    # Full-text search
    if q:
        # For PostgreSQL, we can use full-text search
        # For development with SQLite, we'll use LIKE
        search_filter = or_(
            models.JournalEntry.content.ilike(f"%{q}%"),
            models.JournalEntry.tags.cast(text).ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    # Mood filter
    if mood:
        query = query.filter(models.JournalEntry.mood == mood)
    
    # Date range filter
    if start_date:
        query = query.filter(models.JournalEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.JournalEntry.created_at <= end_date)
    
    # Location filter
    if has_location is not None:
        if has_location:
            query = query.filter(models.JournalEntry.location.isnot(None))
        else:
            query = query.filter(models.JournalEntry.location.is_(None))
    
    # Tags filter
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        for tag in tag_list:
            query = query.filter(models.JournalEntry.tags.cast(text).ilike(f"%{tag}%"))
    
    # Sorting
    sort_field = getattr(models.JournalEntry, sort_by, models.JournalEntry.created_at)
    if order == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Pagination
    entries = query.offset(skip).limit(limit).all()
    
    return entries

@router.get("/entries/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query for suggestions"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get search suggestions based on user's entries
    """
    # Get unique moods
    moods = db.query(models.JournalEntry.mood).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.mood.isnot(None),
        models.JournalEntry.mood.ilike(f"{q}%")
    ).distinct().limit(5).all()
    
    # Get location suggestions
    locations = db.query(
        func.json_extract(models.JournalEntry.location, '$.place_name').label('place')
    ).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.location.isnot(None),
        text("json_extract(location, '$.place_name') LIKE :q").params(q=f"{q}%")
    ).distinct().limit(5).all()
    
    # Get tag suggestions
    # Note: This is simplified. In production, you'd want to properly parse JSON arrays
    entries_with_tags = db.query(models.JournalEntry.tags).filter(
        models.JournalEntry.user_id == current_user.id,
        models.JournalEntry.tags.isnot(None)
    ).all()
    
    all_tags = set()
    for entry in entries_with_tags:
        if entry.tags:
            all_tags.update(entry.tags)
    
    matching_tags = [tag for tag in all_tags if tag.lower().startswith(q.lower())][:5]
    
    return {
        "moods": [mood[0] for mood in moods if mood[0]],
        "locations": [loc[0] for loc in locations if loc[0]],
        "tags": matching_tags
    }

@router.get("/entries/calendar")
def get_calendar_entries(
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get entries for calendar view with entry counts per day
    """
    # Get all entries for the specified month
    from calendar import monthrange
    from datetime import date
    
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    entries = db.query(
        func.date(models.JournalEntry.created_at).label('date'),
        func.count(models.JournalEntry.id).label('count'),
        func.group_concat(models.JournalEntry.mood).label('moods')
    ).filter(
        models.JournalEntry.user_id == current_user.id,
        func.date(models.JournalEntry.created_at) >= start_date,
        func.date(models.JournalEntry.created_at) <= end_date
    ).group_by(
        func.date(models.JournalEntry.created_at)
    ).all()
    
    # Format response
    calendar_data = {}
    for entry in entries:
        date_str = entry.date.strftime('%Y-%m-%d')
        moods = entry.moods.split(',') if entry.moods else []
        calendar_data[date_str] = {
            'count': entry.count,
            'moods': list(set(moods))  # Unique moods for the day
        }
    
    return {
        'year': year,
        'month': month,
        'entries': calendar_data
    }