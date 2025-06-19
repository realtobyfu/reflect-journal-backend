from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app import models, schemas, auth
from app.database import get_db
from app.services.storage import storage_service

router = APIRouter()

@router.post("/", response_model=schemas.JournalEntry)
async def create_entry(
    entry: schemas.JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Calculate word count
    word_count = len(entry.content.split())
    
    # Create entry
    db_entry = models.JournalEntry(
        user_id=current_user.id,
        content=entry.content,
        mood=entry.mood,
        location=entry.location.model_dump() if entry.location else None,
        tags=entry.tags,
        word_count=word_count
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/", response_model=List[schemas.JournalEntry])
def get_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    mood: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.JournalEntry).filter(models.JournalEntry.user_id == current_user.id)
    
    if start_date:
        query = query.filter(models.JournalEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.JournalEntry.created_at <= end_date)
    if mood:
        query = query.filter(models.JournalEntry.mood == mood)
    
    entries = query.order_by(models.JournalEntry.created_at.desc()).offset(skip).limit(limit).all()
    return entries

@router.get("/{entry_id}", response_model=schemas.JournalEntry)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.put("/{entry_id}", response_model=schemas.JournalEntry)
def update_entry(
    entry_id: int,
    entry_update: schemas.JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    update_data = entry_update.model_dump(exclude_unset=True)
    if "content" in update_data:
        update_data["word_count"] = len(update_data["content"].split())
    if "location" in update_data and update_data["location"]:
        update_data["location"] = update_data["location"].model_dump()
    
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted successfully"}

@router.post("/{entry_id}/attachments", response_model=schemas.AttachmentResponse)
async def upload_attachment(
    entry_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify entry belongs to user
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Upload file
    file_url = await storage_service.upload_file(file, f"users/{current_user.id}/entries/{entry_id}")
    
    if not file_url:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Save attachment record
    attachment = models.Attachment(
        entry_id=entry_id,
        type="photo",
        url=file_url,
        metadata={
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size
        }
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment 