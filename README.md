# QuizNess Partner

[![CI/CD](https://github.com/mackenziecox/quiznessPartner/actions/workflows/ci.yml/badge.svg)](https://github.com/mackenziecox/quiznessPartner/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mackenziecox/quiznessPartner/branch/main/graph/badge.svg)](https://codecov.io/gh/mackenziecox/quiznessPartner)

An AI-powered quiz generation platform that creates interactive quizzes from documents and text content.

## 🚀 Features

- **Document Upload**: Generate quizzes from PDF documents
- **Text-based Quiz Generation**: Create quizzes from any text content
- **AI-Powered Questions**: Uses OpenAI to generate high-quality questions
- **User Authentication**: Secure user registration and login
- **Quiz Management**: Save, retrieve, and manage quizzes
- **Interactive Interface**: Modern React frontend with TypeScript
- **Real-time Results**: Instant quiz scoring and feedback

## 📋 Prerequisites

- **Docker & Docker Compose**: For containerized development
- **Node.js 18+**: For frontend development
- **Python 3.9+**: For backend development
- **Git**: For version control

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd quiznessPartner

# Load development environment
direnv allow  # or source .envrc
```

### 2. Environment Configuration

Copy environment files and configure:

```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

Required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)
- `DATABASE_URI`: PostgreSQL connection string

### 3. Start Development Environment

```bash
# Start all services
qup

# Check status
qstatus

# View logs
qlogs
```

### 4. Run Tests

```bash
# Run all tests
qtest

# Run specific test types
qtestunit      # Unit tests only
qtestint       # Integration tests
qtestperf      # Performance tests

# Generate coverage report
qcoverage
```

## 🧪 Testing Environment

Our comprehensive testing infrastructure includes:

### Test Types

- **Unit Tests**: Fast, isolated function testing
- **Integration Tests**: End-to-end API workflow testing
- **Performance Tests**: Load and response time validation
- **Security Tests**: Vulnerability scanning

### Quick Testing Commands

```bash
# Basic testing
qtest                    # All tests (except slow ones)
qtestfull               # ALL tests including performance
qtestfast               # Run tests in parallel

# Specific test types
qtestunit               # Unit tests only
qtestint                # Integration tests
qtestapi                # API endpoint tests
qtestauth               # Authentication tests

# Load testing
qload                   # Basic load test
qloadfast               # Quick 2-minute load test
qloadheavy              # Heavy 5-minute load test

# Docker testing
qtestdocker             # Run tests in Docker
qloaddocker             # Load test with Docker
```

### Test Infrastructure

- **Pytest**: Test framework with fixtures and markers
- **Factory Boy**: Test data generation
- **Locust**: Load testing and performance validation
- **Coverage**: Code coverage reporting with 80% target
- **CI/CD**: Automated testing with GitHub Actions

### Database Testing

- **SQLite**: Fast unit tests
- **PostgreSQL**: Integration and performance tests
- **Docker**: Isolated test environments
- **Migrations**: Automatic database setup

## 📊 Code Quality

### Automated Checks

```bash
# Format code
qformat                 # Auto-format with Black and isort

# Check code quality
qlint                   # Run all linters

# Pre-commit hooks
pip install pre-commit
pre-commit install      # Auto-run checks on commit
```

### Quality Gates

All code must pass:

- Black code formatting
- isort import sorting
- flake8 linting
- mypy type checking
- Security scans (bandit, safety)
- 80% test coverage minimum

## 🏗️ Architecture

### Backend (FastAPI)

```
backend/
├── main.py              # FastAPI application
├── models/              # SQLAlchemy models
├── auth/                # Authentication system
├── tests/               # Test suite
│   ├── test_api.py      # API tests
│   ├── test_integration.py  # Integration tests
│   └── test_performance.py # Performance tests
├── scripts/             # Development scripts
│   ├── test_local.sh    # Local testing script
│   └── load_test.sh     # Load testing script
└── requirements-dev.txt # Development dependencies
```

### Frontend (React + TypeScript)

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom hooks
│   ├── services/       # API services
│   └── types/          # TypeScript types
└── tests/              # Frontend tests
```

### Infrastructure

```
docker/
├── Dockerfile.backend       # Production backend
├── Dockerfile.backend.test  # Testing backend
├── Dockerfile.locust       # Load testing
└── nginx.conf              # Production web server

docker-compose.yml          # Development environment
docker-compose.test.yml     # Testing environment
docker-compose.prod.yml     # Production environment
```

## 🔄 Development Workflow

### Daily Development

1. **Start Environment**: `qdev` (starts services and shows status)
2. **Code Changes**: Make your changes
3. **Test**: `qtest` (run tests)
4. **Format**: `qformat` (auto-format code)
5. **Commit**: Git hooks run quality checks automatically

### Testing Workflow

1. **Unit Tests**: `qtestunit` (fast feedback)
2. **Integration Tests**: `qtestint` (full API testing)
3. **Performance Tests**: `qtestperf` (load validation)
4. **Coverage**: `qcoverage` (view coverage report)

### Load Testing

1. **Quick Test**: `qloadfast` (2-minute test)
2. **Comprehensive**: `qload` (interactive web UI)
3. **Stress Test**: `qloadheavy` (high load validation)

## 🚀 Deployment

### Environments

- **Development**: Local Docker environment
- **Testing**: Automated CI/CD testing
- **Staging**: Pre-production validation
- **Production**: Live deployment

### CI/CD Pipeline

1. **Code Quality**: Linting, formatting, type checking
2. **Security**: Vulnerability scanning, dependency checks
3. **Testing**: Unit, integration, and performance tests
4. **Build**: Docker image creation and validation
5. **Deploy**: Automated deployment to staging/production

### Monitoring

- **Health Checks**: `/health` endpoint monitoring
- **Metrics**: Performance and usage tracking
- **Logs**: Centralized logging and alerting
- **Coverage**: Test coverage tracking with Codecov

## 📖 API Documentation

### Core Endpoints

- `GET /health` - Health check
- `POST /api/v1/generate-quiz` - Generate quiz from text
- `POST /api/v1/upload-document` - Generate quiz from document
- `GET /api/v1/quiz/{id}` - Retrieve quiz
- `POST /api/v1/submit-answer` - Submit quiz answers

### Authentication

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/token` - Login and get JWT token
- Protected endpoints require `Authorization: Bearer <token>`

### Rate Limiting

- Quiz generation: 10 requests/minute per user
- Document upload: 5 requests/minute per user
- General API: 100 requests/minute per IP

## 🛠️ Development Commands

### Environment Management

```bash
qup                     # Start all services
qdown                   # Stop all services
qrestart                # Restart all services
qstatus                 # Show status and statistics
```

### Database Management

```bash
qdb                     # Connect to main database
qdbtest                 # Connect to test database
qusers                  # Show all users
qquizzes                # Show all quizzes
qcount                  # Show record counts
```

### Logs and Monitoring

```bash
qlogs                   # Follow all logs
qbacklogs               # Follow backend logs
qfrontlogs              # Follow frontend logs
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3000, 8000, 5433 are available
2. **Database Issues**: Run `qtestdb` to start test database
3. **Permission Errors**: Run `chmod +x backend/scripts/*.sh`
4. **Import Errors**: Ensure you're in the correct directory

### Getting Help

1. Check `qstatus` for service status
2. View logs with `qlogs`
3. Run health check: `curl http://localhost:8000/health`
4. Check the [Testing Guide](backend/TESTING.md) for detailed testing info

## 📚 Documentation

- [Testing Guide](backend/TESTING.md) - Comprehensive testing documentation
- [API Documentation](docs/api.md) - Detailed API reference
- [Deployment Guide](docs/deployment.md) - Production deployment
- [Contributing Guide](CONTRIBUTING.md) - Development guidelines

## 🤝 Contributing

1. **Fork** the repository
2. **Clone** your fork
3. **Create** a feature branch
4. **Make** your changes
5. **Test** thoroughly (`qtest`)
6. **Format** code (`qformat`)
7. **Submit** a pull request

All contributions must:

- Pass all tests (`qtest`)
- Meet code quality standards (`qlint`)
- Include appropriate test coverage
- Follow the existing code style

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: For the GPT API powering quiz generation
- **FastAPI**: For the excellent Python web framework
- **React**: For the frontend framework
- **PostgreSQL**: For reliable data storage
- **Docker**: For containerization and development environment
