#!/bin/bash

# Vibehuntr Application Restart Script

echo "🔄 Restarting Vibehuntr Application..."
echo ""

# Stop the application
./stop_app.sh

# Wait a moment
sleep 2

# Start the application
./start_app.sh
