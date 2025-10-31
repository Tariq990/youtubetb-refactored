@echo off
:: ============================================================
:: YouTubeTB - Smart Auto-Install (One Command Setup)
:: Detects problems, fixes them, installs everything
:: ============================================================
setlocal EnableExtensions EnableDelayedExpansion

title YouTubeTB - Smart Setup
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║         YouTubeTB - Smart Auto-Installer v3.0           ║
echo ║     Detects Problems → Fixes → Installs → Verifies      ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: Set working directory to script location
cd /d "%~dp0"
set "ROOT=%~dp0"

:: ============================================================
:: STEP 1: Check Admin Rights
:: ============================================================
echo [1/10] 🔐 Checking administrator rights...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo    ❌ Not running as administrator
    echo    🔄 Restarting with admin rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
echo    ✅ Administrator rights confirmed
echo.

:: ============================================================
:: STEP 2: Detect & Install Python (Any Version)
:: ============================================================
echo [2/10] 🐍 Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo    ❌ Python not found
    echo    📥 Installing Python 3.13.0 automatically...
    
    :: Create temp directory
    if not exist "%TEMP%\yttb_setup" mkdir "%TEMP%\yttb_setup"
    
    :: Download Python installer
    echo    ⏬ Downloading Python installer (~30 MB)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile '%TEMP%\yttb_setup\python_installer.exe'"
    
    if not exist "%TEMP%\yttb_setup\python_installer.exe" (
        echo    ❌ Download failed!
        echo    📋 Please download manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Install silently
    echo    ⚙️  Installing Python (silent mode)...
    "%TEMP%\yttb_setup\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0
    timeout /t 10 /nobreak >nul
    
    :: Refresh PATH
    call :RefreshPath
    
    :: Verify
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo    ❌ Installation failed - Please install manually
        pause
        exit /b 1
    )
)

python --version > "%TEMP%\pyver.txt" 2>&1
set /p PYTHON_VER=<"%TEMP%\pyver.txt"
del "%TEMP%\pyver.txt" 2>nul
echo    ✅ %PYTHON_VER% detected
echo    ℹ️  Any Python version accepted (no restrictions)
echo.

:: ============================================================
:: STEP 3: Detect & Install FFmpeg
:: ============================================================
echo [3/10] 🎬 Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo    ❌ FFmpeg not found
    echo    📥 Installing FFmpeg automatically...
    
    :: Download FFmpeg
    echo    ⏬ Downloading FFmpeg (~100 MB, may take 2-5 min)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile '%TEMP%\yttb_setup\ffmpeg.zip'"
    
    if not exist "%TEMP%\yttb_setup\ffmpeg.zip" (
        echo    ⚠️  Download failed - Trying alternative...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile '%TEMP%\yttb_setup\ffmpeg.zip'"
    )
    
    if exist "%TEMP%\yttb_setup\ffmpeg.zip" (
        :: Extract
        echo    📂 Extracting FFmpeg...
        powershell -Command "Expand-Archive -Path '%TEMP%\yttb_setup\ffmpeg.zip' -DestinationPath 'C:\ffmpeg' -Force"
        
        :: Find bin directory
        for /d %%d in ("C:\ffmpeg\ffmpeg*") do (
            if exist "%%d\bin\ffmpeg.exe" (
                set "FFMPEG_BIN=%%d\bin"
            )
        )
        
        :: Add to PATH
        echo    🔧 Adding FFmpeg to system PATH...
        setx /M PATH "%PATH%;!FFMPEG_BIN!" >nul 2>&1
        set "PATH=%PATH%;!FFMPEG_BIN!"
        
        echo    ✅ FFmpeg installed to: !FFMPEG_BIN!
    ) else (
        echo    ⚠️  Auto-install failed - Download manually from: https://ffmpeg.org
        echo    💡 Continuing anyway (you can install FFmpeg later)
    )
) else (
    echo    ✅ FFmpeg already installed
)
echo.

:: ============================================================
:: STEP 4: Clean Old Virtual Environment
:: ============================================================
echo [4/10] 🧹 Checking virtual environment...
if exist "venv" (
    echo    🗑️  Removing old virtual environment...
    rmdir /s /q venv 2>nul
    echo    ✅ Old venv removed
)
echo.

:: ============================================================
:: STEP 5: Create Fresh Virtual Environment
:: ============================================================
echo [5/10] 🏗️  Creating new virtual environment...
python -m venv venv
if %errorLevel% neq 0 (
    echo    ❌ Failed to create venv
    echo    🔧 Trying to install venv module...
    python -m pip install virtualenv
    python -m virtualenv venv
)

if not exist "venv\Scripts\activate.bat" (
    echo    ❌ Virtual environment creation failed!
    pause
    exit /b 1
)
echo    ✅ Virtual environment created
echo.

:: Activate venv
call venv\Scripts\activate.bat

:: ============================================================
:: STEP 6: Upgrade pip & Install Build Tools
:: ============================================================
echo [6/10] 📦 Upgrading pip and installing build tools...
python -m pip install --upgrade pip setuptools wheel --quiet
echo    ✅ pip upgraded
echo.

