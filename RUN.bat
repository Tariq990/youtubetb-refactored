@echo off
echo ========================================
echo YouTubeTB - Starting Application
echo ========================================
echo.

REM Set UTF-8 encoding for Arabic support
chcp 65001 >nul

REM Check if virtual environment exists
if exist venv (
    echo Using virtual environment...
    call venv\Scripts\activate.bat
    python main.py
    call deactivate
) else (
    echo No virtual environment found, using system Python...
    python main.py
)

echo.
echo ========================================
echo Application Closed
echo ========================================
pause

