# Database Schema Migration Guide

This document explains how to properly update the database schema for the Reflective Journal backend application.

## Overview

The Reflective Journal backend uses SQLAlchemy ORM with PostgreSQL. When you modify the database models in `app/models.py`, you need to ensure the actual database schema is updated to match.

## Important Notes

⚠️ **SQLAlchemy's `Base.metadata.create_all()` only creates new tables - it does NOT modify existing tables or add missing columns.**

This is why you might encounter errors like:
```
psycopg2.errors.UndefinedColumn: column users.first_name does not exist
```

## Schema Update Process

### 1. Modify the Model

First, update your SQLAlchemy model in `app/models.py`:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)  # New column
    last_name = Column(String, nullable=True)   # New column
    # ... other columns
```

### 2. Check Current Database Schema

Before making changes, inspect the current table structure:

```bash
psql -U postgres -d journaldb -c "\d tablename"
```

Example:
```bash
psql -U postgres -d journaldb -c "\d users"
```

### 3. Apply Schema Changes

#### For Adding Columns

```bash
psql -U postgres -d journaldb -c "ALTER TABLE tablename ADD COLUMN IF NOT EXISTS column_name data_type;"
```

Example:
```bash
psql -U postgres -d journaldb -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR, ADD COLUMN IF NOT EXISTS last_name VARCHAR;"
```

#### For Modifying Columns

```bash
psql -U postgres -d journaldb -c "ALTER TABLE tablename ALTER COLUMN column_name TYPE new_data_type;"
```

#### For Dropping Columns

```bash
psql -U postgres -d journaldb -c "ALTER TABLE tablename DROP COLUMN IF EXISTS column_name;"
```

#### For Adding Constraints

```bash
psql -U postgres -d journaldb -c "ALTER TABLE tablename ADD CONSTRAINT constraint_name constraint_definition;"
```

### 4. Verify Changes

After applying changes, verify the schema matches your model:

```bash
psql -U postgres -d journaldb -c "\d tablename"
```

### 5. Update Pydantic Schemas

Don't forget to update the corresponding Pydantic schemas in `app/schemas.py`:

```python
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None  # Add new fields
    last_name: Optional[str] = None   # Add new fields
```

## Common Schema Changes

### Adding a New Table

1. Add the model to `app/models.py`
2. Restart the application - `Base.metadata.create_all()` will create new tables automatically
3. Add corresponding Pydantic schemas

### Adding Columns to Existing Table

1. Add columns to the model in `app/models.py`
2. Use `ALTER TABLE ADD COLUMN` to add columns to the database
3. Update Pydantic schemas
4. Restart the application

### Modifying Column Types

1. Update the model in `app/models.py`
2. Use `ALTER TABLE ALTER COLUMN` to modify the database
3. Update Pydantic schemas if needed
4. Restart the application

### Adding Relationships

1. Add foreign key columns to models
2. Use `ALTER TABLE ADD COLUMN` for foreign key columns
3. Add foreign key constraints if needed:
   ```bash
   psql -U postgres -d journaldb -c "ALTER TABLE child_table ADD CONSTRAINT fk_name FOREIGN KEY (parent_id) REFERENCES parent_table(id);"
   ```

## Best Practices

### 1. Always Use Transactions

For complex schema changes, wrap multiple operations in a transaction:

```bash
psql -U postgres -d journaldb -c "
BEGIN;
ALTER TABLE users ADD COLUMN first_name VARCHAR;
ALTER TABLE users ADD COLUMN last_name VARCHAR;
COMMIT;
"
```

### 2. Backup Before Major Changes

```bash
pg_dump -U postgres journaldb > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Test Schema Changes

1. Apply changes to a development database first
2. Test all API endpoints
3. Verify data integrity
4. Only then apply to production

### 4. Use IF NOT EXISTS/IF EXISTS

Always use conditional statements to make scripts idempotent:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR;
DROP TABLE IF EXISTS old_table;
```

### 5. Document Schema Changes

Keep a log of schema changes with timestamps and reasons:

```sql
-- 2024-01-15: Added user profile fields for enhanced user experience
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR;
```

## Troubleshooting

### Column Does Not Exist Error

```
psycopg2.errors.UndefinedColumn: column tablename.column_name does not exist
```

**Solution**: Add the missing column to the database table using `ALTER TABLE ADD COLUMN`.

### Table Does Not Exist Error

```
psycopg2.errors.UndefinedTable: relation "tablename" does not exist
```

**Solution**: The table wasn't created. Restart the application to trigger `Base.metadata.create_all()`.

### Foreign Key Constraint Error

```
psycopg2.errors.ForeignKeyViolation: insert or update on table violates foreign key constraint
```

**Solution**: Ensure referenced tables and data exist before adding foreign key constraints.

### Data Type Mismatch

```
psycopg2.errors.DatatypeMismatch: column "column_name" cannot be cast automatically
```

**Solution**: Use explicit type conversion or update data before changing column type.

## Migration Scripts

For complex changes, create migration scripts in `backend/migrations/`:

```python
# migrations/001_add_user_profile_fields.py
import psycopg2
from app.config import get_settings

def migrate():
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS first_name VARCHAR,
            ADD COLUMN IF NOT EXISTS last_name VARCHAR;
        """)
        conn.commit()
        print("✅ Migration completed successfully")
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
```

## Quick Reference

| Task | Command |
|------|---------|
| Check table structure | `psql -U postgres -d journaldb -c "\d tablename"` |
| Add column | `ALTER TABLE table ADD COLUMN IF NOT EXISTS col_name data_type;` |
| Drop column | `ALTER TABLE table DROP COLUMN IF EXISTS col_name;` |
| Modify column type | `ALTER TABLE table ALTER COLUMN col_name TYPE new_type;` |
| Add constraint | `ALTER TABLE table ADD CONSTRAINT name constraint_def;` |
| List all tables | `psql -U postgres -d journaldb -c "\dt"` |
| Backup database | `pg_dump -U postgres journaldb > backup.sql` |

## Environment Setup

Ensure you have the following environment variables set:

```bash
DATABASE_URL=postgresql://postgres:password@localhost/journaldb
```

And that PostgreSQL is running:

```bash
brew services start postgresql
```

Remember: Always test schema changes in development before applying to production! 