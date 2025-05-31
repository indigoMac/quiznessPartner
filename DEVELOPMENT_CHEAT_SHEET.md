# 🚀 QuizNess Partner - Development Cheat Sheet

_A complete guide for new developers to get up and running quickly_

## 📋 Prerequisites

Before you start, make sure you have:

- **Docker & Docker Compose** (Essential for containerized development)
- **Git** (For version control)
- **direnv** (Optional but recommended - `brew install direnv` on macOS)
- **OpenAI API Key** (Required for AI quiz generation)

## 🏁 Quick Start (0 to Running in 5 minutes)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/mackenziecox/quiznessPartner.git
cd quiznessPartner

# Load development environment (if you have direnv)
direnv allow
# OR manually source the environment
source .envrc
```

### 2. Environment Configuration

```bash
# Create backend environment file
cp backend/.env.example backend/.env

# Create frontend environment file
cp frontend/.env.example frontend/.env

# Edit backend/.env and add your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" >> backend/.env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> backend/.env
```

### 3. Start Everything

```bash
# Start all services (database, backend, frontend)
qup

# Check if everything is running
qstatus

# View logs (optional)
qlogs
```

### 4. Verify Setup

```bash
# Test the backend health endpoint
curl http://localhost:8000/health

# Check if frontend is accessible
open http://localhost:3000

# Run a quick test
qtest
```

**🎉 You're ready to develop!**

---

## 🛠️ Daily Development Workflow

### Starting Your Day

```bash
# 1. Pull latest changes
git pull origin main

# 2. Start development environment
qdev

# 3. Check status
qstatus
```

### Making Changes

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your code changes...

# 3. Test your changes
qtest                    # Run all tests
qtestunit               # Run just unit tests (faster)

# 4. Format your code
qformat                 # Auto-format with Black & isort

# 5. Check code quality
qlint                   # Run linters
```

### Committing Changes

```bash
# 1. Add your changes
git add .

# 2. Commit (pre-commit hooks will run automatically)
git commit -m "feat: your feature description"

# 3. Push to GitHub
git push origin feature/your-feature-name

# 4. Create Pull Request on GitHub
```

---

## 🧪 Testing Guide

### Quick Testing Commands

```bash
# Basic testing
qtest                    # All tests (excluding slow performance tests)
qtestunit               # Unit tests only (fastest)
qtestint                # Integration tests
qtestapi                # API endpoint tests
qtestauth               # Authentication tests

# Comprehensive testing
qtestfull               # ALL tests including performance tests
qtestfast               # Run tests in parallel (faster)

# Load testing
qload                   # Interactive load test with web UI
qloadfast               # Quick 2-minute load test
qloadheavy              # Heavy 5-minute stress test

# Coverage reports
qcoverage               # Generate and open coverage report
```

### Test Types Explained

- **Unit Tests**: Fast, isolated function testing
- **Integration Tests**: End-to-end API workflow testing
- **Performance Tests**: Load and response time validation
- **Security Tests**: Vulnerability scanning (runs in CI)

### Testing Best Practices

```bash
# Always test before committing
git add . && qtest && git commit -m "your message"

# Test specific changes
qtestunit               # For quick feedback during development
qtestint                # Before pushing to verify API changes work

# Performance testing
qloadfast               # Before major releases
```

---

## 🔧 Database Management

### Quick Database Commands

```bash
# Connect to databases
qdb                     # Connect to main development database
qdbtest                 # Connect to test database

# View data
qusers                  # Show all users
qquizzes                # Show all quizzes
qquestions              # Show all questions
qcount                  # Show record counts
qlatest                 # Show 5 most recent quizzes

# Interactive console
qconsole                # PostgreSQL console with expanded display
```

### Database Queries Examples

```bash
# Check recent activity
qlatest

# Count all records
qcount

# Custom queries in database console
qdb
# Then run SQL: SELECT * FROM users WHERE created_at > NOW() - INTERVAL '1 day';
```

---

## 📊 Monitoring & Debugging

### Service Management

```bash
# Check status
qstatus                 # Show all service status + database counts

# Logs
qlogs                   # Follow all logs
qbacklogs               # Follow backend logs only
qfrontlogs              # Follow frontend logs only

# Restart services
qrestart                # Restart all services
qdown && qup            # Full restart
```

### Common Debugging

```bash
# Backend not starting?
qbacklogs               # Check backend logs for errors

# Database connection issues?
qdb                     # Try connecting directly
qcount                  # Check if database has data

# Frontend not loading?
qfrontlogs              # Check frontend logs
curl http://localhost:8000/health  # Verify backend is healthy

# Test failures?
qtestunit -v            # Verbose test output
qcoverage               # Check test coverage
```

---

## 🚀 GitHub Workflow & CI/CD

### Branch Strategy

```bash
# Main branches
main                    # Production-ready code
develop                 # Integration branch (if using)

# Feature branches
feature/quiz-generation
feature/user-auth
bugfix/login-issue
hotfix/critical-bug
```

