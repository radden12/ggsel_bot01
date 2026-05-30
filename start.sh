#!/usr/bin/env bash
# Launcher for GGSelCardinal (Linux / macOS).
set -e
cd "$(dirname "$0")"
if [ -x "venv/bin/python" ]; then
    exec venv/bin/python main.py
else
    exec python3 main.py
fi
