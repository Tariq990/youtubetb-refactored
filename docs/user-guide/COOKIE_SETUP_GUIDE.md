# Cookie Setup Guide - YouTubeTB

## 📖 Overview

This guide explains how to set up and manage cookies.txt for YouTube video access, especially for age-restricted or geo-blocked content.

---

## 🎯 Why Do You Need Cookies?

Cookies allow the application to access YouTube videos **as if you're logged in**, which enables:

✅ **Age-restricted videos** - Videos requiring login
✅ **Geo-blocked content** - Region-specific videos
✅ **Private/unlisted videos** - With proper access
✅ **Better reliability** - Fewer rate-limiting issues

**Note:** Cookies are **optional** but **highly recommended** for reliable operation.

---

## 🆕 New Features (2025-01-15)

### Automatic Cookie Testing
- ✅ **Automatic validation** when pipeline starts
- ✅ **Interactive setup wizard** if cookies invalid
- ✅ **Clear error messages** with solutions
- ✅ **Testing with YouTube** to verify cookies work

### Cookie Manager Module
New `cookie_manager.py` provides:
- Content validation (format, size, domains)
- YouTube connectivity test
- Interactive setup guide
- Step-by-step instructions

---

## 🚀 Quick Start

### Automatic Setup (Recommended)

When you run the pipeline, it will **automatically check cookies**:

```bash
python main.py
```

If cookies are missing or invalid:
1. You'll see a warning
2. Option to run setup wizard: `y`
3. Follow on-screen instructions

### Manual Setup

```bash
# Test cookies
python -m src.infrastructure.adapters.cookie_manager

# Interactive setup wizard
python -m src.infrastructure.adapters.cookie_manager setup
```

---

## 📝 Step-by-Step Guide

### Step 1: Install Browser Extension

**Chrome/Edge:**
1. Go to: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid
2. Click "Add to Chrome/Edge"

**Firefox:**
1. Go to: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
2. Click "Add to Firefox"

### Step 2: Login to YouTube

1. Open YouTube.com in your browser
2. **Login to your account** (important!)
3. Watch 1-2 videos to activate session
4. Make sure you're fully logged in

### Step 3: Export Cookies

1. While on YouTube.com, click the extension icon
2. Click "Export" or "Download"
3. Save file as `cookies.txt`
4. **Verify file size** (should be > 1KB)

### Step 4: Place Cookie File

Put `cookies.txt` in **one** of these locations:

```
Option 1 (recommended):
  secrets/cookies.txt

Option 2:
  cookies.txt  (project root)
```

**Example:**
```bash
# Windows
C:\project\secrets\cookies.txt

# Or
C:\project\cookies.txt
```

---

## ✅ Verification

### Automatic Verification (During Pipeline)
```bash
python main.py
```

Output if OK:
```
🍪 Cookies Check
✓ Cookies OK: cookies.txt
```

Output if invalid:
```
🍪 Cookies Check
⚠️  Invalid cookies: [reason]
   Cookies are optional but recommended
   
Do you want to set up cookies now? (y/n):
```

### Manual Verification
```bash
# Quick check
python -m src.infrastructure.adapters.cookie_manager

# Expected output if valid:
[Cookies] Cookies OK: cookies.txt

# Expected output if invalid:
[Cookies] Invalid cookies: [reason]
```

---

## 🔍 Troubleshooting

### Problem 1: "No cookies.txt found"

**Solution:**
- Export cookies from browser
- Place in `secrets/cookies.txt`
- Run setup wizard: `python -m src.infrastructure.adapters.cookie_manager setup`

### Problem 2: "File too small"

**Causes:**
- Empty or corrupted file
- Not exported correctly

**Solution:**
1. Delete existing cookies.txt
2. Re-export from browser
3. Make sure you're logged into YouTube first
4. Verify file is > 1KB

### Problem 3: "Not in Netscape cookie format"

**Causes:**
- Wrong export format
- Wrong extension used

**Solution:**
- Use recommended extension (Get cookies.txt)
- File should start with `# Netscape HTTP Cookie File`

### Problem 4: "No YouTube/Google cookies found"

**Causes:**
- Not logged into YouTube when exported
- Wrong website cookies exported

**Solution:**
1. Login to YouTube.com
2. While on YouTube page, click extension
3. Export and replace cookies.txt

### Problem 5: "Cookies expired or invalid"

**Causes:**
- Cookies older than 30 days
- Session expired
- Different machine/IP

**Solution:**
- Export **fresh** cookies
- Cookies expire after ~30 days
- Must export new on each machine

---

## 📋 Cookie Validation Checks

The system performs these checks:

