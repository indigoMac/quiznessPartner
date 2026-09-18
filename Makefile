# QuizNess Partner - Development Makefile
# This provides a standardized interface for development tasks

.PHONY: help setup up down restart status logs test format lint clean
.DEFAULT_GOAL := help

# Colors for pretty output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Prefer the repo-root virtualenv over system Python.
VENV_BIN := $(abspath .venv/bin)
ifneq ($(wildcard $(VENV_BIN)/python),)
export PATH := $(VENV_BIN):$(PATH)
endif

##@ 🚀 Quick Start
help: ## Show this help message
	@echo "$(BLUE)QuizNess Partner - Development Commands$(RESET)"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)💡 Pro tip: You can also use the shell aliases (qup, qtest, etc.) if you have .envrc loaded$(RESET)"

setup: ## 🛠️  Run the setup script for new developers
	@echo "$(BLUE)Running development setup...$(RESET)"
	./setup-dev.sh

venv: ## 🐍 Create .venv and install backend dependencies
	@echo "$(BLUE)Creating virtualenv at .venv...$(RESET)"
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r backend/requirements-dev.txt
	@echo "$(GREEN)Activate with: source .venv/bin/activate$(RESET)"

##@ 🐳 Docker Services
up: ## ⬆️  Start all services
	@echo "$(BLUE)Starting all services...$(RESET)"
	docker-compose up -d

down: ## ⬇️  Stop all services
	@echo "$(BLUE)Stopping all services...$(RESET)"
	docker-compose down

restart: ## 🔄 Restart all services
	@echo "$(BLUE)Restarting all services...$(RESET)"
	docker-compose down && docker-compose up -d

status: ## 📊 Show service status and database counts
	@echo "$(BLUE)Service Status:$(RESET)"
	@docker-compose ps
	@echo "\n$(BLUE)Database Counts:$(RESET)"
	@docker-compose exec db psql -U postgres quizness -c 'SELECT (SELECT COUNT(*) FROM users) as users_count, (SELECT COUNT(*) FROM quizzes) as quizzes_count, (SELECT COUNT(*) FROM questions) as questions_count;' 2>/dev/null || echo "Database not ready yet"

logs: ## 📝 Follow all service logs
	docker-compose logs -f

logs-backend: ## 📝 Follow backend logs only
	docker-compose logs -f backend

logs-frontend: ## 📝 Follow frontend logs only
	docker-compose logs -f frontend

##@ 🧪 Testing
test: ## 🧪 Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	cd backend && python3 -m pytest tests/ --cov=. --cov-report=html --cov-report=xml

test-unit: ## ⚡ Run unit tests only (fast)
	@echo "$(BLUE)Running unit tests...$(RESET)"
	cd backend && python3 -m pytest tests/unit/ -v

test-integration: ## 🔗 Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	cd backend && python3 -m pytest tests/integration/ -v

test-performance: ## 🏃 Run performance tests
	@echo "$(BLUE)Running performance tests...$(RESET)"
	cd backend && python3 -m pytest tests/performance/ -v

test-e2e: ## 🎯 Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(RESET)"
	cd backend && python3 -m pytest tests/e2e/ -v

test-fast: ## ⚡ Run fast test suite (unit tests only)
	@echo "$(BLUE)Running fast test suite...$(RESET)"
	cd backend && python3 -m pytest tests/unit/ -v

test-coverage: ## 📊 Generate test coverage report
	@echo "$(BLUE)Generating coverage report...$(RESET)"
	cd backend && python3 -m pytest tests/ --cov=. --cov-report=html
	@echo "$(GREEN)Coverage report generated: backend/htmlcov/index.html$(RESET)"

load-test: ## 🚛 Run load tests
	@echo "$(BLUE)Running load tests...$(RESET)"
	cd backend && python3 -m pytest tests/performance/ -v

load-test-quick: ## ⚡ Quick 2-minute load test
	@echo "$(BLUE)Running quick load test...$(RESET)"
	cd backend && locust --headless -u 20 -r 4 -t 2m --host=http://localhost:8000

##@ 🎨 Code Quality
format: ## 🎨 Format code with Black and isort
	@echo "$(BLUE)Formatting code...$(RESET)"
	cd backend && black . && isort .
	@echo "$(GREEN)Code formatted!$(RESET)"

