@echo off
echo ========================================
echo YouTubeTB - Starting Application
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and add your API keys
    echo Then run this script again
    pause
    exit /b 1
)

REM Set UTF-8 encoding for Arabic support
chcp 65001 >nul

REM Run the application
python main.py

REM Deactivate on exit
deactivate

