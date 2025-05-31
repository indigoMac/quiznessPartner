#!/bin/bash

# Database queries
alias qdb="docker compose exec db psql -U postgres quizness"
alias qdbtest="docker compose exec db psql -U postgres quizness_test"
alias qusers="docker compose exec db psql -U postgres quizness -c 'SELECT * FROM users;'"
alias qquizzes="docker compose exec db psql -U postgres quizness -c 'SELECT * FROM quizzes;'"
alias qquestions="docker compose exec db psql -U postgres quizness -c 'SELECT * FROM questions;'"

# Development commands
alias qup="docker compose up -d"        # Start all services
alias qdown="docker compose down"       # Stop all services
alias qrestart="docker compose down && docker compose up -d"  # Restart all services
alias qlogs="docker compose logs -f"    # Follow all logs
alias qbacklogs="docker compose logs -f backend"  # Follow backend logs
alias qfrontlogs="docker compose logs -f frontend" # Follow frontend logs

# Database queries
alias qcount="docker compose exec db psql -U postgres quizness -c 'SELECT 
  (SELECT COUNT(*) FROM users) as users_count,
  (SELECT COUNT(*) FROM quizzes) as quizzes_count,
  (SELECT COUNT(*) FROM questions) as questions_count;'"

# Testing
alias qtest="docker compose exec backend pytest"   # Run tests

# Useful development queries
alias qlatest="docker compose exec db psql -U postgres quizness -c 'SELECT id, title, created_at FROM quizzes ORDER BY created_at DESC LIMIT 5;'"

# Interactive console with expanded display
alias qconsole="docker compose exec db psql -U postgres -x quizness"

# Status check
alias qstatus="docker compose ps && echo '\nDatabase counts:' && qcount"

echo "QuizApp development aliases loaded! 🚀" 