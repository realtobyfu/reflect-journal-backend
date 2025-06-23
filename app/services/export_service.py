import csv
import io
from datetime import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from sqlalchemy.orm import Session
from app.models import JournalEntry, User

class ExportService:
    """Service for exporting journal entries to various formats"""
    
    def export_to_csv(self, entries: List[JournalEntry]) -> bytes:
        """Export entries to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Time', 'Mood', 'Word Count', 'Location', 
            'Tags', 'Content'
        ])
        
        # Write entry data
        for entry in entries:
            date = entry.created_at.strftime('%Y-%m-%d')
            time = entry.created_at.strftime('%H:%M')
            mood = entry.mood or ''
            word_count = entry.word_count
            location = entry.location.get('place_name', '') if entry.location else ''
            tags = ', '.join(entry.tags) if entry.tags else ''
            content = entry.content.replace('\n', ' ')  # Remove line breaks for CSV
            
            writer.writerow([
                date, time, mood, word_count, location, tags, content
            ])
        
        # Convert to bytes
        output.seek(0)
        return output.getvalue().encode('utf-8')
    
    def export_to_pdf(self, entries: List[JournalEntry], user: User) -> bytes:
        """Export entries to PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1e40af',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        entry_date_style = ParagraphStyle(
            'EntryDate',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#3730a3',
            spaceAfter=12
        )
        
        entry_content_style = ParagraphStyle(
            'EntryContent',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=20
        )
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=9,
            textColor='#6b7280',
            spaceAfter=6
        )
        
        # Add title
        story.append(Paragraph("My Reflective Journal", title_style))
        story.append(Spacer(1, 12))
        
        # Add export info
        export_date = datetime.now().strftime('%B %d, %Y')
        user_name = f"{user.first_name} {user.last_name}" if user.first_name else user.email
        story.append(Paragraph(f"Exported for: {user_name}", styles['Normal']))
        story.append(Paragraph(f"Export Date: {export_date}", styles['Normal']))
        story.append(Paragraph(f"Total Entries: {len(entries)}", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Add entries
        for i, entry in enumerate(entries):
            # Entry header
            date_str = entry.created_at.strftime('%A, %B %d, %Y at %I:%M %p')
            story.append(Paragraph(date_str, entry_date_style))
            
            # Entry metadata
            if entry.mood:
                story.append(Paragraph(f"Mood: {entry.mood}", metadata_style))
            if entry.location:
                location_name = entry.location.get('place_name', 'Unknown location')
                story.append(Paragraph(f"Location: {location_name}", metadata_style))
            if entry.tags:
                tags_str = ', '.join(entry.tags)
                story.append(Paragraph(f"Tags: {tags_str}", metadata_style))
            
            story.append(Paragraph(f"Words: {entry.word_count}", metadata_style))
            story.append(Spacer(1, 12))
            
            # Entry content
            # Clean and format content for PDF
            content = entry.content.replace('\n', '<br/>')
            story.append(Paragraph(content, entry_content_style))
            
            # Add page break between entries (except for the last one)
            if i < len(entries) - 1:
                story.append(Spacer(1, 20))
                story.append(Paragraph("—" * 50, styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_to_json(self, entries: List[JournalEntry]) -> dict:
        """Export entries to JSON format for backup"""
        return {
            "export_date": datetime.now().isoformat(),
            "version": "1.0",
            "entries": [
                {
                    "id": entry.id,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                    "content": entry.content,
                    "mood": entry.mood,
                    "mood_score": entry.mood_score,
                    "location": entry.location,
                    "tags": entry.tags,
                    "word_count": entry.word_count,
                    "attachments": [
                        {
                            "id": att.id,
                            "type": att.type,
                            "url": att.url,
                            "metadata": att.metadata_
                        }
                        for att in entry.attachments
                    ]
                }
                for entry in entries
            ]
        }

# Create singleton instance
export_service = ExportService()