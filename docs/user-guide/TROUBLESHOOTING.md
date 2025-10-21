# YouTubeTB - Troubleshooting Guide

## Common Issues and Solutions

---

## 🍪 Issue 1: Cookies File Not Working

### Problem
When running on a different machine, cookies.txt doesn't work and YouTube requests login.

### Root Cause
- Cookies are machine/browser-specific and contain session information
- Cookies expire after some time
- Different IP address or browser signature causes YouTube to reject cookies

### Solution

#### Step 1: Re-export Cookies
1. **Install Browser Extension**
   - Chrome: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Login to YouTube**
   - Open YouTube in browser
   - Login to your account
   - Watch a few videos to ensure cookies are active

3. **Export Fresh Cookies**
   - Click extension icon on YouTube page
   - Click "Export" or "Download"
   - Save as `cookies.txt`

4. **Place in Correct Location**
   ```
   Option 1: secrets/cookies.txt (recommended)
   Option 2: cookies.txt (project root)
   ```

#### Step 2: Verify Cookies Format
- Open `cookies.txt` in notepad
- Should start with: `# Netscape HTTP Cookie File`
- Should contain many lines with YouTube domains
- File should be at least 10KB in size

#### Step 3: Test
```bash
python -m src.infrastructure.adapters.transcribe https://youtube.com/watch?v=VIDEO_ID
```

### Prevention
- **Re-export cookies on each new machine**
- **Update cookies monthly** (they expire)
- **Keep browser logged in** before exporting

---

## 📚 Issue 2: Amazon Book Cover Not Found

### Problem
Book cover fetching from Amazon fails with 403/503 errors or returns no results.

### Root Cause
- Amazon blocks automated requests (bot detection)
- Rate limiting when making too many requests
- Changed HTML structure

### Solution

#### Method 1: Use Playwright (Recommended - Already Implemented)
The new `amazon_cover.py` module uses Playwright for better reliability:

```python
# Already integrated in process.py
# Automatically uses Playwright first, then falls back to requests
```

**Verify Playwright is installed:**
```bash
.\venv\Scripts\activate
python -m playwright install chromium
```

#### Method 2: Manual Cover Upload
If automated fetching fails:

1. **Download Cover Manually**
   - Go to Amazon: https://www.amazon.com
   - Search for book: "BOOK_TITLE by AUTHOR"
   - Right-click on cover → "Save Image As..."
   - Save as high quality (look for larger versions)

2. **Place in Run Directory**
   ```
   runs/YOUR_BOOK_NAME/bookcover.jpg
   ```

3. **Supported Names**
   - `bookcover.jpg` (preferred)
   - `bookcover.jpeg`
   - `bookcover.png`

#### Method 3: Use Alternative Source
Edit `process.py` to try other sources:
- Google Books API
- Open Library
- Goodreads (requires scraping)

### Verification
```bash
# Test cover fetch
python -c "from src.infrastructure.adapters.amazon_cover import get_book_cover_from_amazon; print(get_book_cover_from_amazon('Atomic Habits', 'James Clear'))"
```

---

## 🗄️ Issue 3: YouTube Database Sync Failed

### Problem
Database.json remains empty, can't sync from YouTube channel.

### Root Cause
- Missing YouTube API key
- Missing or incorrect Channel ID
- API quota exceeded
- Missing google-api-python-client package

### Solution

#### Step 1: Setup YouTube API Key

1. **Get API Key from Google Cloud Console**
   - Go to: https://console.cloud.google.com
   - Create new project or select existing
   - Enable "YouTube Data API v3"
   - Create credentials → API Key
   - Copy the API key

2. **Add to Environment**
   ```bash
   # Option 1: .env file (recommended)
   YT_API_KEY=your_api_key_here
   
   # Option 2: secrets/api_key.txt
   echo "your_api_key_here" > secrets/api_key.txt
   
   # Option 3: Environment variable
   set YOUTUBE_API_KEY=your_api_key_here
   ```

#### Step 2: Configure Channel ID

1. **Find Your Channel ID**
   - Go to YouTube Studio
   - Settings → Channel → Advanced settings
   - Copy "Channel ID" (starts with UC...)

2. **Add to Config**
   Edit `config/settings.json`:
   ```json
   {
     "youtube_sync": {
       "enabled": true,
       "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxxxxx"
     }
   }
   ```