lint: ## 🔍 Run all linters
	@echo "$(BLUE)Running linters...$(RESET)"
	cd backend && flake8 . && black --check . && isort --check .
	@echo "$(GREEN)Linting complete!$(RESET)"

lint-fix: ## 🔧 Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(RESET)"
	$(MAKE) format

security: ## 🔒 Run security scan
	@echo "$(BLUE)Running security scan...$(RESET)"
	cd backend && bandit -r . -f json -o test-reports/security.json || true
	@echo "$(GREEN)Security scan complete!$(RESET)"

##@ 💾 Database
db: ## 🐘 Connect to main database
	docker-compose exec db psql -U postgres quizness

db-test: ## 🧪 Connect to test database
	docker-compose exec db psql -U postgres quizness_test

db-users: ## 👥 Show all users
	docker-compose exec db psql -U postgres quizness -c 'SELECT * FROM users;'

db-quizzes: ## 📝 Show all quizzes
	docker-compose exec db psql -U postgres quizness -c 'SELECT * FROM quizzes;'

db-reset: ## 🗑️  Reset development database (destructive!)
	@echo "$(RED)Warning: This will delete all data in the development database!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "\n$(BLUE)Resetting database...$(RESET)"; \
		docker-compose down; \
		docker volume rm quiznesspartner_postgres_data 2>/dev/null || true; \
		docker-compose up -d; \
		echo "$(GREEN)Database reset complete!$(RESET)"; \
	else \
		echo "\n$(YELLOW)Database reset cancelled$(RESET)"; \
	fi

##@ 🧹 Cleanup
clean: ## 🧹 Clean up Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(RESET)"
	docker-compose down
	docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(RESET)"

clean-all: ## 🗑️  Clean everything including volumes (destructive!)
	@echo "$(RED)Warning: This will delete all data!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "\n$(BLUE)Cleaning everything...$(RESET)"; \
		docker-compose down -v; \
		docker system prune -af; \
		echo "$(GREEN)Everything cleaned!$(RESET)"; \
	else \
		echo "\n$(YELLOW)Cleanup cancelled$(RESET)"; \
	fi

##@ 🚀 Development Workflow
dev: ## 🚀 Start development environment (up + status)
	@$(MAKE) up
	@sleep 5
	@$(MAKE) status
	@echo "\n$(GREEN)Development environment ready!$(RESET)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(RESET)"
	@echo "$(BLUE)Backend:  http://localhost:8000$(RESET)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(RESET)"

health: ## 🏥 Check health of all services
	@echo "$(BLUE)Checking service health...$(RESET)"
	@echo "Backend health:"
	@curl -s http://localhost:8000/health && echo " $(GREEN)✅ Backend healthy$(RESET)" || echo " $(RED)❌ Backend unhealthy$(RESET)"
	@echo "Frontend accessibility:"
	@curl -s http://localhost:3000 >/dev/null && echo "$(GREEN)✅ Frontend accessible$(RESET)" || echo "$(RED)❌ Frontend not accessible$(RESET)"

##@ 📚 Documentation
docs: ## 📚 Show key documentation files
	@echo "$(BLUE)📚 Documentation Files:$(RESET)"
	@echo "  $(GREEN)NEW_DEVELOPER_GUIDE.md$(RESET)     - Quick start for new developers"
	@echo "  $(GREEN)DEVELOPMENT_CHEAT_SHEET.md$(RESET) - Complete development reference"
	@echo "  $(GREEN)README.md$(RESET)                  - Project overview"
	@echo "  $(GREEN)Makefile$(RESET)                   - This file (run 'make help')"

##@ 🎯 Common Workflows
pre-commit: ## ✅ Run pre-commit checks (format + lint + test)
	@echo "$(BLUE)Running pre-commit checks...$(RESET)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test-unit
	@echo "$(GREEN)✅ All pre-commit checks passed!$(RESET)"

pre-push: ## 🚀 Run pre-push checks (all tests + coverage)
	@echo "$(BLUE)Running pre-push checks...$(RESET)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) test-coverage
	@echo "$(GREEN)✅ All pre-push checks passed!$(RESET)"

ci-local: ## 🔄 Run CI checks locally
	@echo "$(BLUE)Running CI checks locally...$(RESET)"
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) test-performance
	@echo "$(GREEN)✅ All CI checks passed!$(RESET)" 