#!/bin/bash

# Development script for Reflective Journal Backend
# This script sets up the environment and starts the development server

set -e

echo "🚀 Starting Reflective Journal Backend Development Server"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated. Please run:"
    echo "   source venv/bin/activate"
    exit 1
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "❌ .env file not found. Please create one based on .env.example"
    exit 1
fi

# Add PostgreSQL to PATH (for macOS with Homebrew)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ -d "/opt/homebrew/opt/postgresql@16/bin" ]]; then
        export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
        echo "✅ Added PostgreSQL to PATH"
    fi
fi

# Check PostgreSQL connection
echo "🔍 Checking PostgreSQL connection..."
if command -v psql >/dev/null 2>&1; then
    if psql -U postgres -d journaldb -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ PostgreSQL connection successful"
    else
        echo "❌ Cannot connect to PostgreSQL. Make sure it's running and the database exists."
        echo "   Run: createdb journaldb"
        exit 1
    fi
else
    echo "❌ psql command not found. Make sure PostgreSQL is installed."
    exit 1
fi

# Check Redis connection
echo "🔍 Checking Redis connection..."
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis connection successful"
    else
        echo "❌ Cannot connect to Redis. Make sure it's running."
        echo "   Run: brew services start redis"
        exit 1
    fi
else
    echo "❌ redis-cli command not found. Make sure Redis is installed."
    exit 1
fi

echo "🎯 Starting FastAPI development server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔗 API Endpoint: http://localhost:8000"
echo ""

# Start the development server
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 