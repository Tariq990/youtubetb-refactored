# ==============================================
# YouTubeTB - Complete Windows Setup Script
# ==============================================
# This script installs all dependencies and sets up the project

$ErrorActionPreference = 'Stop'

function Write-Info($message) {
    Write-Host "`n✓ $message" -ForegroundColor Green
}

function Write-Warning-Custom($message) {
    Write-Host "`n⚠ $message" -ForegroundColor Yellow
}

function Write-Error-Custom($message) {
    Write-Host "`n✗ $message" -ForegroundColor Red
}

function Write-Step($number, $total, $message) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "[$number/$total] $message" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

Write-Host @"

╔═══════════════════════════════════════════════╗
║   YouTubeTB - Complete Windows Setup         ║
║   Comprehensive Installation Script           ║
╚═══════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# ============================================
# Step 1: Check Python Installation
# ============================================
Write-Step 1 8 "Checking Python Installation"

try {
    $pythonVersion = python --version 2>&1
    Write-Info "Python found: $pythonVersion"
    
    # Check if Python version is 3.10+
    $versionMatch = $pythonVersion -match 'Python (\d+)\.(\d+)'
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Error-Custom "Python 3.10+ required. Current version: $pythonVersion"
            Write-Host "Download from: https://www.python.org/downloads/"
            exit 1
        }
    }
} catch {
    Write-Error-Custom "Python not found in PATH"
    Write-Host @"
Please install Python 3.10 or higher:
1. Download from: https://www.python.org/downloads/
2. During installation, check 'Add Python to PATH'
3. Restart PowerShell and run this script again
"@
    exit 1
}

# ============================================
# Step 2: Check FFmpeg Installation
# ============================================
Write-Step 2 8 "Checking FFmpeg Installation"

try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Info "FFmpeg found: $ffmpegVersion"
} catch {
    Write-Warning-Custom "FFmpeg not found in PATH"
    Write-Host @"
FFmpeg is required for video processing!

Installation options:
1. Using Chocolatey (recommended):
   choco install ffmpeg

2. Manual installation:
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract to C:\ffmpeg
   - Add C:\ffmpeg\bin to System PATH
   - Restart PowerShell

"@
    $continue = Read-Host "Continue without FFmpeg? (video processing will fail) [y/N]"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
}

# ============================================
# Step 3: Create Virtual Environment
# ============================================
Write-Step 3 8 "Setting Up Virtual Environment"

if (Test-Path "venv") {
    Write-Warning-Custom "Virtual environment already exists"
    $recreate = Read-Host "Recreate virtual environment? This will delete existing venv [y/N]"
    if ($recreate -eq 'y' -or $recreate -eq 'Y') {
        Remove-Item -Recurse -Force "venv"
        Write-Info "Deleted existing virtual environment"
    }
}

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to create virtual environment"
        exit 1
    }
    Write-Info "Virtual environment created successfully"
} else {
    Write-Info "Using existing virtual environment"
}

# ============================================
# Step 4: Upgrade pip
# ============================================
Write-Step 4 8 "Upgrading pip"

.\venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Warning-Custom "Failed to upgrade pip, continuing anyway"
}
Write-Info "pip upgraded successfully"

# ============================================
# Step 5: Install Python Dependencies
# ============================================
Write-Step 5 8 "Installing Python Dependencies"

Write-Host "This may take several minutes..."
.\venv\Scripts\pip.exe install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to install dependencies"
    Write-Host @"
    
Try manual installation:
1. Activate virtual environment: .\venv\Scripts\activate
2. Install requirements: pip install -r requirements.txt
3. Check for errors and install missing packages manually

"@
    exit 1
}
Write-Info "Python dependencies installed successfully"

# ============================================
# Step 6: Install Playwright Browsers
# ============================================
Write-Step 6 8 "Installing Playwright Chromium Browser"

Write-Host "Installing Chromium browser for web scraping..."
.\venv\Scripts\python.exe -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Warning-Custom "Failed to install Playwright browsers"
    Write-Host @"
    
You can install it manually later:
.\venv\Scripts\activate
python -m playwright install chromium

"@
} else {
    Write-Info "Playwright Chromium browser installed successfully"
}

# Also install dependencies for Playwright
Write-Host "Installing Playwright system dependencies..."
.\venv\Scripts\python.exe -m playwright install-deps chromium 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Info "Playwright system dependencies installed"
} else {
    Write-Warning-Custom "Some Playwright dependencies may be missing (this is usually OK on Windows)"
}

# ============================================
# Step 7: Setup Environment File
# ============================================
Write-Step 7 8 "Setting Up Environment Configuration"

if (Test-Path ".env") {
    Write-Warning-Custom ".env file already exists"
    $overwrite = Read-Host "Overwrite with template? This will erase your API keys [y/N]"
    if ($overwrite -eq 'y' -or $overwrite -eq 'Y') {
        Copy-Item ".env.example" ".env" -Force
        Write-Info ".env file recreated from template"
    } else {
        Write-Info "Keeping existing .env file"
    }
} else {
    Copy-Item ".env.example" ".env"
    Write-Info ".env file created from template"
}

# ============================================
# Step 8: Create Required Directories
# ============================================
Write-Step 8 8 "Creating Required Directories"

$requiredDirs = @(
    "secrets",
    "config",
    "runs",
    "tmp"
)

foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Info "Created directory: $dir"
    } else {
        Write-Info "Directory exists: $dir"
    }
}

# ============================================
# Final Instructions
# ============================================
Write-Host @"

╔═══════════════════════════════════════════════╗
║   Setup Completed Successfully! ✓             ║
╚═══════════════════════════════════════════════╝

📋 Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Configure API Keys:
   • Edit .env file and add your API keys:
     - YT_API_KEY         (YouTube Data API v3)
     - GEMINI_API_KEY     (Google Gemini AI)
     - ELEVENLABS_API_KEY (ElevenLabs TTS)

2️⃣  Setup YouTube OAuth (for video upload):
   • Download client_secret.json from Google Cloud Console
   • Place it in: secrets\client_secret.json

3️⃣  Setup Cookies (optional, for age-restricted videos):
   • Export cookies.txt from browser using extension
   • Place it in: secrets\cookies.txt

4️⃣  Activate Virtual Environment:
   • Run: .\venv\Scripts\activate

5️⃣  Run the Application:
   • Run: python main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Documentation:
   • README.md              - Project overview
   • YOUTUBE_SYNC_QUICKSTART.md - Quick start guide
   • docs\                  - Full documentation

🔧 Troubleshooting:
   • If FFmpeg is missing: choco install ffmpeg
   • If Playwright fails: python -m playwright install chromium
   • Check API keys in .env file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@ -ForegroundColor Green

# Optional: Run API check
Write-Host "`nDo you want to verify your API keys now? [y/N]: " -NoNewline -ForegroundColor Yellow
$checkApis = Read-Host
if ($checkApis -eq 'y' -or $checkApis -eq 'Y') {
    Write-Host "`nRunning API validation..." -ForegroundColor Cyan
    .\venv\Scripts\python.exe -m src.presentation.cli.check_apis
}

Write-Host "`nSetup complete! 🎉`n" -ForegroundColor Green