1. ✅ **File exists** - cookies.txt found
2. ✅ **Not empty** - File has content
3. ✅ **Minimum size** - > 1KB
4. ✅ **Netscape format** - Proper cookie format
5. ✅ **Sufficient cookies** - At least 5 cookie entries
6. ✅ **YouTube domains** - Contains YouTube/Google cookies
7. ✅ **YouTube test** - Actually works with YouTube API

---

## 🔄 When to Update Cookies

### Required Updates:
- ✅ **New machine** - Always export fresh
- ✅ **Monthly** - Cookies expire (~30 days)
- ✅ **After logout** - If you logout from YouTube
- ✅ **IP change** - New location/network

### Update Process:
```bash
# 1. Delete old cookies
rm secrets/cookies.txt

# 2. Export fresh from browser (logged in)
# 3. Place in secrets/cookies.txt

# 4. Verify
python -m src.infrastructure.adapters.cookie_manager
```

---

## 🎯 Best Practices

### DO:
- ✅ Export fresh cookies on each new machine
- ✅ Update cookies monthly
- ✅ Login to YouTube before exporting
- ✅ Watch 1-2 videos before exporting
- ✅ Keep cookies.txt in `secrets/` folder
- ✅ Test cookies after exporting

### DON'T:
- ❌ Copy old cookies to new machine
- ❌ Use cookies older than 30 days
- ❌ Export cookies while logged out
- ❌ Share cookies.txt (contains your session)
- ❌ Commit cookies.txt to git

---

## 🔒 Security Notes

### What cookies.txt Contains:
- Your YouTube session
- Login tokens
- Browser fingerprint
- Preferences

### Security Tips:
- 🔐 **Keep private** - Don't share
- 🔐 **Add to .gitignore** - Already done
- 🔐 **Rotate regularly** - Monthly updates
- 🔐 **Delete if compromised** - Export fresh

---

## 🛠️ Advanced Usage

### Check Cookie Status (Python)
```python
from src.infrastructure.adapters.cookie_manager import check_cookies_status

valid, message = check_cookies_status(verbose=True)
if valid:
    print("Cookies OK!")
else:
    print(f"Issue: {message}")
```

### Interactive Setup (Python)
```python
from src.infrastructure.adapters.cookie_manager import interactive_cookie_setup

success = interactive_cookie_setup()
```

### Find Cookies File (Python)
```python
from src.infrastructure.adapters.cookie_manager import find_cookies_file

cookies_path = find_cookies_file()
if cookies_path:
    print(f"Found: {cookies_path}")
```

---

## 📊 Cookie Manager Features

### File Validation
```python
from src.infrastructure.adapters.cookie_manager import validate_cookies_content
from pathlib import Path

is_valid, message = validate_cookies_content(Path("secrets/cookies.txt"))
print(f"Valid: {is_valid}, Message: {message}")
```

### YouTube Test
```python
from src.infrastructure.adapters.cookie_manager import test_cookies_with_ytdlp
from pathlib import Path

success, message = test_cookies_with_ytdlp(Path("secrets/cookies.txt"))
print(f"Works: {success}, Message: {message}")
```

---

## 🎓 Understanding Cookies

### What Are Cookies?
- Small text files storing session data
- Allow websites to "remember" you
- Contain login tokens and preferences

### Why Machine-Specific?
Cookies contain:
- Browser fingerprint (user agent, screen size, etc.)
- IP address signature
- Session tokens tied to your device

**Result:** Copying cookies to different machine = won't work

### Why Expire?
- Security measure
- Typically expire after 30 days
- Prevents stolen cookies from working forever

---

## 📞 Getting Help

### If Cookies Still Don't Work:

1. **Check TROUBLESHOOTING.md** - Issue #1: Cookies
2. **Run interactive setup**:
   ```bash
   python -m src.infrastructure.adapters.cookie_manager setup
   ```
3. **Verify YouTube login**:
   - Open YouTube.com
   - Make sure you're logged in
   - Try watching a video

4. **Re-export fresh cookies**:
   - Click extension while on YouTube
   - Export and replace

---

## 📖 Related Documentation

- **TROUBLESHOOTING.md** - Common issues and solutions
- **WINDOWS_SETUP.md** - Complete setup guide
- **README.md** - Project overview

---

## ✅ Quick Reference

```bash
# Check cookies
python -m src.infrastructure.adapters.cookie_manager

# Interactive setup
python -m src.infrastructure.adapters.cookie_manager setup

# Test in pipeline (automatic)
python main.py
```

**Cookie Locations:**
```
secrets/cookies.txt (recommended)
cookies.txt (alternative)
```

**File Requirements:**
- Format: Netscape HTTP Cookie File
- Size: > 1KB
- Content: YouTube/Google cookies
- Age: < 30 days

---

**Last Updated:** 2025-01-15
**Module:** `src/infrastructure/adapters/cookie_manager.py`
**Status:** ✅ Fully Implemented & Tested
