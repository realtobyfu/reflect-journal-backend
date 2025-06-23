# app/api/export.py

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json
import io
from app import models, auth
from app.database import get_db
from app.services.export_service import export_service

router = APIRouter()

@router.get("/export/csv")
def export_entries_csv(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Export journal entries to CSV format"""
    query = db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.JournalEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.JournalEntry.created_at <= end_date)
    
    entries = query.order_by(models.JournalEntry.created_at.desc()).all()
    
    # Generate CSV
    csv_data = export_service.export_to_csv(entries)
    
    # Create filename with timestamp
    filename = f"journal_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/pdf")
def export_entries_pdf(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Export journal entries to PDF format"""
    query = db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.JournalEntry.created_at >= start_date)
    if end_date:
        query = query.filter(models.JournalEntry.created_at <= end_date)
    
    entries = query.order_by(models.JournalEntry.created_at.asc()).all()
    
    # Generate PDF
    pdf_data = export_service.export_to_pdf(entries, current_user)
    
    # Create filename with timestamp
    filename = f"journal_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/json")
def export_entries_json(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Export all journal entries to JSON format for backup"""
    entries = db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    ).order_by(models.JournalEntry.created_at.asc()).all()
    
    # Generate JSON
    json_data = export_service.export_to_json(entries)
    
    # Create filename with timestamp
    filename = f"journal_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return StreamingResponse(
        io.BytesIO(json.dumps(json_data, indent=2).encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/import/json")
async def import_entries_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Import journal entries from JSON backup"""
    try:
        # Read and parse JSON
        content = await file.read()
        data = json.loads(content)
        
        if "entries" not in data:
            raise HTTPException(status_code=400, detail="Invalid backup format")
        
        imported_count = 0
        skipped_count = 0
        
        for entry_data in data["entries"]:
            # Check if entry already exists
            existing = db.query(models.JournalEntry).filter(
                models.JournalEntry.user_id == current_user.id,
                models.JournalEntry.created_at == datetime.fromisoformat(entry_data["created_at"])
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create new entry
            new_entry = models.JournalEntry(
                user_id=current_user.id,
                content=entry_data["content"],
                mood=entry_data.get("mood"),
                mood_score=entry_data.get("mood_score"),
                location=entry_data.get("location"),
                tags=entry_data.get("tags", []),
                word_count=entry_data.get("word_count", len(entry_data["content"].split())),
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                updated_at=datetime.fromisoformat(entry_data["updated_at"])
            )
            
            db.add(new_entry)
            imported_count += 1
        
        db.commit()
        
        return {
            "message": "Import completed",
            "imported": imported_count,
            "skipped": skipped_count
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))