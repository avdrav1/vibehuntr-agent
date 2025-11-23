#!/bin/bash

# Vibehuntr Application Startup Script
# This script starts both the backend (FastAPI) and frontend (React) services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    # Try multiple methods to check if port is in use
    if command_exists lsof; then
        lsof -i:"$1" -sTCP:LISTEN >/dev/null 2>&1
    elif command_exists ss; then
        ss -ltn | grep -q ":$1 "
    elif command_exists netstat; then
        netstat -ltn | grep -q ":$1 "
    elif command_exists nc; then
        nc -z localhost "$1" 2>/dev/null
    else
        # Fallback: try to connect with curl
        curl -s http://localhost:"$1" >/dev/null 2>&1
        return $?
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    print_info "Checking for processes on port $port..."
    
    # Try different methods to kill the process
    if command_exists lsof; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    else
        pkill -f "port $port" 2>/dev/null || true
    fi
}

# Print banner
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              🎉 Vibehuntr Application 🎉                  ║"
echo "║                                                           ║"
echo "║         React + FastAPI Event Planning Agent             ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists uv; then
    print_error "uv is not installed. Please install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
print_success "uv is installed"

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi
print_success "Node.js is installed"

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi
print_success "npm is installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env and add your Google Cloud credentials!"
    print_warning "You need to set either GOOGLE_API_KEY or GOOGLE_CLOUD_PROJECT"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
fi

# Check if Google credentials are configured
if ! grep -q "GOOGLE_API_KEY=.*[^=]" .env && ! grep -q "GOOGLE_CLOUD_PROJECT=.*[^=]" .env; then
    print_warning "Google Cloud credentials not configured in .env"
    print_warning "The agent will not work without credentials!"
    echo ""
    echo "To fix this, add one of the following to your .env file:"
    echo "  Option 1: GOOGLE_API_KEY=your-api-key-here"
    echo "  Option 2: GOOGLE_CLOUD_PROJECT=your-project-id"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check and kill existing processes
print_info "Checking for existing processes..."

if port_in_use 8000; then
    print_warning "Port 8000 is in use. Killing existing backend process..."
    kill_port 8000
    sleep 1
fi

if port_in_use 5173; then
    print_warning "Port 5173 is in use. Killing existing frontend process..."
    kill_port 5173
    sleep 1
fi

# Install dependencies if needed
print_info "Checking dependencies..."

if [ ! -d ".venv" ]; then
    print_info "Installing Python dependencies..."
    uv sync
    print_success "Python dependencies installed"
else
    print_success "Python dependencies already installed"
fi

if [ ! -d "frontend/node_modules" ]; then
    print_info "Installing frontend dependencies..."
    (cd frontend && npm install)
    print_success "Frontend dependencies installed"
else
    print_success "Frontend dependencies already installed"
fi

# Create log directory
mkdir -p logs

# Start backend
print_info "Starting backend server..."
uv run uvicorn backend.app.main:app --reload --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

# Wait for backend to start
print_info "Waiting for backend to start..."
BACKEND_READY=false
for i in {1..30}; do
    # Check if process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died. Check logs/backend.log for details."
        cat logs/backend.log | tail -20
        exit 1
    fi
    
    # Check if backend is responding
    if curl -s http://localhost:8000/health >/dev/null 2>&1 || curl -s http://localhost:8000/docs >/dev/null 2>&1 || port_in_use 8000; then
        # Give it one more second to fully initialize
        sleep 1
        if curl -s http://localhost:8000/health >/dev/null 2>&1 || curl -s http://localhost:8000/docs >/dev/null 2>&1; then
            print_success "Backend started successfully (PID: $BACKEND_PID)"
            BACKEND_READY=true
            break
        fi
    fi
    
    if [ $i -eq 30 ]; then
        print_error "Backend failed to start. Check logs/backend.log for details."
        echo ""
        print_info "Last 20 lines of backend log:"
        cat logs/backend.log | tail -20
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    print_error "Backend did not become ready in time"
    exit 1
fi

# Start frontend
print_info "Starting frontend server..."
(cd frontend && npm run dev > ../logs/frontend.log 2>&1 &)
FRONTEND_PID=$!
echo $FRONTEND_PID > logs/frontend.pid

# Wait for frontend to start
print_info "Waiting for frontend to start..."
FRONTEND_READY=false
for i in {1..30}; do
    # Check if frontend is responding
    if curl -s http://localhost:5173 >/dev/null 2>&1 || port_in_use 5173; then
        # Give it one more second to fully initialize
        sleep 1
        if curl -s http://localhost:5173 >/dev/null 2>&1; then
            print_success "Frontend started successfully"
            FRONTEND_READY=true
            break
        fi
    fi
    
    if [ $i -eq 30 ]; then
        print_error "Frontend failed to start. Check logs/frontend.log for details."
        echo ""
        print_info "Last 20 lines of frontend log:"
        cat logs/frontend.log | tail -20
        kill $BACKEND_PID 2>/dev/null || true
        pkill -f "vite" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

if [ "$FRONTEND_READY" = false ]; then
    print_error "Frontend did not become ready in time"
    exit 1
fi

# Print success message
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              ✨ Application Started! ✨                    ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
print_success "Backend running at: http://localhost:8000"
print_success "Frontend running at: http://localhost:5173"
echo ""
print_info "Logs are available in:"
echo "  - Backend: logs/backend.log"
echo "  - Frontend: logs/frontend.log"
echo ""
print_info "To stop the application, run: ./stop_app.sh"
echo ""
print_warning "Opening browser in 3 seconds..."
sleep 3

# Try to open browser
if command_exists xdg-open; then
    xdg-open http://localhost:5173 2>/dev/null || true
elif command_exists open; then
    open http://localhost:5173 2>/dev/null || true
else
    print_info "Please open http://localhost:5173 in your browser"
fi

echo ""
print_success "Application is ready! 🚀"
echo ""
