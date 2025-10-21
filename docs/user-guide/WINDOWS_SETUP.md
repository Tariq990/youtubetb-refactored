# YouTubeTB - Windows Setup Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Windows 10/11
- Python 3.10+ ([Download](https://www.python.org/downloads/))
- FFmpeg ([Installation Guide](#installing-ffmpeg))
- Internet connection

---

## 📦 Installation

### Step 1: Run Automated Setup

Open PowerShell in project directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

This script will:
- ✅ Check Python installation
- ✅ Check FFmpeg installation
- ✅ Create virtual environment
- ✅ Install all Python packages
- ✅ Install Playwright browser
- ✅ Setup `.env` file
- ✅ Create required directories

---

## 🔑 Step 2: Configure API Keys

### Required API Keys

Edit `.env` file and add your API keys:

```env
# YouTube API (for metadata and database sync)
YT_API_KEY=your_youtube_api_key_here

# Google Gemini AI (for content generation)
GEMINI_API_KEY=your_gemini_api_key_here

# ElevenLabs (for high-quality TTS - optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### How to Get API Keys

#### 1. YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Copy and paste into `.env`

#### 2. Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy and paste into `.env`

#### 3. ElevenLabs (Optional)
1. Sign up at [ElevenLabs](https://elevenlabs.io)
2. Go to Profile → API Keys
3. Copy and paste into `.env`

**Alternative:** Use free Edge TTS (no API key needed, set in config)

---

## 🎬 Step 3: YouTube OAuth (For Video Upload)

### Setup OAuth Credentials

1. **Create OAuth Client**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - APIs & Services → Credentials
   - Create OAuth 2.0 Client ID
   - Application type: "Desktop app"
   - Download JSON file

2. **Place in Project**
   ```
   secrets/client_secret.json
   ```

3. **First Upload**
   - Browser will open automatically
   - Login and grant permissions
   - `token.json` created (reusable)

---

## 🍪 Step 4: Cookies Setup (Optional)

For age-restricted or geo-blocked videos:

### Export Cookies

1. **Install Browser Extension**
   - [Chrome: Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - [Firefox: cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export from YouTube**
   - Login to YouTube
   - Visit any video
   - Click extension icon → Export
   - Save file

3. **Place in Project**
   ```
   secrets/cookies.txt
   ```

---

## ⚙️ Installing FFmpeg

### Method 1: Chocolatey (Recommended)

```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

### Method 2: Manual Installation

1. Download: https://www.gyan.dev/ffmpeg/builds/
2. Extract to: `C:\ffmpeg`
3. Add to PATH:
   - Windows Search → "Environment Variables"
   - Edit "Path" variable
   - Add: `C:\ffmpeg\bin`
   - Click OK
4. Restart PowerShell

### Verify Installation
```powershell
ffmpeg -version
```

---

## 🎯 Usage

### Activate Virtual Environment
**Always run this first:**
```powershell
.\venv\Scripts\activate
```

### Run the Application
```powershell
python main.py
```

### Interactive Menu Options

1. **Process Single Book** - Full pipeline for one book
2. **Batch Process** - Process multiple books from file
3. **Resume Failed Run** - Continue from where it stopped
4. **Generate Short** - Create YouTube Short from video
5. **Generate Thumbnail** - Create custom thumbnail
6. **Check APIs** - Verify all API keys
7. **Sync Database** - Update from YouTube channel
8. And more...

---

## 📁 Project Structure

```
youtubetb_refactored/
├── .env                    # API keys (YOU MUST EDIT)
├── .env.example           # Template
├── setup_windows.ps1      # Automated setup script
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
├── TROUBLESHOOTING.md     # Solutions to common issues
├── secrets/               # Private credentials
│   ├── client_secret.json # YouTube OAuth (required for upload)
│   ├── token.json         # Auto-generated after first login
│   ├── cookies.txt        # Browser cookies (optional)
│   └── api_key.txt        # Alternative to .env
├── config/                # Configuration files
│   └── settings.json      # App settings
├── runs/                  # Output directory
│   └── BOOK_NAME/         # Each book gets its own folder
│       ├── output.mp4     # Final video
│       ├── output.titles.json
│       ├── bookcover.jpg
│       └── ...
├── src/                   # Source code
└── venv/                  # Virtual environment
```

---

## 🔍 Quick Verification

### Check Installation
```powershell
# Activate venv
.\venv\Scripts\activate

# Check Python packages
pip list

# Check APIs
python -m src.presentation.cli.check_apis

# Check FFmpeg
ffmpeg -version

# Check Playwright
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

---

## 🛠️ Common Commands

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run main application
python main.py

# Process specific book
python main.py --book "Atomic Habits"

# Batch process from file
python main.py --batch books.txt

# Check API status
python -m src.presentation.cli.check_apis

# Sync database from YouTube
python -m src.infrastructure.adapters.database sync

# Generate thumbnail for existing video
python -m src.infrastructure.adapters.thumbnail --run runs/YOUR_BOOK

# Upload video manually
python -m src.infrastructure.adapters.youtube_upload --run runs/YOUR_BOOK
```

---

## ⚠️ Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.10+ and check "Add Python to PATH" during installation

### Issue: "FFmpeg not found"
**Solution:** Follow [Installing FFmpeg](#installing-ffmpeg) section

### Issue: "Module not found"
**Solution:** 
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Cookies not working"
**Solution:** Re-export cookies from browser (they expire)

### Issue: "Amazon cover failed"
**Solution:** Check `TROUBLESHOOTING.md` - Playwright-based solution implemented

### Issue: "Database sync failed"
**Solution:** Verify YouTube API key and Channel ID in config

**For more issues:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📚 Next Steps

After setup:

1. **Configure Settings** - Edit `config/settings.json` for your preferences
2. **Test with One Book** - Process a simple book first
3. **Setup Batch Processing** - Create `books.txt` with your book list
4. **Explore Features** - Check interactive menu for all options

---

## 📖 Documentation

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions to common issues
- **[README.md](README.md)** - Full project documentation
- **[YOUTUBE_SYNC_QUICKSTART.md](YOUTUBE_SYNC_QUICKSTART.md)** - YouTube integration
- **[SECRETS_ENCRYPTION.md](SECRETS_ENCRYPTION.md)** - Security features
- **[REFACTORING_CHANGELOG.md](REFACTORING_CHANGELOG.md)** - Recent improvements

---

## 🎓 Tutorial: First Book Processing

### Step-by-Step Example

1. **Activate Environment**
   ```powershell
   .\venv\Scripts\activate
   ```

2. **Run Application**
   ```powershell
   python main.py
   ```

3. **Select Option 1** - Process Single Book

4. **Enter Book Details**
   ```
   Book name: Atomic Habits
   Author: James Clear
   ```

5. **Wait for Processing**
   - Stage 1-4: Content generation (5-10 min)
   - Stage 5-7: Voice and audio (5-10 min)
   - Stage 8-9: Video rendering (10-20 min)
   - Stage 10: YouTube upload (5 min)

6. **Check Output**
   ```
   runs/Atomic_Habits_James_Clear/output.mp4
   ```

---

## ⚡ Performance Tips

### Speed Up Processing
- **Use Edge TTS** (free, faster than ElevenLabs)
- **Batch process overnight** for multiple books
- **SSD recommended** for video rendering
- **Close heavy applications** during rendering

### Save API Quota
- **Test with short books** first
- **Use resume feature** if pipeline fails
- **Cache covers locally** (prefer_local_cover: true)

---

## 🔒 Security Notes

- **Never commit `.env`** to git
- **Keep `secrets/` folder private**
- **Don't share `token.json`** (contains your YouTube access)
- **Rotate API keys** regularly
- **Use `.gitignore`** properly

---

## 🆘 Getting Help

1. **Read error messages** carefully
2. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
3. **Verify all requirements** installed
4. **Test with simple example** first
5. **Check project issues** on GitHub

---

## ✅ Setup Checklist

- [ ] Python 3.10+ installed
- [ ] FFmpeg installed and in PATH
- [ ] Virtual environment created (`venv` folder exists)
- [ ] All packages installed (`pip list` shows packages)
- [ ] Playwright browser installed
- [ ] `.env` file exists with API keys
- [ ] `secrets/client_secret.json` for YouTube upload
- [ ] `config/settings.json` configured
- [ ] Tested with `python -m src.presentation.cli.check_apis`

---

**Ready to Start!** 🎉

Run: `python main.py`

---

**Need Help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