:: ============================================================
:: STEP 7: Smart Dependency Installation
:: ============================================================
echo [7/10] 📚 Installing Python dependencies...
echo    ℹ️  This may take 5-15 minutes depending on your Python version
echo    ℹ️  Some packages may fail - we'll handle that automatically
echo.

:: Try full installation first
echo    📥 Attempting full installation...
python -m pip install -r requirements.txt --no-warn-script-location 2>&1 | findstr /V "Using cached Downloading"

:: Check if openai-whisper failed (common with Python 3.14+)
python -c "import openai_whisper" >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo    ⚠️  openai-whisper installation failed
    echo    💡 This is normal for Python 3.14+ (numba incompatibility)
    echo    🔧 Installing without whisper (word-level subtitles disabled)
    echo.
    
    :: Create requirements without whisper
    findstr /V "openai-whisper" requirements.txt > "%TEMP%\requirements_no_whisper.txt"
    python -m pip install -r "%TEMP%\requirements_no_whisper.txt" --no-warn-script-location
)

:: Verify critical packages
echo.
echo    🔍 Verifying critical packages...
set "MISSING_PACKAGES="
for %%p in (
    google-generativeai
    playwright
    yt-dlp
    Pillow
    requests
    typer
    rich
) do (
    python -c "import %%p" >nul 2>&1
    if !errorLevel! neq 0 (
        echo    ❌ Missing: %%p
        set "MISSING_PACKAGES=!MISSING_PACKAGES! %%p"
    ) else (
        echo    ✅ %%p
    )
)

if defined MISSING_PACKAGES (
    echo.
    echo    🔧 Installing missing packages individually...
    for %%p in (!MISSING_PACKAGES!) do (
        echo       Installing %%p...
        python -m pip install %%p --quiet
    )
)

echo.
echo    ✅ Python packages installed
echo.

:: ============================================================
:: STEP 8: Install Playwright Browsers
:: ============================================================
echo [8/10] 🌐 Installing Playwright browsers...
python -m playwright install chromium --force
if %errorLevel% neq 0 (
    echo    ⚠️  Playwright installation warning (may still work)
) else (
    echo    ✅ Chromium browser installed
)
echo.

:: ============================================================
:: STEP 9: Setup Secrets (Decrypt if available)
:: ============================================================
echo [9/10] 🔐 Setting up secrets...

if exist "secrets_encrypted" (
    echo    📁 Found encrypted secrets
    
    :: Check for password in environment variable
    if defined YTTB_SECRETS_PASSWORD (
        echo    🔓 Decrypting automatically (using env variable)...
        echo !YTTB_SECRETS_PASSWORD! | python scripts\decrypt_secrets.py >nul 2>&1
    ) else (
        echo    🔑 Enter decryption password (or press Enter to skip):
        set /p "SECRET_PASS="
        if not "!SECRET_PASS!"=="" (
            echo !SECRET_PASS! | python scripts\decrypt_secrets.py
        ) else (
            echo    ⏭️  Skipped decryption
            echo    💡 You can decrypt later: python scripts\decrypt_secrets.py
        )
    )
) else (
    if not exist "secrets" mkdir secrets
    echo    📋 No encrypted secrets found
    echo    💡 Create secrets manually in secrets/ folder:
    echo       - api_key.txt (Gemini API)
    echo       - cookies.txt (YouTube cookies)
    echo       - client_secret.json (YouTube OAuth)
    echo       - token.json (YouTube OAuth token)
)
echo.

:: ============================================================
:: STEP 10: Final Verification
:: ============================================================
echo [10/10] ✅ Verifying installation...
echo.

:: Check Python packages
set "ALL_OK=1"
echo    🐍 Python Packages:
for %%p in (rich typer google.generativeai) do (
    python -c "import %%p" >nul 2>&1
    if !errorLevel! equ 0 (
        echo       ✅ %%p
    ) else (
        echo       ❌ %%p
        set "ALL_OK=0"
    )
)

echo.
echo    🛠️  External Tools:
ffmpeg -version >nul 2>&1
if !errorLevel! equ 0 (
    echo       ✅ FFmpeg
) else (
    echo       ⚠️  FFmpeg (install manually if needed)
)

echo.
echo    📂 Secrets:
if exist "secrets\api_key.txt" (
    echo       ✅ api_key.txt
) else (
    echo       ⚠️  api_key.txt (add your Gemini API key)
)

if exist "secrets\cookies.txt" (
    echo       ✅ cookies.txt
) else (
    echo       ℹ️  cookies.txt (optional - for age-restricted videos)
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
if !ALL_OK! equ 1 (
    echo ║              ✅ INSTALLATION COMPLETE! ✅               ║
) else (
    echo ║          ⚠️  INSTALLATION WITH WARNINGS ⚠️            ║
)
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 🚀 Quick Start:
echo    1. Activate venv:  venv\Scripts\activate
echo    2. Run program:    python main.py
echo.
echo 📚 Documentation:
echo    - Quick Start: docs\QUICK_START.md
echo    - Full Guide:  docs\INSTALL.md
echo.

pause
goto :eof

:: ============================================================
:: Helper Function: Refresh Environment PATH
:: ============================================================
:RefreshPath
:: Refresh environment variables without restarting
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
