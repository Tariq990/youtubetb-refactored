@echo off
echo ========================================
echo YouTubeTB - Setup Script for Windows
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK: Python found
echo.

REM Check FFmpeg
echo [2/5] Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg not found in PATH
    echo Please install FFmpeg from https://www.gyan.dev/ffmpeg/builds/
    echo You can continue, but video rendering will not work
    pause
) else (
    echo OK: FFmpeg found
)
echo.

REM Create virtual environment
echo [3/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo OK: Virtual environment created
)
echo.

REM Activate and install dependencies
echo [4/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo OK: Dependencies installed
echo.

REM Setup .env file
echo [5/5] Setting up environment file...
if exist .env (
    echo .env file already exists
) else (
    copy .env.example .env
    echo OK: .env file created
    echo.
    echo IMPORTANT: Please edit .env file and add your API keys:
    echo   - YT_API_KEY
    echo   - GEMINI_API_KEY
    echo   - ELEVENLABS_API_KEY
)
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python main.py
echo.
pause

