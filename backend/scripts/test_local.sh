#!/bin/bash

# QuizNess Backend Testing Suite
# Comprehensive testing script for unit, integration, e2e, and performance tests

set -e  # Exit on any error

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTEST_CMD="/usr/local/bin/python3 -m pytest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Database setup
setup_test_db() {
    log_info "Setting up test database..."
    
    # Go to the parent directory where docker-compose.test.yml is located
    cd "${PROJECT_DIR}/.."
    
    # Start test database
    docker-compose -f docker-compose.test.yml up -d db-test
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker exec $(docker-compose -f docker-compose.test.yml ps -q db-test) pg_isready -U testuser -d testdb > /dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "Database failed to start within 30 seconds"
            cleanup_test_db
            exit 1
        fi
        
        echo -n "."
        sleep 1
    done
    
    # Return to project directory
    cd "${PROJECT_DIR}"
}

cleanup_test_db() {
    log_info "Cleaning up test database..."
    cd "${PROJECT_DIR}/.."
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
    log_success "Test database cleaned up"
}

# Change to project directory
cd "${PROJECT_DIR}"

# Set Python path
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Create reports directory
mkdir -p test-reports

case "$1" in
    "unit")
        log_info "Running unit tests..."
        $PYTEST_CMD tests/unit/ \
            -v \
            --cov=. \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "not integration and not e2e and not slow"
        log_success "Unit tests completed"
        ;;
    
    "integration")
        log_info "Running integration tests..."
        setup_test_db
        trap cleanup_test_db EXIT
        
        $PYTEST_CMD tests/integration/ \
            -v \
            --cov=. \
            --cov-append \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "integration"
        log_success "Integration tests completed"
        ;;
    
    "e2e")
        log_info "Running end-to-end tests..."
        setup_test_db
        trap cleanup_test_db EXIT
        
        $PYTEST_CMD tests/e2e/ \
            -v \
            --cov=. \
            --cov-append \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "e2e"
        log_success "E2E tests completed"
        ;;
    
    "performance")
        log_info "Running performance tests..."
        $PYTEST_CMD tests/performance/test_quiz_performance.py \
            -v \
            --durations=10 \
            -m "performance or slow"
        log_success "Performance tests completed"
        ;;
        
    "load")
        log_info "Running load tests..."
        if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_error "Server must be running on localhost:8000 for load tests"
            log_info "Start the server with: uvicorn main:app --reload"
            exit 1
        fi
        
        cd tests/performance
        locust -f test_load.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=30s --headless
        log_success "Load tests completed"
        ;;
    
    "all")
        log_info "Running complete test suite..."
        
        # Unit tests first
        $PYTEST_CMD tests/unit/ \
            -v \
            --cov=. \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "not integration and not e2e and not slow"
        
        # Integration tests
        setup_test_db
        trap cleanup_test_db EXIT
        
        $PYTEST_CMD tests/integration/ \
            -v \
            --cov=. \
            --cov-append \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "integration"
            
        # E2E tests  
        $PYTEST_CMD tests/e2e/ \
            -v \
            --cov=. \
            --cov-append \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "e2e"
            
        # Performance tests
        $PYTEST_CMD tests/performance/test_quiz_performance.py \
            -v \
            --durations=10 \
            -m "performance or slow"
            
        log_success "Complete test suite completed"
        ;;
    
    "fast")
        log_info "Running fast test suite (unit tests only)..."
        $PYTEST_CMD tests/unit/ \
            -v \
            --cov=. \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --durations=10 \
            -m "not integration and not e2e and not slow"
        log_success "Fast test suite completed"
        ;;
        
    "install")
        log_info "Installing test dependencies..."
        python3 -m pip install -r requirements.txt
        python3 -m pip install pytest-html pytest-json-report pytest-benchmark locust
        log_success "Dependencies installed"
        ;;
        
    "clean")
        log_info "Cleaning up test artifacts..."
        rm -rf htmlcov/ test-reports/ .coverage .pytest_cache/
        cleanup_test_db
        log_success "Cleanup completed"
        ;;
    
    *)
        echo "QuizNess Backend Testing Suite"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "    unit            Run unit tests only"
        echo "    integration     Run integration tests only"  
        echo "    e2e             Run end-to-end tests only"
        echo "    performance     Run performance tests only"
        echo "    load            Run load tests (server must be running)"
        echo "    all             Run complete test suite"
        echo "    fast            Run fast test suite (unit tests)"
        echo "    install         Install test dependencies"
        echo "    clean           Clean up test artifacts"
        echo ""
        echo "Examples:"
        echo "    $0 unit         # Run unit tests"
        echo "    $0 integration  # Run integration tests"
        echo "    $0 all          # Run all tests"
        echo "    $0 load         # Run load tests"
        ;;
esac 