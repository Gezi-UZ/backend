#!/bin/bash
set -e

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI server..."
# Use PORT provided by Railway or fallback to 8000
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
