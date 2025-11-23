#!/bin/bash

# Vibehuntr Application Stop Script
# This script stops both the backend and frontend services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║           Stopping Vibehuntr Application...              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Stop backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    print_info "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm logs/backend.pid
    print_success "Backend stopped"
else
    print_warning "Backend PID file not found, trying to kill by port..."
    pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true
fi

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    print_info "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm logs/frontend.pid
    print_success "Frontend stopped"
else
    print_warning "Frontend PID file not found, trying to kill by process name..."
    pkill -f "vite" 2>/dev/null || true
fi

# Additional cleanup - kill any remaining processes on the ports
print_info "Cleaning up any remaining processes..."
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
else
    pkill -f "port 8000" 2>/dev/null || true
    pkill -f "port 5173" 2>/dev/null || true
fi

echo ""
print_success "Application stopped successfully! 👋"
echo ""
