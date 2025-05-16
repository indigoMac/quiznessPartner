#!/bin/bash

# Go to the backend directory
cd "$(dirname "$0")"

# Set environment variables for testing
export OPENAI_API_KEY="test_key"
export ENVIRONMENT="test"
export DATABASE_URL="sqlite:///./test.db"

# Run the tests with pytest and coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml 