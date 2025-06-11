.PHONY: help install test test-unit test-integration test-e2e test-performance test-load test-all test-fast clean lint format type-check security

# Default target
help:
	@echo "QuizNess Backend Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install           Install all dependencies"
	@echo "  install-dev       Install development dependencies"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test-unit         Run unit tests"
	@echo "  test-integration  Run integration tests"
	@echo "  test-e2e          Run end-to-end tests"
	@echo "  test-performance  Run performance tests"
	@echo "  test-load         Run load tests (server must be running)"
	@echo "  test-all          Run complete test suite"
	@echo "  test-fast         Run fast test suite (unit tests only)"
	@echo "  test              Alias for test-unit"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint              Run linting checks"
	@echo "  format            Format code with black and isort"
	@echo "  type-check        Run type checking with mypy"
	@echo "  security          Run security checks with bandit"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean             Clean up test artifacts and cache"
	@echo "  coverage          Open coverage report in browser"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev               Start development server"
	@echo "  dev-db            Start development database"
	@echo "  migrate           Run database migrations"

# Installation
install:
	python3 -m pip install -r requirements.txt

install-dev:
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt || python3 -m pip install \
		pytest pytest-asyncio pytest-cov pytest-html pytest-json-report \
		pytest-benchmark black isort mypy bandit locust factory-boy faker \
		flake8 pre-commit

# Testing commands
test-unit:
	@echo "Running unit tests..."
	python3 -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	python3 -m pytest tests/integration/ -v

test-e2e:
	@echo "Running end-to-end tests..."
	python3 -m pytest tests/e2e/ -v

test-performance:
	@echo "Running performance tests..."
	python3 -m pytest tests/performance/ -v

test-load:
	@echo "Running load tests..."
	python3 -m pytest tests/performance/ -v

test-all:
	@echo "Running complete test suite..."
	python3 -m pytest tests/ --cov=. --cov-report=html --cov-report=xml

test-fast:
	@echo "Running fast test suite..."
	python3 -m pytest tests/unit/ -v

# Alias for most common test command
test: test-unit

# Code quality
lint:
	@echo "Running linting checks..."
	python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "Formatting code..."
	python3 -m black .
	python3 -m isort .

type-check:
	@echo "Running type checks..."
	python3 -m mypy . --ignore-missing-imports

security:
	@echo "Running security checks..."
	mkdir -p test-reports
	python3 -m bandit -r . -f json -o test-reports/security.json || true
	python3 -m bandit -r . -f txt

# Development
dev:
	@echo "Starting development server..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-db:
	@echo "Starting development database..."
	docker-compose up -d db

migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# Maintenance
clean:
	@echo "Cleaning up test artifacts..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf test-reports
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

coverage:
	@echo "Opening coverage report..."
	@if [ -f htmlcov/index.html ]; then \
		if command -v open >/dev/null 2>&1; then \
			open htmlcov/index.html; \
		elif command -v xdg-open >/dev/null 2>&1; then \
			xdg-open htmlcov/index.html; \
		else \
			echo "Coverage report available at: htmlcov/index.html"; \
		fi; \
	else \
		echo "No coverage report found. Run tests first."; \
	fi

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t quizness-backend .

docker-test:
	@echo "Running tests in Docker..."
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-dev:
	@echo "Starting development environment..."
	docker-compose up --build

# Database commands
db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	alembic upgrade head

db-backup:
	@echo "Creating database backup..."
	docker exec $$(docker-compose ps -q db) pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backup.sql

db-restore:
	@echo "Restoring database from backup..."
	docker exec -i $$(docker-compose ps -q db) psql -U $$POSTGRES_USER $$POSTGRES_DB < backup.sql

# CI/CD commands
ci-test:
	@echo "Running CI test suite..."
	python3 -m pytest tests/ --cov=. --cov-report=html --cov-report=xml

ci-quality:
	@echo "Running CI quality checks..."
	make lint
	make type-check
	make security

# Documentation
docs:
	@echo "Starting documentation server..."
	mkdocs serve

docs-build:
	@echo "Building documentation..."
	mkdocs build

# Utilities
check-deps:
	@echo "Checking for outdated dependencies..."
	python3 -m pip list --outdated

update-deps:
	@echo "Updating dependencies..."
	python3 -m pip freeze > requirements.txt

# Project info
info:
	@echo "QuizNess Backend Project Information"
	@echo "====================================="
	@echo "Python Version: $$(python3 --version)"
	@echo "Pip Version: $$(python3 -m pip --version)"
	@echo "Project Directory: $$(pwd)"
	@echo "Virtual Environment: $${VIRTUAL_ENV:-None}"
	@echo ""
	@echo "Test Structure:"
	@echo "  tests/unit/         - Unit tests"
	@echo "  tests/integration/  - Integration tests"
	@echo "  tests/e2e/          - End-to-end tests"
	@echo "  tests/performance/  - Performance tests"
	@echo "  tests/fixtures/     - Test fixtures and factories"
	@echo ""
	@echo "Reports Directory: test-reports/"
	@echo "Coverage Directory: htmlcov/" 