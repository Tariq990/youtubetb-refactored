@echo off
title Quick Fix - Install Dependencies
color 0A

echo ========================================
echo   Quick Fix - Installing Dependencies
echo ========================================
echo.

:: Create virtual environment if missing
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo Failed to create venv!
        pause
        exit /b 1
    )
)

:: Activate venv
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install requirements
echo Installing requirements...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)

:: Install Playwright
echo Installing Playwright Chromium...
python -m playwright install chromium

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo Now run: run.bat
pause