### Pull Request Process

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature
   ```

2. **Develop & Test Locally**

   ```bash
   # Make changes...
   qtest                # Ensure tests pass
   qformat              # Format code
   qlint                # Check quality
   ```

3. **Push & Create PR**

   ```bash
   git push origin feature/your-feature
   # Create PR on GitHub
   ```

4. **CI/CD Pipeline Runs Automatically**

   - ✅ **Code Quality**: Linting, formatting, type checking
   - ✅ **Security Scans**: Bandit, Safety, vulnerability checks
   - ✅ **Unit Tests**: Python 3.9, 3.10, 3.11 + Frontend tests
   - ✅ **Integration Tests**: Full API workflow testing
   - ✅ **Performance Tests**: Load testing (on main branch only)
   - ✅ **Coverage**: Codecov integration

5. **Review & Merge**
   - All checks must pass ✅
   - Code review approval required
   - Merge to main triggers deployment

### CI/CD Pipeline Details

The pipeline automatically runs when you:

- Push to `main` or `develop` branches
- Create/update Pull Requests

**What gets tested:**

- Backend tests on Python 3.9, 3.10, 3.11
- Frontend tests with Node.js 18
- Security scanning with Bandit & Safety
- Performance tests (main branch only)
- Code coverage with 80% minimum target

---

## 🌍 Deployment Setup

### Environments

- **Development**: Your local Docker environment
- **Staging**: Pre-production testing (auto-deployed from develop)
- **Production**: Live environment (auto-deployed from main)

### Production Deployment

```bash
# Production uses different Docker compose file
docker-compose -f docker-compose.prod.yml up -d

# Production images are built automatically in CI/CD
# and pushed to GitHub Container Registry
```

### Environment Variables for Production

Required production environment variables:

```bash
# Backend (.env)
OPENAI_API_KEY=your_production_key
SECRET_KEY=secure_random_key_64_chars
DATABASE_URI=postgresql://user:pass@prod-db:5432/quizness
ENVIRONMENT=production

# Frontend
VITE_API_URL=https://your-production-api.com
```

### Deployment Checklist

- [ ] All tests passing in CI ✅
- [ ] Code coverage above 80% ✅
- [ ] Security scans clean ✅
- [ ] Performance tests passing ✅
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Monitoring setup
- [ ] Backup strategy in place

---

## 🆘 Troubleshooting Guide

### Common Issues & Solutions

#### "Port already in use"

```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5433  # Database

# Kill processes or change ports in docker-compose.yml
```

#### "Database connection refused"

```bash
# Check if database is running
qstatus

# Restart database
qdown && qup

# Connect directly to test
qdb
```

#### "Tests failing locally but pass in CI"

```bash
# Clean test environment
qtestdbdown && qtestdb

# Run tests exactly like CI
qtestdocker

# Check for environment differences
env | grep -E "(DATABASE|OPENAI|SECRET)"
```

#### "Docker build failing"

```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
qdown
docker-compose up --build

# Check Docker logs
docker-compose logs backend
```

#### "Import/Module errors"

```bash
# Ensure you're in the right directory
pwd
cd /path/to/quiznessPartner

# Reload environment
source .envrc

# Check Python path in container
docker-compose exec backend python -c "import sys; print(sys.path)"
```

### Getting Help

1. **Check Status**: `qstatus` - Shows all service status
2. **View Logs**: `qlogs` - See real-time logs
3. **Health Check**: `curl http://localhost:8000/health`
4. **Test Database**: `qcount` - Verify database connectivity
5. **Clean Restart**: `qdown && qup` - Nuclear option

---

## 📚 Quick Reference

### Command Options - Choose Your Style!

**You have two ways to run commands:**

#### 🐚 **Shell Aliases** (Fastest - if you have `.envrc` loaded)

```bash
qup                     # Start services
qtest                   # Run tests
qstatus                 # Show status
```

#### 🔨 **Make Commands** (Standardized - works anywhere)

```bash
make up                 # Start services
make test               # Run tests
make status             # Show status
make help               # See all commands
```

**💡 Use whichever feels more natural to you!**

### Essential Commands

| Shell Alias | Make Command         | Description                                 |
| ----------- | -------------------- | ------------------------------------------- |
| `qdev`      | `make dev`           | Start development environment + show status |
| `qtest`     | `make test`          | Run all tests                               |
| `qstatus`   | `make status`        | Show service status + database counts       |
| `qlogs`     | `make logs`          | Follow all service logs                     |
| `qformat`   | `make format`        | Auto-format code (Black + isort)            |
| `qcoverage` | `make test-coverage` | Generate test coverage report               |

### Service URLs

| Service     | URL                        | Purpose         |
| ----------- | -------------------------- | --------------- |
| Frontend    | http://localhost:3000      | React app       |
| Backend API | http://localhost:8000      | FastAPI backend |
| API Docs    | http://localhost:8000/docs | Swagger UI      |
| Database    | localhost:5433             | PostgreSQL      |

### File Structure

```
quiznessPartner/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── models/             # Database models
│   ├── auth/               # Authentication
│   ├── tests/              # Test suite
│   └── scripts/            # Development scripts
├── frontend/               # React frontend
│   ├── src/                # Source code
│   └── tests/              # Frontend tests
├── docker/                 # Docker configurations
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── .envrc                  # Development aliases
```

---

## 🎯 Success Metrics

### Development Quality Gates

- ✅ All tests passing (`qtest`)
- ✅ Code coverage ≥ 80% (`qcoverage`)
- ✅ No linting errors (`qlint`)
- ✅ Code formatted (`qformat`)
- ✅ Security scans clean
- ✅ Performance tests passing

### Performance Targets

- API response time < 200ms (95th percentile)
- Quiz generation < 5 seconds
- Database queries < 100ms
- Frontend load time < 2 seconds

**Happy coding! 🚀**

---

_💡 Pro Tip: Bookmark this file and keep it open during development. The aliases make everything much faster!_
