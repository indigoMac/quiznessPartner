#!/bin/bash

# Load testing script using Locust
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
HOST="http://localhost:8000"
USERS=10
SPAWN_RATE=2
RUN_TIME="5m"
WEB_UI=true
HEADLESS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            WEB_UI=false
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --host HOST         Target host (default: http://localhost:8000)"
            echo "  -u, --users NUM     Number of users to simulate (default: 10)"
            echo "  -r, --spawn-rate NUM Rate of spawning users per second (default: 2)"
            echo "  -t, --run-time TIME Test duration (default: 5m)"
            echo "  --headless          Run without web UI"
            echo "  --docker            Use Docker Compose for testing"
            echo "  -h, --help          Show this help"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Go to the backend directory
cd "$(dirname "$0")/.."

print_status "Starting load testing for QuizNess API..."

if [ "$USE_DOCKER" = true ]; then
    print_status "Using Docker Compose for load testing..."
    
    # Start the application if not running
    print_status "Starting application services..."
    docker-compose -f ../docker-compose.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Start Locust using Docker
    print_status "Starting Locust load test..."
    docker-compose -f ../docker-compose.test.yml up locust-test
    
else
    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        print_error "Locust is not installed. Install it with: pip install locust"
        exit 1
    fi
    
    # Check if target host is accessible
    print_status "Testing connection to $HOST..."
    if ! curl -s "$HOST/health" > /dev/null; then
        print_warning "Cannot reach $HOST/health. Make sure the API is running."
        print_status "You can start it with: docker-compose up -d"
    fi
    
    # Build Locust command
    LOCUST_CMD="locust -f locustfile.py --host=$HOST"
    
    if [ "$HEADLESS" = true ]; then
        LOCUST_CMD="$LOCUST_CMD --headless -u $USERS -r $SPAWN_RATE -t $RUN_TIME --html=load_test_report.html"
        print_status "Running headless load test..."
        print_status "Users: $USERS, Spawn rate: $SPAWN_RATE/sec, Duration: $RUN_TIME"
    else
        print_status "Starting Locust web UI..."
        print_status "Open http://localhost:8089 in your browser"
        print_status "Suggested settings:"
        print_status "  - Number of users: $USERS"
        print_status "  - Spawn rate: $SPAWN_RATE"
        print_status "  - Host: $HOST"
    fi
    
    # Run Locust
    $LOCUST_CMD
fi

if [ "$HEADLESS" = true ]; then
    print_success "Load test completed!"
    if [ -f "load_test_report.html" ]; then
        print_status "Load test report saved to load_test_report.html"
        
        # Try to open report if on macOS
        if [[ "$OSTYPE" == "darwin"* ]] && command -v open &> /dev/null; then
            print_status "Opening load test report..."
            open load_test_report.html
        fi
    fi
fi 