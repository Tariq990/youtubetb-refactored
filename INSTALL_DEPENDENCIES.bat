@echo off
title YouTubeTB - Install Dependencies
color 0A

:: Change to script directory (critical fix)
cd /d "%~dp0"

echo ========================================
echo   YouTubeTB - Install Dependencies
echo ========================================
echo.

:: Update from GitHub first
echo Updating from GitHub...
git pull origin master 2>nul
if %errorLevel% equ 0 (
    echo ✅ Repository updated
) else (
    echo ⚠️  Not a git repository or update failed (continuing anyway)
)
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
if %errorLevel% neq 0 (
    echo ⚠️  Failed to activate virtual environment
    echo Continuing anyway...
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install requirements (without openai-whisper for Python 3.14+)
echo Installing requirements...
if not exist requirements.txt (
    echo ERROR: requirements.txt not found in current directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Step 1: Installing all packages except openai-whisper...
findstr /V "openai-whisper" requirements.txt > "%TEMP%\requirements_no_whisper.txt"
pip install -r "%TEMP%\requirements_no_whisper.txt" --no-warn-script-location
del "%TEMP%\requirements_no_whisper.txt" 2>nul

echo.
echo Step 2: Verifying critical packages...

:: Check critical packages one by one (package_name:import_name)
set "packages=playwright:playwright google-generativeai:google.generativeai yt-dlp:yt_dlp Pillow:PIL requests:requests typer:typer rich:rich ffmpeg-python:ffmpeg mutagen:mutagen"

for %%p in (%packages%) do (
    for /f "tokens=1,2 delims=:" %%a in ("%%p") do (
        python -c "import %%b" >nul 2>&1
        if errorLevel 1 (
            echo    ❌ Missing: %%a - Installing now...
            pip install %%a --quiet
            
            :: Verify installation
            python -c "import %%b" >nul 2>&1
            if errorLevel 1 (
                echo       ⚠️  Failed to install %%a
            ) else (
                echo       ✅ %%a installed successfully
            )
        ) else (
            echo    ✅ %%a already installed
        )
    )
)

echo.
echo Installing Playwright Chromium browser...
python -m playwright install chromium

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo 🚀 Starting the program automatically...
timeout /t 2 /nobreak >nul
call RUN.bat
