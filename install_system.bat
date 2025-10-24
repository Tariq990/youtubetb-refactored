@echo off
REM ========================================
REM YouTubeTB - System-wide Installation
REM No virtual environment required
REM ========================================

echo ========================================
echo YouTubeTB System Installation
echo ========================================
echo.

REM Check Python version
echo [1/6] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.10+ first.
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo    - Python %PYTHON_VERSION% detected

REM Check pip
echo.
echo [2/6] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not found!
    pause
    exit /b 1
)
echo    - pip OK

REM Upgrade pip
echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo    - pip upgraded

REM Install dependencies
echo.
echo [4/6] Installing dependencies...
echo    This may take 5-10 minutes...
python -m pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo    - All packages installed

REM Install Playwright browsers
echo.
echo [5/6] Installing Playwright browsers...
python -m playwright install chromium
if errorlevel 1 (
    echo WARNING: Playwright installation failed
    echo    TTS stage may not work properly
)
echo    - Playwright chromium installed

REM Check external tools
echo.
echo [6/6] Checking external tools...

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo    WARNING: FFmpeg not found
    echo    Download: https://ffmpeg.org/download.html
) else (
    echo    - FFmpeg: OK
)

where yt-dlp >nul 2>&1
if errorlevel 1 (
    echo    WARNING: yt-dlp not found
    echo    Install: pip install yt-dlp
) else (
    echo    - yt-dlp: OK
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run: python main.py
echo.
echo NOTE: Using system Python (no virtual environment)
echo      Make sure no conflicting package versions exist.
echo.
pause
