::   7. Decrypts secrets with password
::   8. Verifies installation
:: ============================================================

echo.
echo ===============================================
echo   YouTubeTB - Complete Installation
echo ===============================================
echo.

@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

:: Always operate from the script directory (repo root)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ============================================================
:: SECTION 2: Python Installation Check
:: ============================================================
echo [2/8] Checking Python installation...

:: Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Python not found. Downloading Python 3.13...
    
    :: Create temp directory
    if not exist "%TEMP%\youtubetb_install" mkdir "%TEMP%\youtubetb_install"
    pushd "%TEMP%\youtubetb_install"
    
    :: Download Python 3.13.0 installer (compatible version)
    echo    Downloading Python installer ^(~30 MB^)...
    echo    Please wait, this may take 1-3 minutes...
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host '    Downloading ' -NoNewline; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile 'python_installer.exe'; Write-Host 'Done!'"
    
    if not exist "python_installer.exe" (
        echo ❌ Failed to download Python installer!
        echo Please download manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Install Python with interactive installer (more reliable)
    echo    Installing Python 3.13.0...
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
    
    :: Return to previous directory
    popd
    echo ✅ Python installed successfully
) else (
    :: Check Python version
    for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
    echo ✅ Python !PYTHON_VERSION! found
    echo    Any Python version accepted (no restrictions)
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
    echo    Downloading FFmpeg ^(~90 MB^)...
    echo    Please wait, this may take 2-5 minutes depending on your internet speed...
    pushd "%TEMP%\youtubetb_install"
    
    :: Download with progress indication
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host '    Downloading ' -NoNewline; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'; Write-Host 'Done!'"
    
    if %errorLevel% neq 0 (
        echo.
        echo ❌ PowerShell download failed! Trying alternative method...
        echo    Please wait...
        curl -L -o ffmpeg.zip "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" 2>nul
    )
    
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
    
        :: Add to PATH permanently (robust, avoid duplicates and truncation)
        echo    Adding FFmpeg to PATH...
    
        :: Append to Machine PATH only if not already present
        powershell -NoProfile -Command ^
            "$p='!FFMPEG_BIN!';" ^
            "$m=[Environment]::GetEnvironmentVariable('Path','Machine');" ^
            "if(-not ($m -split ';' | ForEach-Object { $_.Trim().ToLower() }) -contains $p.ToLower()){" ^
            "  [Environment]::SetEnvironmentVariable('Path', ($m.TrimEnd(';') + ';' + $p), 'Machine')" ^
            "}"
    
        :: Update current CMD session immediately
        set "PATH=%PATH%;!FFMPEG_BIN!"
    
        :: Refresh PATH from registry for this process
        call :RefreshEnv
    
        :: Optional: notify environment change so new processes pick it up
        powershell -NoProfile -Command ^
            "$sig='[DllImport(\"user32.dll\",SetLastError=true,CharSet=CharSet.Auto)]public static extern IntPtr SendMessageTimeout(IntPtr h,int m,IntPtr w,string l,int f,int t,out IntPtr r);';" ^
            "Add-Type -MemberDefinition $sig -Name 'Win32' -Namespace 'PInvoke' | Out-Null;" ^
            "[PInvoke.Win32]::SendMessageTimeout([IntPtr]0xffff,0x1A,[IntPtr]0,'Environment',2,5000,[ref]([IntPtr]::Zero)) | Out-Null"
    
        :: Verify installation
    ffmpeg -version >nul 2>&1
    if %errorLevel% neq 0 (
                echo ⚠️  FFmpeg installed but not detected in current session.
                echo    Installed to: !FFMPEG_BIN!
                echo    Tip: Open a new CMD window or run it via full path above.
    ) else (
        echo ✅ FFmpeg installed successfully
    )
    
    :: Return to previous directory
    popd
) else (
    echo ✅ FFmpeg already installed
)
echo.

:: ============================================================
:: SECTION 4: Git Check and Repository Clone
:: ============================================================
echo [4/8] Checking repository...

:: Check if we're already in the repo (prefer script directory)
if exist "%SCRIPT_DIR%\.git" (
    echo ✅ Already inside repository
    set "REPO_DIR=%SCRIPT_DIR%"
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

:: Create venv if it doesn't exist (in repo root)
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
call "%SCRIPT_DIR%venv\Scripts\activate.bat"
if %errorLevel% neq 0 (
    echo ❌ Failed to activate virtual environment!
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

REM Ensure current session can import project packages (src, etc.)
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

:: ============================================================
:: SECTION 6: Install Python Dependencies
:: ============================================================
echo [6/8] Installing Python dependencies...

:: Upgrade pip first
echo    Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install requirements
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

echo    Installing dependencies ^(~500 MB, 5-10 minutes^)...
echo    ⏳ This will download and install 60+ Python packages...
echo    📊 Progress will be shown below:
echo.
pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorLevel% neq 0 (
    echo.
    echo ❌ Failed to install dependencies!
    echo    Some packages may have failed. Retrying problematic packages...
    pip install -r requirements.txt --no-cache-dir
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully
echo.

:: ============================================================
:: SECTION 7: Install Playwright Browsers
:: ============================================================
echo [7/8] Installing Playwright browsers...

echo    Downloading Chromium ^(required for web scraping^)...
playwright install chromium
if %errorLevel% neq 0 (
    echo ⚠️  Playwright installation had issues, but continuing...
) else (
    echo ✅ Playwright browsers installed
)
echo.

:: ============================================================
:: SECTION 8: Decrypt Secrets (Automatic)
:: ============================================================
echo [8/8] Setting up secrets...

if exist "secrets_encrypted" (
    echo    Encrypted secrets found. Attempting automatic decryption...
    if defined YTTB_SECRETS_PASSWORD (
        echo    Using password from environment variable YTTB_SECRETS_PASSWORD
        python scripts\decrypt_secrets.py --non-interactive --password "%YTTB_SECRETS_PASSWORD%"
    ) else (
        echo    No password provided via env var. You will be prompted now.
        python scripts\decrypt_secrets.py
    )
    if !errorlevel! neq 0 (
        echo ⚠️  Decryption returned exit code !errorlevel!.
        if !errorlevel! equ 2 (
            echo    Wrong password provided. Please re-run decryption later:
            echo       python scripts\decrypt_secrets.py
        ) else (
            echo    Decryption failed. You can retry later:
            echo       python scripts\decrypt_secrets.py
        )
    ) else (
        echo ✅ Secrets decrypted successfully
    )
) else (
    echo ⚠️  No encrypted secrets found ^(secrets_encrypted/ directory missing^)
    echo    You'll need to manually create secrets/ folder with required files:
    echo      - api_key.txt ^(Gemini API key^)
    echo      - cookies.txt ^(YouTube cookies^)
    echo      - client_secret.json ^(YouTube OAuth^)
    echo      - token.json ^(YouTube OAuth token^)
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
if exist scripts\test_all_apis.py (
    python -m scripts.test_all_apis
) else (
    echo (Skipping scripts\test_all_apis.py - not found)
)
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
