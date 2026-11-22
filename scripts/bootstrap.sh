#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  ClearWayAI - Linux Bootstrap & Environment Setup        "
echo "=========================================================="

echo -e "\n[1/5] Checking Python environment..."
if command -v python3 &>/dev/null; then
    python3 --version
else
    echo "Error: Python3 is not installed."
    exit 1
fi

echo -e "\n[2/5] Checking Node.js environment..."
if command -v node &>/dev/null; then
    node --version
else
    echo "Error: Node.js is not installed."
    exit 1
fi

echo -e "\n[3/5] Checking configuration (.env)..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
else
    echo ".env already exists."
fi

echo -e "\n[4/5] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo -e "\n[5/5] Installing Node dependencies..."
npm install

echo "=========================================================="
echo " Bootstrap Complete! Run:"
echo "   - Backend: python3 -m uvicorn apps.api.src.main:app --reload --port 8000"
echo "   - Frontend: npm --prefix apps/web run dev"
echo "   - Tests:    pytest -v"
echo "=========================================================="
