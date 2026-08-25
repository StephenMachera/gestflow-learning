#!/bin/bash
# ==========================================
# GESTFLOW SETUP — Linux / Mac
# ==========================================
# Run this script to install GestFlow.
# Usage: ./setup.sh
# ==========================================

set -e  # stop on any error

echo ""
echo "======================================"
echo "  🤚 GestFlow Setup for Linux/Mac"
echo "======================================"

# ── Check Python ──
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo "   Install from: https://python.org"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# ── Navigate to repo root ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

echo "✅ Repo: $REPO_DIR"

# ── Create virtual environment ──
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# ── Activate virtual environment ──
source .venv/bin/activate
echo "✅ Virtual environment activated"

# ── Run Python installer ──
echo ""
python3 installer/setup.py

echo ""
echo "======================================"
echo "✅ GestFlow setup complete!"
echo ""
echo "  To start GestFlow:"
echo "  source .venv/bin/activate"
echo "  cd gestflow/gestflow_02_content_engine"
echo "  python main.py"
echo "======================================"
echo ""