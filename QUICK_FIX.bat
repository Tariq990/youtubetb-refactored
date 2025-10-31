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

:: Install requirements (without openai-whisper for Python 3.14+)
echo Installing requirements...
if exist requirements.txt (
    echo Step 1: Installing all packages except openai-whisper...
    findstr /V "openai-whisper" requirements.txt > "%TEMP%\requirements_no_whisper.txt"
    pip install -r "%TEMP%\requirements_no_whisper.txt"
    del "%TEMP%\requirements_no_whisper.txt" 2>nul
    
    echo.
    echo Step 2: Verifying critical packages...
    python -c "import playwright" >nul 2>&1
    if %errorLevel% neq 0 (
        echo Installing playwright separately...
        pip install playwright
    )
) else (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)

echo.
echo Installing Playwright Chromium browser...
python -m playwright install chromium

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo Now run: run.bat
pause
