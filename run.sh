#!/bin/bash
# Gladtidings Help Desk - Start script

cd "$(dirname "$0")/ticketing-system" || exit 1

echo "Starting Gladtidings Help Desk..."
echo "Dashboard: http://localhost:8000"
echo "Public form: http://localhost:8000/public"
echo ""
echo "Press Ctrl+C to stop"
echo ""

./venv/bin/python main.py