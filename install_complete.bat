@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title YouTubeTB - Complete Installation

:: ============================================================
:: YouTubeTB Complete Installation Script
:: ============================================================
:: This script performs a complete installation on a fresh Windows system:
::   1. Checks for Python 3.11+ (downloads if missing)
::   2. Downloads and installs FFmpeg
::   3. Adds both to Windows PATH
::   4. Clones the repository (if not already cloned)
::   5. Installs Python dependencies
::   6. Installs Playwright browsers
::   7. Decrypts secrets with password
::   8. Verifies installation
:: ============================================================

echo.
echo ===============================================
echo   YouTubeTB - Complete Installation
echo ===============================================
echo.

:: Set color for better visibility
color 0A

:: ============================================================
:: SECTION 1: Check Administrator Rights
:: ============================================================
echo [1/8] Checking administrator rights...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ❌ ERROR: This script requires administrator rights!
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)
echo ✅ Administrator rights confirmed
echo.

:: ============================================================
:: SECTION 2: Python Installation Check
:: ============================================================
echo [2/8] Checking Python installation...

:: Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Python not found. Downloading Python 3.11...
    
    :: Create temp directory
    if not exist "%TEMP%\youtubetb_install" mkdir "%TEMP%\youtubetb_install"
    cd /d "%TEMP%\youtubetb_install"
    
    :: Download Python 3.11.9 installer
    echo    Downloading Python installer...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python_installer.exe'}"
    
    if not exist "python_installer.exe" (
        echo ❌ Failed to download Python installer!
        echo Please download manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Install Python with interactive installer (more reliable)
    echo    Installing Python 3.11.9...
    echo    ⚠️  IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    start /wait python_installer.exe InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0
    
    :: Wait for installation
    echo    Waiting for installation to complete...
    timeout /t 15 /nobreak >nul
    
    :: Refresh environment variables
    echo    Refreshing environment variables...
    call :RefreshEnv
    
    :: Verify installation
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo.
        echo ❌ Python installation failed or PATH not updated!
        echo.
        echo 📋 Manual Installation Steps:
        echo    1. Close this window
        echo    2. Double-click the installer at: %TEMP%\youtubetb_install\python_installer.exe
        echo    3. ✅ CHECK "Add Python to PATH" during installation
        echo    4. Complete the installation
        echo    5. Restart this script
        echo.
        echo Or download from: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    
    echo ✅ Python installed successfully
) else (
    :: Check Python version
    for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
    echo ✅ Python !PYTHON_VERSION! found
    
    :: Verify version is 3.11+
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if !MAJOR! LSS 3 (
        echo ❌ Python version too old. Requires Python 3.11+
        echo Please install from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    if !MAJOR! EQU 3 if !MINOR! LSS 11 (
        echo ⚠️  Warning: Python 3.!MINOR! detected. Recommended: Python 3.11+
        echo Continue anyway? (Y/N)
        set /p CONTINUE=
        if /i not "!CONTINUE!"=="Y" exit /b 1
    )
)
echo.

:: ============================================================
:: SECTION 3: FFmpeg Installation
:: ============================================================
echo [3/8] Checking FFmpeg installation...

:: Check if FFmpeg is in PATH
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  FFmpeg not found. Installing...
    
    :: Create installation directory
    set FFMPEG_DIR=C:\ffmpeg
    if not exist "!FFMPEG_DIR!" mkdir "!FFMPEG_DIR!"
    
    :: Download FFmpeg
    echo    Downloading FFmpeg...
    cd /d "%TEMP%\youtubetb_install"
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'}"
    
    if not exist "ffmpeg.zip" (
        echo ❌ Failed to download FFmpeg!
        echo Please download manually from: https://ffmpeg.org/download.html
        pause
        exit /b 1
    )
    
    :: Extract FFmpeg
    echo    Extracting FFmpeg...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '!FFMPEG_DIR!' -Force"
    
    :: Find the bin directory (it's nested in a versioned folder)
    for /d %%D in ("!FFMPEG_DIR!\ffmpeg-*") do (
        set FFMPEG_BIN=%%D\bin
    )
    
    if not exist "!FFMPEG_BIN!\ffmpeg.exe" (
        echo ❌ FFmpeg extraction failed!
        pause
        exit /b 1
    )
    
    :: Add to PATH permanently
    echo    Adding FFmpeg to PATH...
    setx PATH "%PATH%;!FFMPEG_BIN!" /M >nul 2>&1
    set "PATH=%PATH%;!FFMPEG_BIN!"
    
    :: Verify installation
    call :RefreshEnv
    ffmpeg -version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ⚠️  FFmpeg installed but not in PATH. Please restart your computer.
        echo    Installed to: !FFMPEG_BIN!
    ) else (
        echo ✅ FFmpeg installed successfully
    )
) else (
    echo ✅ FFmpeg already installed
)
echo.

