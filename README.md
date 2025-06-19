# Reflective Journal Backend

A FastAPI-based backend for a personal journaling application with mood tracking, photo attachments, and location features.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ (or Docker)
- Redis (or Docker)
- Git

## Quick Start with Docker (Recommended)

1. **Clone and navigate to the backend directory:**
```bash
git clone <repository-url>
cd backend
```

2. **Start services with Docker:**
```bash
docker compose up -d
```

3. **The API will be available at:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Local Development Setup

### 1. Install Dependencies

**macOS (using Homebrew):**
```bash
# Install PostgreSQL and Redis
brew install postgresql@16 redis

# Start services
brew services start postgresql@16
brew services start redis

# Add PostgreSQL to PATH (add to ~/.zshrc for persistence)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server
sudo systemctl start postgresql redis-server
sudo systemctl enable postgresql redis-server
```

### 2. Database Setup

```bash
# Create database
createdb journaldb

# Create postgres user with password (if needed)
psql journaldb -c "CREATE USER postgres WITH PASSWORD 'password' SUPERUSER;"

# Test connection
psql -U postgres -d journaldb -c "SELECT version();"
```

### 3. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Database connection
DATABASE_URL=postgresql://postgres:password@localhost:5432/journaldb

# Redis connection
REDIS_URL=redis://localhost:6379

# Application security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Firebase Admin (optional)
# firebase_service_account_path=app/keys/serviceAccountKey.json

# AWS S3 settings (optional)
# s3_bucket_name=
# aws_access_key_id=
# aws_secret_access_key=
# aws_region=us-east-1
```

### 5. Run the Application

```bash
# Make sure PostgreSQL is in PATH
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API route handlers
│   ├── services/           # Business logic
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database configuration
│   ├── config.py           # Application settings
│   ├── auth.py             # Authentication logic
│   └── main.py             # FastAPI application
├── docker-compose.yml      # Docker services
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore patterns
└── README.md              # This file
```

## Available Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /entries/` - Get journal entries
- `POST /entries/` - Create journal entry
- `PUT /entries/{id}` - Update journal entry
- `DELETE /entries/{id}` - Delete journal entry
- `GET /health` - Health check

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | No |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `10080` (7 days) | No |

## Troubleshooting

### Database Connection Issues

**Error: `role "postgres" does not exist`**
```bash
# Create the postgres user
psql journaldb -c "CREATE USER postgres WITH PASSWORD 'password' SUPERUSER;"
```

**Error: `could not translate host name "postgres"`**
- Make sure you're using `localhost` not `postgres` in DATABASE_URL for local development
- For Docker, use `postgres` as the hostname

### PostgreSQL Service Issues

**macOS:**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@16

# Add to PATH permanently
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
```

**Ubuntu/Debian:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Python Dependencies

**Install issues:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

### Environment Variables

**Case sensitivity issues:**
- Make sure environment variables in `.env` are UPPERCASE
- `DATABASE_URL`, not `database_url`
- `SECRET_KEY`, not `secret_key`

## Docker Development

The `docker-compose.yml` includes services for:
- PostgreSQL database
- Redis cache
- Backend application (when uncommented)

**Start only databases:**
```bash
docker compose up -d postgres redis
```

**View logs:**
```bash
docker compose logs -f postgres
```

**Stop services:**
```bash
docker compose down
```

## Production Deployment

1. **Set strong environment variables:**
   - Generate a secure `SECRET_KEY`
   - Use production database credentials
   - Configure CORS origins

2. **Database migrations:**
   - Implement Alembic for database migrations
   - Run migrations on deployment

3. **Security considerations:**
   - Use HTTPS
   - Configure proper CORS settings
   - Set up database connection pooling
   - Enable proper logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here] 