#!/bin/bash
set -e

# Initialize the database using SQLAlchemy
echo "Initializing database..."
python init_db.py

# Start the application
echo "Starting the application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload 