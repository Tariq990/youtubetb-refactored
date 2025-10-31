@echo off
title YouTubeTB - Full Auto Setup (Main Runner)
color 0A
setlocal EnableExtensions EnableDelayedExpansion

echo ==========================================================
echo       🚀 YouTubeTB - Full Auto Setup (Main Runner)
echo ==========================================================
echo.

:: STEP 1: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ This script requires Administrator rights.
    echo 🔄 Restarting as Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
echo ✅ Running as Administrator
echo.

:: STEP 2: Check if Chocolatey exists
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo 🍫 Installing Chocolatey...
    powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    :: Refresh PATH after Chocolatey install
    call :RefreshPath
    
    :: Verify Chocolatey
    where choco >nul 2>&1
    if %errorLevel% neq 0 (
        echo ❌ Failed to install Chocolatey.
        pause
        exit /b 1
    )
)
echo ✅ Chocolatey ready.
echo.

:: STEP 3: Install required tools (Git, Python, FFmpeg)
echo 📦 Installing Git, Python, and FFmpeg (if missing)...
choco install git python ffmpeg -y --no-progress

:: Refresh PATH to recognize new tools
call :RefreshPath

echo ✅ All base tools installed.
echo.

:: STEP 4: Clone or update project
set "REPO=https://github.com/Tariq990/youtubetb-refactored.git"
set "FOLDER=youtubetb-refactored"

if exist "%FOLDER%\.git" (
    echo 🔄 Updating existing repository...
    cd "%FOLDER%"
    git pull origin master
    if %errorLevel% neq 0 (
        echo ⚠️  Failed to update repository (continuing anyway)
    )
) else (
    echo ⏬ Cloning repository from GitHub...
    git clone "%REPO%"
    if %errorLevel% neq 0 (
        echo ❌ Failed to clone repository.
        pause
        exit /b 1
    )
    cd "%FOLDER%"
)
echo ✅ Repository ready.
echo.

:: STEP 5: Run internal setup (QUICK_FIX.bat - simpler and more reliable)
if not exist "QUICK_FIX.bat" (
    echo ❌ QUICK_FIX.bat not found in project folder.
    pause
    exit /b 1
)

echo 🧩 Running quick setup (dependencies only)...
echo.
call QUICK_FIX.bat

echo.
echo ==========================================================
echo ✅ All steps completed successfully!
echo ==========================================================
echo.
echo 🚀 Next step: Run the program
echo    cd %FOLDER%
echo    run.bat
echo.
pause
exit /b 0

:: ============================================================
:: Helper Function: Refresh Environment PATH
:: ============================================================
:RefreshPath
echo    🔄 Refreshing environment variables...
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
