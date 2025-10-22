# 🍪 Cookies Setup Guide

## Overview
YouTubeTB requires browser cookies from **YouTube** and **Amazon** to:
- Download age-restricted or private YouTube videos (via yt-dlp)
- Fetch book cover images from Amazon

## ✅ Required Cookies
You need cookies from **both** websites in a **single file**:
- `secrets/cookies.txt` (Netscape HTTP Cookie File format)

## 📥 How to Extract Cookies

### Method: Browser Extension (Recommended)

#### Step 1: Install Extension
Install **"Get cookies.txt LOCALLY"** extension:
- **Chrome Web Store**: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Works on: Chrome, Brave, Edge, and other Chromium browsers

#### Step 2: Login to Required Sites
1. Open **YouTube** (https://www.youtube.com)
   - Make sure you're logged in
   - Verify you see your profile picture

2. Open **Amazon** (https://www.amazon.com)
   - Make sure you're logged in
   - Verify you see "Hello, [Your Name]"

#### Step 3: Export YouTube Cookies
1. While on YouTube.com, click the extension icon 🍪
2. Click **"Export"** or **"Current Site"**
3. Save as `www.youtube.com_cookies.txt`

#### Step 4: Export Amazon Cookies
1. Navigate to Amazon.com
2. Click the extension icon 🍪 again
3. Click **"Export"** or **"Current Site"**
4. Save as `www.amazon.com_cookies.txt`

#### Step 5: Merge Cookie Files
You must combine both files into one:

**Windows (PowerShell):**
```powershell
Get-Content www.youtube.com_cookies.txt, www.amazon.com_cookies.txt | Set-Content secrets\cookies.txt
```

**Windows (Command Prompt):**
```cmd
copy /b www.youtube.com_cookies.txt+www.amazon.com_cookies.txt secrets\cookies.txt
```

**Linux/Mac:**
```bash
cat www.youtube.com_cookies.txt www.amazon.com_cookies.txt > secrets/cookies.txt
```

#### Step 6: Verify Cookies
Run the validation tool:
```bash
python -m src.infrastructure.adapters.cookie_manager
```

**Expected output:**
```
[Cookies] Cookies OK: cookies.txt
```

If you see errors, check:
- File is in `secrets/cookies.txt` (not root directory)
- File size is > 1KB (should contain actual cookie data)
- Both YouTube and Amazon domains are present

## 📋 Cookie File Format

The final `secrets/cookies.txt` should look like:
```
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html

.youtube.com	TRUE	/	TRUE	1776726098	PREF	f4=4000000...
.youtube.com	TRUE	/	TRUE	0	YSC	5ALO_MdHLK0
.youtube.com	TRUE	/	TRUE	1776726095	VISITOR_INFO1_LIVE	FbjKyHlsASM
...
.amazon.com	TRUE	/	TRUE	1776725644	session-id	140-2105984-8480100
.amazon.com	TRUE	/	TRUE	1776725644	session-id-time	2082787201l
.amazon.com	TRUE	/	TRUE	1776725654	ubid-main	131-1561947-7215657
...
```

**Important:** Each cookie line has **7 tab-separated fields**:
1. Domain
2. Flag (TRUE/FALSE)
3. Path
4. Secure (TRUE/FALSE)
5. Expiration (Unix timestamp)
6. Name
7. Value

## 🔧 Troubleshooting

### Error: "File too small"
- **Cause**: Cookie file is incomplete or empty
- **Solution**: Re-export cookies and ensure you're logged in to both sites

### Error: "May not contain YouTube cookies"
- **Cause**: Only Amazon cookies were exported
- **Solution**: Export YouTube cookies separately and merge both files

### Error: "yt-dlp failed to download"
- **Cause**: Cookies are expired or invalid
- **Solution**: 
  1. Logout and login again to YouTube
  2. Re-export fresh cookies
  3. Replace `secrets/cookies.txt`

### Cookies Expire Too Soon
- **Tip**: Most cookies last 1-2 weeks
- **Solution**: Re-export cookies when pipeline fails
- **Automation**: You can schedule cookie refresh weekly

## 🔒 Security Notes

1. **Never commit cookies to Git**
   - Already in `.gitignore` as `secrets/`
   - Contains sensitive session data

2. **Keep cookies private**
   - Anyone with your cookies can impersonate you
   - Don't share cookie files publicly

3. **Refresh regularly**
   - Cookies expire (usually 1-2 weeks)
   - Pipeline will fail when cookies expire

## 🚀 Quick Start (Complete Workflow)

```bash
# 1. Install extension (one-time setup)
# Visit: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

# 2. Login to both sites
# - https://www.youtube.com
# - https://www.amazon.com

# 3. Export cookies from YouTube
# Click extension → Export → Save as www.youtube.com_cookies.txt

# 4. Export cookies from Amazon
# Click extension → Export → Save as www.amazon.com_cookies.txt

# 5. Merge files
Get-Content www.youtube.com_cookies.txt, www.amazon.com_cookies.txt | Set-Content secrets\cookies.txt

# 6. Verify
python -m src.infrastructure.adapters.cookie_manager

# 7. Run pipeline
python main.py
```

## 📚 Related Documentation

- **Main README**: `README.md`
- **Quick Start**: `docs/QUICK_START.md`
- **Pipeline Guide**: `docs/user-guide/PIPELINE_STOP_ON_ERROR.md`

## ❓ FAQ

**Q: Can I use cookies from different browsers?**
A: Yes, but they must be from the same logged-in account on both sites.

**Q: Do I need to be logged in to Amazon.sa or Amazon.com?**
A: Amazon.com is recommended (English book covers). Amazon.sa works but has fewer books.

**Q: How often should I refresh cookies?**
A: When you see "yt-dlp failed" or "403 Forbidden" errors, refresh cookies.

**Q: Can I automate cookie extraction?**
A: The extension method is manual. Automated extraction requires browser automation (Selenium/Playwright) which is complex and fragile.

## 🆘 Still Having Issues?

If cookies still don't work:
1. Check you're logged in (see your profile picture/name)
2. Try incognito/private window logout → fresh login
3. Use a different browser (Chrome, Edge, Firefox)
4. Ensure extension is updated to latest version
5. Check browser console for extension errors

---

**Last Updated**: October 23, 2025
**Extension Link**: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