:: ============================================================
:: SECTION 4: Git Check and Repository Clone
:: ============================================================
echo [4/8] Checking repository...

:: Check if we're already in the repo
if exist "%~dp0\.git" (
    echo ✅ Already inside repository
    set "REPO_DIR=%~dp0"
) else (
    :: Check if git is installed
    git --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo ⚠️  Git not found. Please install Git first:
        echo    https://git-scm.com/download/win
        echo.
        echo    After installing Git, run this script again.
        pause
        exit /b 1
    )
    
    echo ⚠️  Not inside repository. Please provide GitHub repository URL:
    echo    (or press Enter to skip cloning)
    set /p REPO_URL=
    
    if "!REPO_URL!"=="" (
        echo ⚠️  Skipping repository clone. Make sure you're in the correct directory.
        set "REPO_DIR=%CD%"
    ) else (
        echo    Cloning repository...
        git clone "!REPO_URL!" youtubetb_refactored
        if %errorLevel% neq 0 (
            echo ❌ Failed to clone repository!
            pause
            exit /b 1
        )
        cd youtubetb_refactored
        set "REPO_DIR=%CD%"
        echo ✅ Repository cloned successfully
    )
)
echo.

:: Navigate to repo directory
cd /d "!REPO_DIR!"

:: ============================================================
:: SECTION 5: Python Virtual Environment
:: ============================================================
echo [5/8] Setting up Python virtual environment...

:: Create venv if it doesn't exist
if not exist "venv" (
    echo    Creating virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ❌ Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

:: Activate venv
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ❌ Failed to activate virtual environment!
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

:: ============================================================
:: SECTION 6: Install Python Dependencies
:: ============================================================
echo [6/8] Installing Python dependencies...

:: Upgrade pip first
echo    Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install requirements
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

echo    Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo ❌ Failed to install dependencies!
    echo    Trying again with verbose output...
    pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully
echo.

:: ============================================================
:: SECTION 7: Install Playwright Browsers
:: ============================================================
echo [7/8] Installing Playwright browsers...

echo    Downloading Chromium (required for web scraping)...
playwright install chromium
if %errorLevel% neq 0 (
    echo ⚠️  Playwright installation had issues, but continuing...
) else (
    echo ✅ Playwright browsers installed
)
echo.

:: ============================================================
:: SECTION 8: Decrypt Secrets
:: ============================================================
echo [8/8] Setting up secrets...

:: Check if secrets_encrypted exists
if exist "secrets_encrypted" (
    echo    Encrypted secrets found. Do you want to decrypt them now? (Y/N)
    set /p DECRYPT=
    
    if /i "!DECRYPT!"=="Y" (
        echo.
        echo    Running decryption script...
        echo    You will be prompted for the encryption password.
        echo.
        python scripts/decrypt_secrets.py
        if %errorLevel% neq 0 (
            echo ⚠️  Decryption failed or was cancelled.
            echo    You can run it later with: python scripts\decrypt_secrets.py
        ) else (
            echo ✅ Secrets decrypted successfully
        )
    ) else (
        echo ⚠️  Skipping decryption. Run later with: python scripts\decrypt_secrets.py
    )
) else (
    echo ⚠️  No encrypted secrets found (secrets_encrypted/ directory missing)
    echo    You'll need to manually create secrets/ folder with required files:
    echo      - api_key.txt (Gemini API key)
    echo      - cookies.txt (YouTube cookies)
    echo      - client_secret.json (YouTube OAuth)
    echo      - token.json (YouTube OAuth token)
)
echo.

:: ============================================================
:: SECTION 9: Final Verification
:: ============================================================
echo ===============================================
echo   Installation Complete! Running Verification
echo ===============================================
echo.

:: Run verification tests
echo Verifying installation...
python scripts/test_all_apis.py
if %errorLevel% neq 0 (
    echo.
    echo ⚠️  Some verification tests failed.
    echo    This is normal if you haven't set up all API keys yet.
    echo.
)

:: ============================================================
:: Success Message
:: ============================================================
echo.
echo ===============================================
echo   ✅ INSTALLATION SUCCESSFUL!
echo ===============================================
echo.
echo Next steps:
echo   1. Ensure all API keys are in secrets/ folder
echo   2. Run: python main.py
echo   3. Follow the interactive menu
echo.
echo Useful commands:
echo   - Run pipeline: python main.py
echo   - Encrypt secrets: python scripts\encrypt_secrets.py
echo   - Decrypt secrets: python scripts\decrypt_secrets.py
echo   - Test APIs: python scripts\test_all_apis.py
echo.
echo Documentation: docs/QUICK_START.md
echo.
pause
exit /b 0

:: ============================================================
:: Helper Function: Refresh Environment Variables
:: ============================================================
:RefreshEnv
:: Refresh PATH without restarting
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
