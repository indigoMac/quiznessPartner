#!/bin/bash

# QuizNess Partner - Development Setup Script
# This script sets up your development environment in one go!

set -e  # Exit on any error

echo "🚀 QuizNess Partner Development Setup"
echo "======================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ All prerequisites met!"

# Setup environment files
echo ""
echo "🔧 Setting up environment files..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env from example"
    else
        echo "⚠️  backend/.env.example not found, creating basic .env"
        cat > backend/.env << EOF
# Database
DATABASE_URI=postgresql://postgres:postgres@db:5432/quizness
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=quizness

# Authentication
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=True

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# OpenAI (you need to add your key)
OPENAI_API_KEY=your_openai_api_key_here
EOF
    fi
else
    echo "✅ backend/.env already exists"
fi

# Frontend environment
if [ ! -f "frontend/.env" ]; then
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env
        echo "✅ Created frontend/.env from example"
    else
        echo "⚠️  frontend/.env.example not found, creating basic .env"
        cat > frontend/.env << EOF
VITE_API_URL=http://localhost:8000
EOF
    fi
else
    echo "✅ frontend/.env already exists"
fi

# Load development environment
echo ""
echo "🔧 Loading development environment..."

# Check if direnv is available
if command -v direnv &> /dev/null; then
    echo "✅ direnv detected - you can run 'direnv allow' to auto-load environment"
    echo "   or source .envrc manually each time"
else
    echo "💡 Consider installing direnv for automatic environment loading:"
    echo "   brew install direnv  # on macOS"
fi

# Source the environment manually for this session
if [ -f ".envrc" ]; then
    source .envrc
    echo "✅ Environment loaded for this session"
fi

# Check OpenAI API Key
echo ""
echo "🔑 OpenAI API Key Check..."

if grep -q "your_openai_api_key_here" backend/.env; then
    echo "⚠️  Please add your OpenAI API key to backend/.env"
    echo "   Edit the OPENAI_API_KEY line with your actual key"
    echo "   You can get one from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Do you want to set your OpenAI API key now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your OpenAI API key: " openai_key
        if [ ! -z "$openai_key" ]; then
            # Replace the placeholder with actual key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/your_openai_api_key_here/$openai_key/" backend/.env
            else
                # Linux
                sed -i "s/your_openai_api_key_here/$openai_key/" backend/.env
            fi
            echo "✅ OpenAI API key set successfully"
        fi
    fi
else
    echo "✅ OpenAI API key appears to be configured"
fi

# Start services
echo ""
echo "🚀 Starting development services..."

# Function to check if we have the aliases loaded
if command -v qup &> /dev/null; then
    echo "✅ Using qup alias to start services"
    qup
else
    echo "✅ Starting services with docker-compose"
    docker-compose up -d
fi

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Checking service status..."

if command -v qstatus &> /dev/null; then
    qstatus
else
    docker-compose ps
fi

# Health check
echo ""
echo "🏥 Running health checks..."

# Check backend health
echo "Checking backend health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed - check logs with: docker-compose logs backend"
fi

# Check frontend
echo "Checking frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "⚠️  Frontend not accessible - check logs with: docker-compose logs frontend"
fi

# Run a quick test
echo ""
echo "🧪 Running quick test..."

if command -v qtest &> /dev/null; then
    echo "Running tests with qtest..."
    if qtest; then
        echo "✅ Tests passed!"
    else
        echo "⚠️  Some tests failed - this might be expected on first setup"
    fi
else
    echo "Running tests with docker-compose..."
    if docker-compose exec backend pytest --tb=short; then
        echo "✅ Tests passed!"
    else
        echo "⚠️  Some tests failed - this might be expected on first setup"
    fi
fi

# Setup complete
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your development environment is ready! Here's what's available:"
echo ""
echo "🌐 Services:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Database:  localhost:5433"
echo ""
echo "🛠️  Quick Commands (if you have .envrc loaded):"
echo "   qstatus    - Check service status"
echo "   qlogs      - View all logs"
echo "   qtest      - Run tests"
echo "   qdown      - Stop services"
echo "   qup        - Start services"
echo ""
echo "📚 Documentation:"
echo "   Development Guide: DEVELOPMENT_CHEAT_SHEET.md"
echo "   Project README:    README.md"
echo ""
echo "💡 Next Steps:"
echo "   1. Load environment: source .envrc (or direnv allow if you have direnv)"
echo "   2. Check status: qstatus"
echo "   3. View the cheat sheet: cat DEVELOPMENT_CHEAT_SHEET.md"
echo "   4. Start coding! 🚀"
echo ""

# Check if they want to open the browser
read -p "Would you like to open the frontend in your browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open http://localhost:3000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    else
        echo "Please open http://localhost:3000 in your browser"
    fi
fi

echo ""
echo "Happy coding! 🚀" 