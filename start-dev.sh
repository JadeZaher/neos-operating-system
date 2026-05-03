#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Starting NEOS API development server..."

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate venv
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -e "agent[dev]" --quiet

# Start server
cd agent
echo "Backend running at http://localhost:8000/dashboard"
python -m neos_agent.main --dev
