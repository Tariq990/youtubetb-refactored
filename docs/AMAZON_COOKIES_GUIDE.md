# 🍪 Amazon Cookies Setup Guide

## Why Amazon Cookies?

Amazon cookies are used to:
- Fetch book cover images from Amazon when Google Books API doesn't return results
- Access age-restricted or region-locked book pages
- Improve scraping reliability and avoid bot detection

## Quick Setup (5 minutes)

### Method 1: Browser Extension (Recommended)

1. **Install Cookie Exporter Extension**
   
   Choose one:
   - [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) (Chrome/Edge)
   - [Cookie-Editor](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/) (Firefox)

2. **Login to Amazon**
   - Go to https://www.amazon.com
   - Login with your account (free account works)

3. **Export Cookies**
   - Click the extension icon
   - Choose "Export" → "Netscape format"
   - Save as `amazon_cookies.txt`

4. **Append to Project Cookies**
   ```cmd
   # Open your downloaded amazon_cookies.txt
   # Copy all lines containing "amazon.com"
   # Paste them at the end of: secrets\cookies.txt
   ```

### Method 2: Manual Cookie Extraction

1. **Get Session Cookies**
   - Login to Amazon.com
   - Press F12 (Developer Tools)
   - Go to "Application" tab → "Cookies" → "https://www.amazon.com"

2. **Copy These Important Cookies** (minimum required):
   - `session-id`
   - `session-id-time`
   - `ubid-main`
   - `at-main` (if present)
   - `x-main` (if present)

3. **Format and Add to cookies.txt**
   
   Format (tab-separated):
   ```
   .amazon.com	TRUE	/	FALSE	<expiry>	<cookie_name>	<cookie_value>
   ```
   
   Example:
   ```
   .amazon.com	TRUE	/	FALSE	2147483647	session-id	139-1234567-8901234
   .amazon.com	TRUE	/	FALSE	2147483647	ubid-main	132-9876543-2109876
   ```

4. **Append to secrets\cookies.txt**

## Verify Setup

Run the verification script:
```cmd
python -m scripts.test_all_apis
```

Look for:
```
✅ Amazon cookies: X
```

## Troubleshooting

### "No Amazon cookies found"
- Make sure you copied lines with `.amazon.com` domain
- Check the file format (tab-separated, not spaces)
- Ensure cookies are appended to existing file (don't replace YouTube cookies)

### "Scraping fails with 403/429 errors"
- Your cookies may have expired
- Re-export fresh cookies from a logged-in session
- Try using a different Amazon account

### "Book covers not fetching"
- Amazon cookies are optional fallback
- Google Books API is used first (faster, no login needed)
- Covers will still work without Amazon cookies for most books

## Cookie Expiry

- Amazon cookies typically expire after ~1 year
- Re-export when you see 403/401 errors
- The project will fallback to other sources automatically

## Security Notes

- ⚠️ Never commit `secrets/cookies.txt` to GitHub (already in .gitignore)
- ✅ Cookies are encrypted in `secrets_encrypted/` before pushing
- 🔒 Use the encryption script: `python scripts\encrypt_secrets.py`

## Optional: Amazon Regional Sites

For better results in specific regions, you can add cookies from:
- amazon.co.uk (UK)
- amazon.de (Germany)
- amazon.fr (France)
- amazon.co.jp (Japan)

Same process, just visit the regional site, login, and export cookies.

---

**Last Updated:** October 24, 2025
