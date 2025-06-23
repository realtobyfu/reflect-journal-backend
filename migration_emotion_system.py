#!/usr/bin/env python3
"""
Database migration script for Phase 1 emotion system.
Adds emotions and energy_level columns to journal_entries table
and creates emotion_history table.
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    """Run the emotion system database migration."""
    
    try:
        with engine.connect() as connection:
            # Add new columns to journal_entries table
            connection.execute(text("""
                ALTER TABLE journal_entries 
                ADD COLUMN IF NOT EXISTS emotions JSONB,
                ADD COLUMN IF NOT EXISTS energy_level INTEGER
            """))
            
            # Create index for emotions column for better query performance
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_emotions 
                ON journal_entries USING GIN(emotions)
            """))
            
            # Create emotion_history table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS emotion_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    emotion_data JSONB NOT NULL,
                    context JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Create index for emotion_history
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_emotion_history_user_id 
                ON emotion_history(user_id)
            """))
            
            connection.commit()
            print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()