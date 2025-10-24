# 🚀 YouTubeTB - Quick Setup Guide

## للمستخدمين العرب / For Arabic Users

**دليل التثبيت الكامل بالعربي:** [`docs/arabic/دليل_التثبيت_الشامل.md`](docs/arabic/دليل_التثبيت_الشامل.md)

---

## ⚡ Quick Installation (Windows)

### One-Click Complete Setup:

```batch
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/youtubetb-refactored.git
cd youtubetb-refactored

# 2. Run complete installation (as Administrator)
install_complete.bat
```

**This will automatically:**
- ✅ Install Python 3.11+ (if needed)
- ✅ Install FFmpeg
- ✅ Add both to Windows PATH
- ✅ Create virtual environment
- ✅ Install all Python dependencies
- ✅ Install Playwright browsers
- ✅ Decrypt secrets (you'll be asked for password)
- ✅ Verify installation

**Total time:** ~5-10 minutes (depending on internet speed)

---

## 🔐 Secrets Management

### First Time (Setting Up Encryption):

```batch
# 1. Create your secrets in secrets/ folder:
secrets/
├── api_key.txt          # Your Gemini API key
├── cookies.txt          # YouTube cookies
├── client_secret.json   # YouTube OAuth
└── token.json           # YouTube token

# 2. Encrypt them for GitHub:
python scripts\encrypt_secrets.py
# Enter a strong password (remember it!)

# 3. Push to GitHub (encrypted files only):
git add secrets_encrypted/
git commit -m "Add encrypted secrets"
git push
```

### On New Machine:

```batch
# The install_complete.bat will ask to decrypt automatically
# Or run manually:
python scripts\decrypt_secrets.py
# Enter the same password you used for encryption
```

---

## 📦 What Gets Installed?

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Main language |
| FFmpeg | Latest | Video processing |
| Playwright | Latest | Web scraping |
| Dependencies | See requirements.txt | All Python packages |

---

## 🎯 Quick Start After Installation

```batch
# Activate virtual environment
venv\Scripts\activate

# Run the program
python main.py

# Follow the interactive menu
```

---

## 📚 Documentation

- **Complete Arabic Guide:** [`docs/arabic/دليل_التثبيت_الشامل.md`](docs/arabic/دليل_التثبيت_الشامل.md)
- **Quick Start:** [`docs/QUICK_START.md`](docs/QUICK_START.md)
- **Troubleshooting:** [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
- **Cookies Setup:** [`docs/COOKIES_SETUP.md`](docs/COOKIES_SETUP.md)

---

## ⚠️ Requirements

- Windows 10/11
- Administrator rights
- Internet connection
- Encryption password (for secrets)

---

## 🛠️ Manual Installation

If you prefer manual control:

### 1. Install Python 3.11+
Download from: https://www.python.org/downloads/
- ☑️ Add Python to PATH
- ☑️ Install pip

### 2. Install FFmpeg
Download from: https://www.gyan.dev/ffmpeg/builds/
- Extract to `C:\ffmpeg`
- Add `C:\ffmpeg\bin` to PATH

### 3. Install Dependencies
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 4. Decrypt Secrets
```batch
python scripts\decrypt_secrets.py
```

### 5. Run
```batch
python main.py
```

---

## 🔄 Workflow Summary

### On Development Machine:
```
Work → Update secrets → Encrypt → Push to GitHub
```

### On New/Production Machine:
```
Clone → Run install_complete.bat → Enter password → Ready!
```

---

## ✨ Features

- 🎥 Automated YouTube video generation
- 📚 Book summary processing (Arabic → English)
- 🗣️ AI-powered voice narration
- 🎨 Dynamic thumbnail generation
- 📤 Automatic YouTube upload
- ✂️ Shorts generation
- 🔐 Secure secrets encryption

---

## 📞 Support

For issues:
1. Check `docs/TROUBLESHOOTING.md`
2. Review `runs/*/pipeline.log`
3. Run `python scripts/test_all_apis.py`

---

**Created:** October 24, 2025  
**License:** See LICENSE file
