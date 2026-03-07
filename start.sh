#!/usr/bin/env bash
# start.sh — Run Wilder Bot in Codespaces or VPS
# Usage: bash start.sh

set -euo pipefail

# Load .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded .env"
fi

# Check SSID is set
if [ -z "${PO_SSID:-}" ] || [ "$PO_SSID" = "paste_your_ssid_here" ]; then
    echo ""
    echo "❌ SSID not set!"
    echo ""
    echo "  Do ONE of the following:"
    echo "  1. Create a .env file:  echo 'PO_SSID=your_ssid' > .env"
    echo "  2. Or set it directly:  export PO_SSID=your_ssid"
    echo ""
    exit 1
fi

echo ""
echo "============================================"
echo "  🤖 Pocket Option — Wilder Bot"
echo "  Mode: ${IS_DEMO:-demo}"
echo "============================================"
echo ""

python3 main.py
