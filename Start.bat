@echo off
chcp 65001 > nul
title GGSelCardinal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
    echo [GGSelCardinal] Virtual environment not found, using system Python.
    python main.py
) else (
    venv\Scripts\python.exe main.py
)
pause