#### Step 3: Install Required Package
```bash
.\venv\Scripts\activate
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

#### Step 4: Test Sync
```bash
python -m src.infrastructure.adapters.database sync
```

### Manual Database Entry
If sync fails, manually add books to `database.json`:

```json
{
  "books": [
    {
      "book_name": "Atomic Habits",
      "author_name": "James Clear",
      "status": "done",
      "youtube_url": "https://youtube.com/watch?v=VIDEO_ID",
      "playlist": "Self-Development",
      "added_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## 📤 Issue 4: YouTube Upload Failed

### Problem
Video upload to YouTube fails with authentication errors.

### Root Cause
- Missing `client_secret.json`
- Expired or invalid `token.json`
- Incorrect OAuth scopes
- API quota exceeded

### Solution

#### Step 1: Setup OAuth Credentials

1. **Get OAuth Client**
   - Go to: https://console.cloud.google.com
   - APIs & Services → Credentials
   - Create OAuth 2.0 Client ID
   - Application type: "Desktop app"
   - Download JSON file

2. **Rename and Place**
   ```bash
   # Rename downloaded file to:
   secrets/client_secret.json
   ```

#### Step 2: First-Time Authentication
```bash
.\venv\Scripts\activate
python -m src.infrastructure.adapters.youtube_upload --run runs/YOUR_BOOK
```

- Browser will open automatically
- Login to YouTube account
- Grant permissions
- `token.json` will be created automatically

#### Step 3: Verify Upload Permissions
The OAuth client needs these scopes:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

#### Step 4: Re-authenticate if Needed
If upload still fails:
```bash
# Delete old token
del secrets\token.json

# Re-run upload (will prompt for login again)
python -m src.infrastructure.adapters.youtube_upload --run runs/YOUR_BOOK
```

---

## 🔧 Issue 5: FFmpeg Not Found

### Problem
Video rendering fails with "FFmpeg not found" error.

### Solution

#### Windows

**Option 1: Chocolatey (Recommended)**
```powershell
# Install Chocolatey first (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

**Option 2: Manual Installation**
1. Download: https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\ffmpeg\bin`
   - Restart terminal

**Verify Installation:**
```bash
ffmpeg -version
```

---

## 🐍 Issue 6: Python Package Import Errors

### Problem
`ModuleNotFoundError` or `ImportError` for various packages.

### Solution

#### Verify Virtual Environment
```bash
# Activate venv
.\venv\Scripts\activate

# Check if in venv (should show path to venv)
where python

# Reinstall all requirements
pip install -r requirements.txt --upgrade
```

#### Install Missing Packages
```bash
# Core packages
pip install python-dotenv pydantic google-generativeai

# YouTube packages
pip install google-api-python-client google-auth-oauthlib yt-dlp youtube-transcript-api

# TTS packages
pip install elevenlabs edge-tts

# Media processing
pip install Pillow moviepy pydub ffmpeg-python mutagen

# Web scraping
pip install beautifulsoup4 playwright requests

# Playwright browsers
python -m playwright install chromium
```

---

## ⚙️ Issue 7: Playwright Browser Errors

### Problem
"Browser executable not found" or "Playwright not installed" errors.

### Solution

```bash
.\venv\Scripts\activate

# Install Playwright
pip install playwright

# Install Chromium browser
python -m playwright install chromium

# If still fails, install all dependencies
python -m playwright install-deps chromium
```

---

## 🔑 Issue 8: API Keys Not Working

### Problem
"Invalid API key" or "API key not found" errors.

### Solution

#### Verify .env File
1. Check `.env` file exists in project root
2. Verify format (no spaces around =):
   ```
   YT_API_KEY=your_key_here
   GEMINI_API_KEY=your_key_here
   ELEVENLABS_API_KEY=your_key_here
   ```

#### Test API Keys
```bash
python -m src.presentation.cli.check_apis
```

#### Common Issues
- **Extra spaces**: Remove spaces before/after keys
- **Quotes**: Don't use quotes around keys
- **File encoding**: Save as UTF-8 without BOM
- **Line endings**: Use Unix (LF) or Windows (CRLF)

---

## 📝 Issue 9: Settings.json Not Found

### Problem
"Config file not found" errors.

### Solution

1. **Create Missing Directories**
   ```bash
   mkdir config
   mkdir secrets
   mkdir runs
   mkdir tmp
   ```

2. **Create Default Settings**
   Create `config/settings.json`:
   ```json
   {
     "tts_provider": "edge",
     "voice": "en-US-GuyNeural",
     "prefer_local_cover": true,
     "amazon_affiliate_enabled": false,
     "youtube_sync": {
       "enabled": true,
       "channel_id": ""
     }
   }
   ```

---

## 🚨 Issue 10: General Debugging

### Enable Verbose Output
```bash
# Set debug environment variable
set DEBUG=1

# Run with verbose output
python main.py
```

### Check System Requirements
```bash
python --version    # Should be 3.10+
ffmpeg -version    # Should be installed
pip list           # Check installed packages
```

### Reset Everything
```bash
# Delete virtual environment
rmdir /s /q venv

# Delete cached files
rmdir /s /q __pycache__
del /s /q *.pyc

# Re-run setup
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

---

## 📞 Getting Help

### Before Reporting Issues

1. **Check this guide** for your specific error
2. **Read error messages** carefully - they often contain the solution
3. **Verify all requirements** are installed correctly
4. **Test with simple example** first

### Where to Get Help

1. **Project Documentation**
   - README.md
   - YOUTUBE_SYNC_QUICKSTART.md
   - SECRETS_ENCRYPTION.md

2. **Check Logs**
   - Look in `runs/YOUR_BOOK/` for error logs
   - Check `tmp/` directory for temporary files

3. **Report Issues**
   Include:
   - Full error message
   - Steps to reproduce
   - Python version
   - OS version
   - What you've tried already

---

## 🎯 Quick Fixes Checklist

Before troubleshooting, try these:

- [ ] Activate virtual environment: `.\venv\Scripts\activate`
- [ ] Update pip: `python -m pip install --upgrade pip`
- [ ] Reinstall requirements: `pip install -r requirements.txt`
- [ ] Check .env file exists and has correct keys
- [ ] Verify FFmpeg is installed: `ffmpeg -version`
- [ ] Check internet connection
- [ ] Verify API keys are valid
- [ ] Restart terminal/PowerShell
- [ ] Check disk space (video rendering needs space)
- [ ] Run as administrator if permission errors

---

## 📖 Additional Resources

### API Key Setup Guides
- [YouTube Data API](https://developers.google.com/youtube/v3/getting-started)
- [Google Gemini API](https://ai.google.dev/)
- [ElevenLabs API](https://docs.elevenlabs.io/api-reference/quick-start)

### Tools
- [Get cookies.txt Extension](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
- [FFmpeg Download](https://www.gyan.dev/ffmpeg/builds/)
- [Python Download](https://www.python.org/downloads/)

### Community
- Check project GitHub issues
- Read existing documentation
- Review CHANGELOG files

---

**Last Updated:** 2025-01-15
**Version:** 1.0
