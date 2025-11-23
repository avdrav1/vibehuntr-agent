#!/bin/bash
# Start the ADK playground with environment variables loaded

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  WARNING: GOOGLE_API_KEY is not set!"
    echo "Please set it in your .env file or export it:"
    echo "  export GOOGLE_API_KEY='your-key-here'"
    echo ""
fi

echo "==============================================================================="
echo "| 🎉 Starting Vibehuntr Playground...                                         |"
echo "|                                                                             |"
echo "| 💡 Try asking: Find Italian restaurants in San Francisco                    |"
echo "|                Create a user for me named Sarah                             |"
echo "|                Create a hiking group called Weekend Warriors               |"
echo "|                                                                             |"
echo "| 🌐 Opening at: http://localhost:8501                                        |"
echo "==============================================================================="

uv run streamlit run vibehuntr_playground.py
