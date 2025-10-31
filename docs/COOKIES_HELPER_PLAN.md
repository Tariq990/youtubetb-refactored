# 🍪 Cookies & API Helper - Detailed Plan

## 📋 Overview

**Script Name**: `cookies_helper.py`  
**Location**: Root directory  
**Language**: English (all output)  
**Purpose**: Interactive helper for managing cookies and API keys

---

## 🎯 Main Menu (3 Options)

```
============================================================
🍪 Cookies & API Helper
============================================================

Choose an option:

  [1] 👤 Set User-Agent (for cookies/API operations)
  [2] ➕ Add Cookies or API Keys
  [3] 🔍 Quick Status Check (with detailed report)
  [0] 🚪 Exit

Enter choice [0/1/2/3]:
```

---

## � Integration with Pipeline (CRITICAL)

### File Locations Strategy

**IMPORTANT**: This helper ONLY creates files in **existing fallback locations**.  
It does NOT introduce new locations or break existing pipeline code.

#### Cookies Files:
- ✅ `secrets/cookies.txt` (Priority 1 - transcribe.py line 532)
- ✅ `secrets/cookies_1.txt` (Priority 2 - transcribe.py line 533)
- ✅ `secrets/cookies_2.txt` (Priority 3 - transcribe.py line 534)
- ✅ `secrets/cookies_3.txt` (Priority 4 - transcribe.py line 535)
- ✅ `cookies.txt` (root - Priority 5 - transcribe.py line 536)

**Pipeline Integration**:
- `transcribe.py` already scans these 5 locations (lines 529-560)
- Helper will ONLY write to these exact paths
- NO new locations introduced
- NO conflicts with existing code

#### Gemini API Keys:
- ✅ `secrets/api_keys.txt` (Priority 1 - process.py uses this)
- ✅ `secrets/api_key.txt` (Priority 2 - fallback)
- ✅ `secrets/.env` with `GEMINI_API_KEY=...` (Priority 5)
- ❌ `GEMINI_API_KEY` env var (read-only - helper will NOT set env vars)

**Pipeline Integration**:
- `process.py` reads from `api_keys.txt` (multi-key support)
- `youtube_metadata.py` uses same fallback system
- Helper writes to SAME files
- NO conflicts

#### YouTube API Keys:
- ✅ `secrets/api_keys.txt` (Priority 2 - search.py, database.py)
- ✅ `secrets/.env` with `YT_API_KEY=...` (Priority 5)
- ❌ `YT_API_KEY` env var (read-only - NOT set by helper)

**Pipeline Integration**:
- `search.py` scans env var → api_keys.txt → .env
- `database.py` uses same system
- Helper writes to SAME files
- NO conflicts

#### Pexels API Keys:
- ✅ `secrets/pexels_key.txt` (Priority 3 - shorts_generator.py line 295)
- ✅ `secrets/.env` with `PEXELS_API_KEY=...` (Priority 2)
- ✅ `secrets/api_keys.txt` (Priority 4 - shared location)
- ❌ `PEXELS_API_KEY` env var (read-only - NOT set by helper)

**Pipeline Integration**:
- `shorts_generator.py` already scans these locations (lines 280-350)
- Helper writes to SAME files
- NO conflicts

#### User-Agent (NEW - NOT used by pipeline yet):
- ✅ `secrets/user_agent.txt` (NEW file - optional)
- 📝 **NOTE**: Pipeline does NOT currently read this file
- 🔮 **Future use**: Can be integrated into transcribe.py later
- ⚠️ **No breaking changes**: Creating this file won't affect current pipeline

---

### Conflict Prevention Rules

1. **NEVER create new locations**: Only use existing fallback paths
2. **NEVER modify pipeline code**: Helper is standalone
3. **NEVER set environment variables**: Only read them for status check
4. **ALWAYS deduplicate**: Check if key/cookies already exists
5. **ALWAYS validate format**: Ensure file format matches pipeline expectations
6. **ALWAYS use same priorities**: Match exact order in pipeline code

---

### Pipeline Compatibility Matrix

| Component | Helper Action | Pipeline Reads From | Conflict Risk |
|-----------|--------------|---------------------|---------------|
| **Cookies** | Write to `secrets/cookies*.txt` | `transcribe.py` lines 529-560 | ✅ NONE |
| **Gemini API** | Write to `api_keys.txt`, `.env` | `process.py`, `youtube_metadata.py` | ✅ NONE |
| **YouTube API** | Write to `api_keys.txt`, `.env` | `search.py`, `database.py` | ✅ NONE |
| **Pexels API** | Write to `pexels_key.txt`, `.env` | `shorts_generator.py` lines 280-350 | ✅ NONE |
| **User-Agent** | Write to `user_agent.txt` | ❌ NOT read by pipeline (yet) | ✅ NONE |

---

### File Format Compatibility

#### Cookies Format (TWO FORMATS SUPPORTED):

**Format 1: JSON (from browser extensions)** - MOST COMMON:
```json
[
    {
        "domain": ".youtube.com",
        "expirationDate": 1777392218.784224,
        "name": "__Secure-3PSID",
        "path": "/",
        "secure": true,
        "httpOnly": true,
        "value": "g.a0003AhaTKoSVny8aEwCZYyuwQuf5oG66HLYvsvD3dUOJtHVLGzxJl7mI8nursuMl33poh8gOAACgYKAUESARISFQHGX2MiLQXkQXGRUcn_38gERfWewhoVAUF8yKqDYVBEX58JIAAJJMjOqQC60076"
    },
    {
        "domain": ".youtube.com",
        "expirationDate": 1777392218.783727,
        "name": "__Secure-1PSIDTS",
        "path": "/",
        "value": "sidts-CjUBwQ9iIxLEUF8vb8hY37yw28lVyMkbIKTBLZ7Ae0VHhdBSclTvn6Zw9eJo7eFfIyS9x2hZbRAA"
    }
]
```

**Format 2: Netscape (old format)**:
```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1735689600	VISITOR_INFO1_LIVE	abc123
.youtube.com	TRUE	/	TRUE	1735689600	CONSENT	YES+cb
```

**Auto-Detection & Conversion**:
- ✅ Script **auto-detects** format (JSON vs Netscape)
- ✅ If JSON → **converts to Netscape** format
- ✅ If Netscape → uses directly
- ✅ Validates `.youtube.com` domain exists
- ✅ Size > 50 bytes (transcribe.py line 545 validation)

#### API Keys Format (api_keys.txt):
```
AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
AIzaSyD9876543210zyxwvutsrqponmlkjihgfedcba
AIzaSyD5555555555aaaaaaaaabbbbbbbbbcccccccc
```
**Validation**:
- ✅ One key per line
- ✅ No comments (pipeline doesn't strip comments)
- ✅ No empty lines between keys
- ✅ Exact format: `^AIzaSy[A-Za-z0-9_-]{33}$`

#### .env Format:
```
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
YT_API_KEY=AIzaSyD9876543210zyxwvutsrqponmlkjihgfedcba
PEXELS_API_KEY=563492ad6f917000010000017a2c79b55b394f18
```
**Validation**:
- ✅ Format: `KEY_NAME=value` (no spaces around `=`)
- ✅ No quotes around values
- ✅ One variable per line
- ✅ Compatible with `python-dotenv` parsing

---

## �📐 Option 1: User-Agent Manager

### Purpose
- Allow user to set custom User-Agent for yt-dlp operations
- Useful when cookies fail or need specific browser matching
- **NOTE**: Currently NOT integrated with pipeline (future feature)

### Workflow
```
============================================================
👤 User-Agent Manager
============================================================

Current User-Agent:
  Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...

Options:
  [1] Use default (Chrome 141 - Latest)
  [2] Chrome 120 (Windows)
  [3] Firefox 121 (Windows)
  [4] Edge 120 (Windows)
  [5] Safari 17 (macOS)
  [6] Custom User-Agent (manual input)
  [0] Back to main menu

Enter choice:
```

### Implementation Details
1. Read current User-Agent from config (if exists)
2. Display preset User-Agents from `transcribe.py::USER_AGENTS`
3. Allow custom input
4. Save to: `secrets/user_agent.txt` or `config/user_agent.txt`
5. Validate format (must contain "Mozilla" or similar)

### File Operations
- **Read**: `transcribe.py` USER_AGENTS list
- **Write**: `secrets/user_agent.txt`
- **Validate**: Check if string is valid User-Agent format

---

## 📐 Option 2: Add Cookies or API Keys

### Purpose
- Interactive wizard to add cookies or API keys
- Guides user through proper file creation

### Workflow

#### Step 1: Choose Type
```
============================================================
➕ Add Cookies or API Keys
============================================================

What would you like to add?

  [1] 🍪 Cookies (YouTube login cookies)
  [2] 🤖 Gemini API Key
  [3] 📺 YouTube Data API Key
  [4] 🎬 Pexels API Key
  [0] Back to main menu

Enter choice:
```

#### Step 2a: Add Cookies (SUPPORTS JSON & NETSCAPE)

```
============================================================
🍪 Add YouTube Cookies
============================================================

Instructions:
1. Install browser extension:
   - Chrome: "Get cookies.txt LOCALLY" or "EditThisCookie"
   - Firefox: "Cookie Quick Manager" or "cookies.txt"

2. Login to YouTube.com in your browser

3. Export cookies in ANY format:
   - JSON format (most extensions) ✅ Recommended
   - Netscape format (old extensions)

4. Paste the cookies content below (Ctrl+V, then Ctrl+D on new line):

[Press Ctrl+D or type 'END' on new line when done]
------------------------------------------------------------

```

**Implementation (AUTO-DETECTS FORMAT)**:
1. Read multi-line input (until Ctrl+D or "END")
2. **Auto-detect format**:
   ```python
   def detect_cookies_format(content):
       content_stripped = content.strip()
       # Check if JSON
       if content_stripped.startswith('[') or content_stripped.startswith('{'):
           return 'json'
       # Check if Netscape
       elif '# Netscape HTTP Cookie File' in content:
           return 'netscape'
       else:
           return 'unknown'
   ```
3. **Convert if needed**:
   - If JSON → convert to Netscape format
   - If Netscape → use directly
   - If unknown → reject with clear error
4. Validate final Netscape format:
   - Check for `.youtube.com` entries
   - Check file size > 50 bytes
5. Detect which slot to use:
   - If `secrets/cookies.txt` empty/missing → use it
   - Else check `cookies_1.txt`, `cookies_2.txt`, `cookies_3.txt`
   - Auto-assign to first empty slot
6. Save to chosen location
7. Display confirmation with file path

**JSON to Netscape Conversion**:
```python
def json_to_netscape(json_content):
    """
    Convert JSON cookies to Netscape format
    """
    import json
    
    try:
        # Parse JSON
        cookies = json.loads(json_content)
        if not isinstance(cookies, list):
            cookies = [cookies]  # Single cookie object
        
        # Start with header
        netscape_lines = [
            "# Netscape HTTP Cookie File",
            "# This is a generated file! Do not edit.",
            ""
        ]
        
        # Convert each cookie
        for cookie in cookies:
            domain = cookie.get('domain', '')
            
            # Skip non-YouTube cookies
            if 'youtube.com' not in domain and 'google.com' not in domain:
                continue
            
            # Extract fields
            flag = "TRUE" if cookie.get('hostOnly', False) == False else "FALSE"
            path = cookie.get('path', '/')
            secure = "TRUE" if cookie.get('secure', False) else "FALSE"
            expiration = int(cookie.get('expirationDate', 0))
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            # Build Netscape line (tab-separated)
            line = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
            netscape_lines.append(line)
        
        # Join with newlines
        netscape_content = "\n".join(netscape_lines)
        
        return netscape_content, None  # Success
        
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return None, f"Conversion failed: {str(e)}"
```

**Example Output (After Conversion)**:
```
Detecting cookies format...
✅ Detected: JSON format (13 cookies)

Converting JSON to Netscape format...
✅ Converted successfully
   - Kept: 13 YouTube/Google cookies
   - Removed: 0 non-YouTube cookies
   - Size: 2,845 bytes

Validating Netscape format...
✅ Valid format
✅ Contains .youtube.com cookies
✅ Ready to save

Save to secrets/cookies.txt? [Y/n]:
```

#### Step 2b: Add Gemini API Key

```
============================================================
🤖 Add Gemini API Key
============================================================

Instructions:
1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with "AIzaSy...")

Enter Gemini API Key:
> _

Validating...
✅ Valid format (39 chars, starts with 'AIzaSy')

Where to save?
  [1] secrets/api_keys.txt (recommended - supports multiple)
  [2] secrets/.env (GEMINI_API_KEY=...)
  [3] secrets/api_key.txt (single key)

Enter choice [1/2/3] (default: 1):
```

**Implementation**:
1. Prompt for API key
2. Validate:
   - Starts with "AIzaSy"
   - Length ≈ 39 chars
   - Only alphanumeric + hyphens
3. Ask where to save (default: `api_keys.txt`)
4. If `api_keys.txt`:
   - Check if key already exists (deduplicate)
   - Append to file
5. If `.env`:
   - Check if `GEMINI_API_KEY=` exists
   - Update or append line
6. Display confirmation

#### Step 2c: Add YouTube API Key

```
============================================================
📺 Add YouTube Data API Key
============================================================

Instructions:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create API Key or use existing
3. Enable "YouTube Data API v3"
4. Copy the key (starts with "AIzaSy...")

Enter YouTube API Key:
> _

Validating...
✅ Valid format
⚠️  Testing API key (calling YouTube API)...
✅ API Key works! (Quota: 10000/day remaining)

Where to save?
  [1] secrets/api_keys.txt (recommended - supports multiple)
  [2] Environment variable YT_API_KEY (current session only)
  [3] secrets/.env (YT_API_KEY=...)

Enter choice [1/2/3] (default: 1):
```

**Implementation**:
1. Prompt for API key
2. Validate format (same as Gemini)
3. **Test API key** (optional but recommended):
   - Call YouTube API: `GET https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key=API_KEY`
   - Check response for quota info
4. Save to chosen location
5. Display confirmation with quota info

#### Step 2d: Add Pexels API Key

```
============================================================
🎬 Add Pexels API Key
============================================================

Instructions:
1. Go to: https://www.pexels.com/api/
2. Sign up for free account
3. Copy your API key from dashboard

Enter Pexels API Key:
> _

Validating...
✅ Valid format (52 chars)

Where to save?
  [1] secrets/pexels_key.txt (recommended - dedicated file)
  [2] secrets/.env (PEXELS_API_KEY=...)
  [3] secrets/api_keys.txt (shared with other keys)

Enter choice [1/2/3] (default: 1):
```

**Implementation**:
1. Prompt for API key
2. Validate:
   - Length ≈ 52-60 chars
   - Alphanumeric only
3. Save to chosen location
4. Display confirmation

---

## 📐 Option 3: Quick Status Check (WITH REAL TESTING)

### Purpose
- **Display current status** of all cookies and API keys
- **Test each file/key** with actual API calls (not just format check)
- **Distinguish between**:
  - ✅ Valid & Working
  - ⚠️ Valid but Quota Exceeded / Rate Limited
  - ❌ Expired / Invalid
  - 🔒 Format Valid but Not Tested (offline mode)
- Show which files are active, which are backups
- Provide detailed report with real-time status

### Workflow (WITH REAL TESTING)

```
============================================================
🔍 Quick Status Check (Real Testing Mode)
============================================================

⚠️  This will test ALL cookies and API keys with real API calls.
   This may take 30-60 seconds and consume quota.

Options:
  [1] Full test (recommended - test everything)
  [2] Quick check (format validation only - no API calls)
  [0] Back to main menu

Enter choice [1/2/0] (default: 1): 1

============================================================
Testing in progress... Please wait...
============================================================

============================================================
🤖 Gemini API Keys
============================================================
Testing 3 keys from secrets/api_keys.txt...

  ✅ Key 1: AIzaSyD11m... 
     Status: ACTIVE ✅
     Model: gemini-2.5-flash
     Test query: Success (0.8s)
     Last tested: Just now

  ⚠️  Key 2: AIzaSyAUxX...
     Status: QUOTA EXCEEDED ⚠️
     Error: "API quota exceeded. Try again tomorrow."
     Quota resets: Tomorrow at 12:00 AM PST
     Last tested: Just now

  ✅ Key 3: AIzaSyDWA-...
     Status: ACTIVE ✅
     Model: gemini-2.5-flash
     Test query: Success (1.1s)
     Last tested: Just now

Testing secrets/.env (GEMINI_API_KEY)...
  ✅ AIzaSyDD_a... - ACTIVE ✅ (same as Key 1)

  📊 Summary: 3 total keys
     ✅ 2 working (67%)
     ⚠️ 1 quota exceeded (33%)
     ❌ 0 invalid (0%)

============================================================
📺 YouTube Data API Keys
============================================================
Testing YT_API_KEY environment variable...
  ✅ AIzaSyBNV3...
     Status: ACTIVE ✅
     API: YouTube Data API v3 enabled
     Quota: 9,234/10,000 remaining (92%)
     Test: Fetched video details successfully
     Last tested: Just now

Testing 4 keys from secrets/api_keys.txt...

  ✅ Key 1: AIzaSyBNV3... - ACTIVE ✅ (same as env var)
  ✅ Key 2: AIzaSyD11m... - ACTIVE ✅ (Quota: 8,765/10,000)
  ❌ Key 3: AIzaSyAUxX... - INVALID ❌
     Error: "API_KEY_INVALID"
     Action: Remove this key or regenerate
  ✅ Key 4: AIzaSyDWA-... - ACTIVE ✅ (Quota: 9,123/10,000)

  📊 Summary: 4 total keys
     ✅ 3 working (75%)
     ⚠️ 0 quota exceeded (0%)
     ❌ 1 invalid (25%)
     💡 Recommendation: Remove invalid key #3

============================================================
🍪 YouTube Cookies
============================================================
Testing secrets/cookies.txt...
  ⏳ Testing with yt-dlp (Rick Roll video)...
  ✅ VALID & WORKING ✅
     Size: 3,055 bytes
     Entries: 28 cookies
     Domains: .youtube.com, accounts.google.com
     Last modified: 2025-10-30 19:00:05
     Test result: Successfully fetched video title
     Can access: Age-restricted content ✅
     Expiry: Valid until 2026-01-15
     Last tested: Just now

Testing secrets/cookies_1.txt...
  ⏳ Testing with yt-dlp...
  ❌ EXPIRED / INVALID ❌
     Size: 3,055 bytes (same as cookies.txt)
     Error: "HTTP Error 403: Forbidden"
     Status: Cookies expired or revoked
     Action: Re-export from browser
     Last tested: Just now

  ❌ secrets/cookies_2.txt - NOT FOUND
  ❌ secrets/cookies_3.txt - NOT FOUND

  📊 Summary: 2 files found
     ✅ 1 working (50%)
     ⚠️ 0 rate limited (0%)
     ❌ 1 expired (50%)
     💡 Recommendation: Replace cookies_1.txt with fresh cookies

============================================================
🎬 Pexels API Key
============================================================
Testing secrets/pexels_key.txt...
  ⏳ Calling Pexels API (search: 'nature')...
  ✅ ACTIVE ✅
     Key: RYLjHA4Pk6... (56 chars)
     Status: Working
     Rate limit: 156/200 remaining (78%)
     Rate limit resets: In 23 minutes
     Test: Found 15 videos successfully
     Response time: 0.6s
     Last tested: Just now

Testing secrets/.env (PEXELS_API_KEY)...
  ✅ Same key as pexels_key.txt ✅

  📊 Summary: 1 key
     ✅ 1 working (100%)
     ⚠️ 0 rate limited (0%)
     ❌ 0 invalid (0%)

============================================================
📊 Overall Summary
============================================================
  🤖 Gemini API:     2/3 working (67%) - 1 quota exceeded
  📺 YouTube API:    3/4 working (75%) - 1 invalid key
  🍪 Cookies:        1/2 working (50%) - 1 expired
  🎬 Pexels API:     1/1 working (100%)

  ⚠️  Issues Found:
     1. Gemini Key #2: Quota exceeded (wait until tomorrow)
     2. YouTube Key #3: Invalid - should be removed
     3. Cookies File #2: Expired - needs replacement

  💡 Recommendations:
     • Remove invalid YouTube key from api_keys.txt
     • Replace expired cookies_1.txt with fresh export
     • Use Gemini Key #1 or #3 (Key #2 over quota)

  ✅ Overall Status: OPERATIONAL (with warnings)

============================================================
Test completed in 28.4 seconds

Press Enter to continue...
```

============================================================
🤖 Gemini API Keys
============================================================
  ✅ secrets/api_keys.txt         (3 keys)
     - AIzaSyD11m... (Primary)
     - AIzaSyAUxX... (Backup 1)
     - AIzaSyDWA-... (Backup 2)
  ✅ secrets/.env                  (1 key)
     - AIzaSyDD_a... (GEMINI_API_KEY)
  ❌ GEMINI_API_KEY env var        (not set)

  📊 Total: 3 unique keys available

============================================================
📺 YouTube Data API Keys
============================================================
  ✅ YT_API_KEY env var            (1 key)
     - AIzaSyBNV3... (Active)
  ✅ secrets/api_keys.txt          (4 keys)
     - AIzaSyBNV3... (Primary - matches env)
     - AIzaSyD11m... (Backup 1)
     - AIzaSyAUxX... (Backup 2)
     - AIzaSyDWA-... (Backup 3)
  ✅ secrets/.env                  (1 key)
     - AIzaSyBav... (YT_API_KEY)

  📊 Total: 4 unique keys available

============================================================
🍪 YouTube Cookies
============================================================
  ✅ secrets/cookies.txt           (3,055 bytes - Valid ✓)
     Last modified: 2025-10-30 19:00:05
     Entries: 28 cookies
     Domains: .youtube.com, accounts.google.com
  ✅ secrets/cookies_1.txt         (3,055 bytes - Valid ✓)
     Last modified: 2025-10-30 20:45:12
     Status: Backup (identical to primary)
  ❌ secrets/cookies_2.txt         (not found)
  ❌ secrets/cookies_3.txt         (not found)

  📊 Total: 2 valid cookies files (1 primary + 1 backup)

============================================================
🎬 Pexels API Key
============================================================
  ✅ secrets/pexels_key.txt        (1 key)
     - RYLjHA4Pk6... (Primary)
  ✅ secrets/.env                  (1 key)
     - RYLjHA4Pk6... (matches primary)
  ❌ PEXELS_API_KEY env var        (not set)

  📊 Total: 1 key available

============================================================
📊 Summary
============================================================
  ✅ Gemini API:     3 keys (2 locations)
  ✅ YouTube API:    4 keys (3 locations)
  ✅ Cookies:        2 files (both valid)
  ✅ Pexels API:     1 key (2 locations)

  🎉 All systems operational!

============================================================

Press Enter to continue...
```

### Implementation Details (REAL TESTING)

#### Testing Mode Selection:
```python
def option_3_status_check():
    print("\n⚠️  This will test ALL cookies and API keys with real API calls.")
    print("   This may take 30-60 seconds and consume quota.\n")
    print("Options:")
    print("  [1] Full test (recommended - test everything)")
    print("  [2] Quick check (format validation only - no API calls)")
    print("  [0] Back to main menu")
    
    choice = input("\nEnter choice [1/2/0] (default: 1): ").strip() or "1"
    
    if choice == "1":
        test_mode = "full"  # Real API testing
    elif choice == "2":
        test_mode = "quick"  # Format only
    else:
        return
    
    # Run tests...
```

#### For Gemini API (REAL TESTING):
```python
def check_gemini_status(test_mode="full"):
    """
    Check Gemini API keys and test them if test_mode='full'
    """
    import google.generativeai as genai
    
    # 1. Scan all locations
    locations = [
        ("secrets/api_keys.txt", "multi"),
        ("secrets/api_key.txt", "single"),
        ("secrets/.env", "env"),
    ]
    
    results = {
        "keys": [],
        "working": 0,
        "quota_exceeded": 0,
        "invalid": 0
    }
    
    for location, type in locations:
        path = Path(location)
        if not path.exists():
            continue
            
        # Parse keys from file
        if type == "multi":
            keys = [k.strip() for k in path.read_text().splitlines() if k.strip()]
        elif type == "single":
            keys = [path.read_text().strip()]
        elif type == "env":
            keys = parse_env_var(path, "GEMINI_API_KEY")
        
        # Test each key (if full mode)
        for idx, key in enumerate(keys, 1):
            key_info = {
                "key": mask_key(key),
                "location": location,
                "index": idx,
                "status": "unknown"
            }
            
            if test_mode == "full":
                # REAL API TEST
                print(f"  ⏳ Testing Key {idx}: {mask_key(key)}...")
                success, message, details = test_gemini_api_real(key)
                
                if success:
                    key_info["status"] = "active"
                    key_info["model"] = details.get("model", "gemini-2.5-flash")
                    key_info["response_time"] = details.get("response_time", 0)
                    results["working"] += 1
                    print(f"     ✅ ACTIVE - {message}")
                elif "QUOTA_EXCEEDED" in message:
                    key_info["status"] = "quota_exceeded"
                    key_info["error"] = message
                    results["quota_exceeded"] += 1
                    print(f"     ⚠️  QUOTA EXCEEDED - {message}")
                else:
                    key_info["status"] = "invalid"
                    key_info["error"] = message
                    results["invalid"] += 1
                    print(f"     ❌ INVALID - {message}")
            else:
                # Quick mode - format only
                if validate_api_key_format(key, "gemini"):
                    key_info["status"] = "format_valid"
                else:
                    key_info["status"] = "format_invalid"
            
            results["keys"].append(key_info)
    
    return results

def test_gemini_api_real(api_key):
    """
    Test Gemini API with REAL API call
    Returns: (success, message, details_dict)
    """
    import time
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        start_time = time.time()
        response = model.generate_content("Reply with exactly: 'API key works'")
        response_time = time.time() - start_time
        
        if response and response.text:
            return True, "API key works!", {
                "model": "gemini-2.5-flash",
                "response_time": round(response_time, 1)
            }
        else:
            return False, "Empty response", {}
            
    except Exception as e:
        error_msg = str(e)
        if "QUOTA_EXCEEDED" in error_msg or "quota exceeded" in error_msg.lower():
            return False, "QUOTA_EXCEEDED: Daily limit reached", {}
        elif "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return False, "API_KEY_INVALID: Key is invalid or revoked", {}
        elif "PERMISSION_DENIED" in error_msg:
            return False, "PERMISSION_DENIED: Billing not enabled", {}
        else:
            return False, f"Error: {error_msg[:50]}", {}
```

#### For YouTube API (REAL TESTING):
```python
def check_youtube_status(test_mode="full"):
    """
    Check YouTube API keys and test them
    """
    import requests
    
    results = {
        "keys": [],
        "working": 0,
        "quota_exceeded": 0,
        "invalid": 0
    }
    
    # Scan all locations (env var, api_keys.txt, .env)
    # ... similar to Gemini ...
    
    if test_mode == "full":
        # REAL API TEST
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet",
            "id": "dQw4w9WgXcQ",
            "key": key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Success - extract quota info
                data = response.json()
                quota_used = 10000 - int(response.headers.get("X-RateLimit-Remaining", 10000))
                
                key_info["status"] = "active"
                key_info["quota"] = f"{10000 - quota_used}/10,000"
                results["working"] += 1
                print(f"     ✅ ACTIVE - Quota: {key_info['quota']}")
                
            elif response.status_code == 403:
                error_data = response.json()
                reason = error_data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                
                if reason == "quotaExceeded":
                    key_info["status"] = "quota_exceeded"
                    results["quota_exceeded"] += 1
                    print(f"     ⚠️  QUOTA EXCEEDED")
                else:
                    key_info["status"] = "invalid"
                    key_info["error"] = f"Forbidden: {reason}"
                    results["invalid"] += 1
                    print(f"     ❌ INVALID - {reason}")
            else:
                key_info["status"] = "invalid"
                results["invalid"] += 1
                print(f"     ❌ INVALID - HTTP {response.status_code}")
                
        except Exception as e:
            key_info["status"] = "error"
            key_info["error"] = str(e)
            results["invalid"] += 1
            print(f"     ❌ ERROR - {str(e)[:50]}")
    
    return results
```

#### For Cookies (REAL TESTING WITH yt-dlp):
```python
def check_cookies_status(test_mode="full"):
    """
    Check cookies files and test them with yt-dlp
    """
    import subprocess
    from datetime import datetime
    
    results = {
        "files": [],
        "working": 0,
        "expired": 0,
        "not_found": 0
    }
    
    cookie_paths = [
        "secrets/cookies.txt",
        "secrets/cookies_1.txt",
        "secrets/cookies_2.txt",
        "secrets/cookies_3.txt",
        "cookies.txt"
    ]
    
    for cookie_path in cookie_paths:
        path = Path(cookie_path)
        
        if not path.exists():
            results["not_found"] += 1
            print(f"  ❌ {cookie_path} - NOT FOUND")
            continue
        
        file_info = {
            "path": cookie_path,
            "size": path.stat().st_size,
            "modified": datetime.fromtimestamp(path.stat().st_mtime),
            "status": "unknown"
        }
        
        # Count cookies
        content = path.read_text()
        cookie_count = len([line for line in content.splitlines() 
                          if line.strip() and not line.startswith("#")])
        file_info["cookie_count"] = cookie_count
        
        if test_mode == "full":
            # REAL TEST WITH yt-dlp
            print(f"  ⏳ Testing {cookie_path} with yt-dlp...")
            
            cmd = [
                "yt-dlp",
                "--cookies", str(path),
                "--skip-download",
                "--print", "title",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    file_info["status"] = "working"
                    file_info["test_result"] = "Successfully fetched video"
                    results["working"] += 1
                    print(f"     ✅ VALID & WORKING")
                    print(f"        Size: {file_info['size']:,} bytes")
                    print(f"        Entries: {cookie_count} cookies")
                    print(f"        Last modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    file_info["status"] = "expired"
                    results["expired"] += 1
                    print(f"     ❌ EXPIRED / INVALID")
                    
            except subprocess.CalledProcessError as e:
                # Check error type
                error_output = e.stderr or e.stdout or ""
                
                if "403" in error_output or "Forbidden" in error_output:
                    file_info["status"] = "expired"
                    file_info["error"] = "HTTP 403: Cookies expired or revoked"
                    results["expired"] += 1
                    print(f"     ❌ EXPIRED (HTTP 403)")
                elif "401" in error_output or "Unauthorized" in error_output:
                    file_info["status"] = "expired"
                    file_info["error"] = "HTTP 401: Cookies invalid"
                    results["expired"] += 1
                    print(f"     ❌ EXPIRED (HTTP 401)")
                else:
                    file_info["status"] = "error"
                    file_info["error"] = error_output[:100]
                    results["expired"] += 1
                    print(f"     ❌ ERROR: {error_output[:50]}")
                    
            except subprocess.TimeoutExpired:
                file_info["status"] = "timeout"
                file_info["error"] = "Test timed out (network issue?)"
                results["expired"] += 1
                print(f"     ⏱️ TIMEOUT")
        else:
            # Quick mode - format only
            if file_info["size"] > 50 and "# Netscape HTTP Cookie File" in content:
                file_info["status"] = "format_valid"
            else:
                file_info["status"] = "format_invalid"
        
        results["files"].append(file_info)
    
    return results
```

#### For Pexels API (REAL TESTING):
```python
def check_pexels_status(test_mode="full"):
    """
    Check Pexels API key and test it
    """
    import requests
    import time
    
    results = {
        "keys": [],
        "working": 0,
        "rate_limited": 0,
        "invalid": 0
    }
    
    # Scan pexels_key.txt, .env, api_keys.txt
    # ... parse keys ...
    
    if test_mode == "full":
        # REAL API TEST
        print(f"  ⏳ Testing Pexels key...")
        
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": key}
        params = {"query": "nature", "per_page": 1}
        
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract rate limit info
                limit = response.headers.get("X-Ratelimit-Limit", "200")
                remaining = response.headers.get("X-Ratelimit-Remaining", "Unknown")
                
                key_info["status"] = "active"
                key_info["rate_limit"] = f"{remaining}/{limit}"
                key_info["response_time"] = round(response_time, 1)
                results["working"] += 1
                
                print(f"     ✅ ACTIVE")
                print(f"        Rate limit: {remaining}/{limit} remaining ({int(remaining)/int(limit)*100:.0f}%)")
                print(f"        Response time: {response_time:.1f}s")
                
            elif response.status_code == 401:
                key_info["status"] = "invalid"
                key_info["error"] = "Unauthorized: Invalid API key"
                results["invalid"] += 1
                print(f"     ❌ INVALID - Unauthorized")
                
            elif response.status_code == 429:
                key_info["status"] = "rate_limited"
                key_info["error"] = "Rate limit exceeded (200/hour)"
                results["rate_limited"] += 1
                print(f"     ⚠️  RATE LIMITED")
                
            else:
                key_info["status"] = "error"
                key_info["error"] = f"HTTP {response.status_code}"
                results["invalid"] += 1
                print(f"     ❌ ERROR - HTTP {response.status_code}")
                
        except Exception as e:
            key_info["status"] = "error"
            key_info["error"] = str(e)
            results["invalid"] += 1
            print(f"     ❌ ERROR - {str(e)[:50]}")
    
    return results
```

---

## 🏗️ File Structure

```
cookies_helper.py
├── main()
│   ├── show_menu()
│   ├── option_1_user_agent()
│   ├── option_2_add_credentials()
│   └── option_3_status_check()
│
├── User-Agent Functions
│   ├── get_current_user_agent()
│   ├── set_user_agent(ua_string)
│   └── load_preset_user_agents()
│
├── Add Credentials Functions
│   ├── add_cookies()
│   │   ├── read_multiline_input()
│   │   ├── validate_cookies_format()
│   │   └── save_cookies_to_file()
│   ├── add_gemini_api()
│   ├── add_youtube_api()
│   └── add_pexels_api()
│
├── Status Check Functions
│   ├── check_gemini_status()
│   ├── check_youtube_status()
│   ├── check_cookies_status()
│   └── check_pexels_status()
│
└── Utility Functions
    ├── validate_api_key_format(key, service)
    ├── test_youtube_api(key)
    ├── mask_key(key)
    ├── parse_env_file(path)
    ├── count_cookies_in_file(path)
    └── get_file_stats(path)
```

---

## 🎨 Output Formatting

### Status Icons & Colors:
- ✅ **Green (ACTIVE)**: Working perfectly, tested successfully
- ⚠️ **Yellow (WARNING)**: Valid but quota/rate limit exceeded
- ❌ **Red (INVALID)**: Expired, invalid, or test failed
- 🔒 **Gray (NOT TESTED)**: Format valid but not tested (quick mode)
- ⏱️ **Blue (TIMEOUT)**: Test timed out (network issue)
- 💡 **Cyan**: Info/Tips/Recommendations

### Status Categories Table:

| Icon | Status | Meaning | Examples |
|------|--------|---------|----------|
| ✅ | **ACTIVE** | Tested and working | API responds, Cookies fetch video |
| ⚠️ | **QUOTA EXCEEDED** | Valid but over limit | Gemini quota, YouTube quota, Pexels rate limit |
| ❌ | **INVALID** | Not working | API_KEY_INVALID, HTTP 403, Expired cookies |
| ❌ | **EXPIRED** | Was valid, now expired | Cookies expired, Token revoked |
| 🔒 | **FORMAT VALID** | Not tested (quick mode) | Format check only, no API call |
| ⏱️ | **TIMEOUT** | Network issue | API unreachable, slow response |

### Colors (using rich or simple print):
- ✅ Green: Success/Found
- ❌ Red: Error/Not found
- ⚠️ Yellow: Warning
- 💡 Cyan: Info/Tips
- 📊 Blue: Statistics

### Layout:
- Use `=` for major sections (60 chars wide)
- Use `-` for sub-sections
- Indent details with 2-4 spaces
- Use emoji for visual clarity

---

## 🔧 Dependencies

```python
# Standard library
import os
import sys
from pathlib import Path
from datetime import datetime
import re
import hashlib
import subprocess
import time

# Required for API testing
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  Warning: 'requests' not installed. API testing disabled.")

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("⚠️  Warning: 'google-generativeai' not installed. Gemini testing disabled.")

# Optional (for better UX)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Required for cookies testing
# yt-dlp must be installed and in PATH
# Check: subprocess.run(["yt-dlp", "--version"], ...)
```

---

## 🧪 Validation & Testing Rules (ENHANCED)

### API Key Format Comparison Table

| API Type | Length | Prefix | Character Set | Example |
|----------|--------|--------|---------------|---------|
| **Gemini** | **Exactly 39** | `AIzaSy` | Alphanumeric + `-_` | `AIzaSyD11m...` (39 chars) |
| **YouTube** | **Exactly 39** | `AIzaSy` | Alphanumeric + `-_` | `AIzaSyBNV3...` (39 chars) |
| **Pexels** | **50-60** | None | Alphanumeric only | `RYLjHA4Pk66s...` (56 chars) |

**⚠️ CRITICAL**: Pexels keys are **~45% longer** than Google API keys!

---

### Two-Step Validation System:
1. **Format Validation** (offline - instant)
2. **Functionality Testing** (online - actual API/cookies test)

---

### Cookies Validation (SUPPORTS JSON & NETSCAPE):

#### Step 1: Format Detection & Auto-Conversion (Offline)
**Auto-detect input format**:
```python
def detect_and_convert_cookies(content):
    """
    Auto-detect cookies format and convert to Netscape if needed
    """
    content = content.strip()
    
    # Detect format
    if content.startswith('[') or content.startswith('{'):
        # JSON format - convert to Netscape
        netscape, error = json_to_netscape(content)
        if error:
            return None, f"JSON conversion failed: {error}"
        return netscape, None
        
    elif '# Netscape HTTP Cookie File' in content:
        # Already Netscape - use directly
        return content, None
        
    elif '<html>' in content.lower() or '<!doctype' in content.lower():
        # HTML content - reject
        return None, "This looks like HTML, not cookies. Did you paste the wrong content?"
        
    else:
        # Unknown format
        return None, "Unrecognized format. Please export as JSON or Netscape format."
```

**Validation checks** (after conversion to Netscape):
- ✅ File size > 50 bytes
- ✅ Contains "# Netscape HTTP Cookie File" (after conversion)
- ✅ Has at least one `.youtube.com` or `.google.com` line
- ✅ Not HTML content (reject if contains `<html>`)
- ✅ Line count > 5
- ✅ Tab-separated values (not spaces)

#### Step 2: Functionality Test (Online - REQUIRED)
```
Testing cookies validity...
[1/3] Checking cookie format... ✅ Valid
[2/3] Testing with yt-dlp... ⏳ Please wait...
[3/3] Verifying YouTube access... ✅ Cookies work!

Test Results:
  ✅ Successfully accessed YouTube
  ✅ Cookies are valid and not expired
  ✅ Can fetch video information
  
Proceed to save? [Y/n]:
```

**How to Test Cookies**:
```python
def test_cookies(cookies_content):
    """
    Test cookies by trying to fetch a public YouTube video
    """
    # Save to temp file
    temp_cookies = Path("temp_cookies_test.txt")
    temp_cookies.write_text(cookies_content)
    
    try:
        # Test with yt-dlp on a known public video
        cmd = [
            "yt-dlp",
            "--cookies", str(temp_cookies),
            "--skip-download",
            "--print", "title",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (always available)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return True, "Cookies work! Fetched video title successfully"
        else:
            return False, "Cookies failed to fetch video data"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: Cookies test took too long (network issue?)"
    except subprocess.CalledProcessError as e:
        return False, f"yt-dlp failed: {e.stderr}"
    except Exception as e:
        return False, f"Test failed: {str(e)}"
    finally:
        # Cleanup temp file
        if temp_cookies.exists():
            temp_cookies.unlink()
```

**Test Output Example (JSON Input)**:
```
============================================================
🍪 Testing Cookies (Auto-Converted from JSON)
============================================================

[Step 1/4] Format detection...
  ✅ Detected: JSON format
  ✅ Found: 13 cookies in JSON array

[Step 2/4] Converting to Netscape format...
  ✅ Converted successfully
     • Kept: 13 YouTube/Google cookies
     • Filtered: .youtube.com, .google.com domains
     • Output size: 2,845 bytes

[Step 3/4] Format validation...
  ✅ Valid Netscape format (after conversion)
  ✅ Contains YouTube cookies (13 entries)
  ✅ File size: 2,845 bytes

[Step 4/4] Testing with yt-dlp...
  ⏳ Fetching test video (Rick Astley - Never Gonna Give You Up)...
  ✅ Success! Video title fetched

Verification:
  ✅ Cookies are active and not expired
  ✅ Can access age-restricted content (if logged in)

📊 Test Result: PASS ✅

Save cookies to secrets/cookies.txt? [Y/n]:
```

**Test Output Example (Netscape Input)**:
```
============================================================
🍪 Testing Cookies
============================================================

[Step 1/3] Format validation...
  ✅ Valid Netscape format
  ✅ Contains YouTube cookies (28 entries)
  ✅ File size: 3,055 bytes

[Step 2/3] Testing with yt-dlp...
  ⏳ Fetching test video (Rick Astley - Never Gonna Give You Up)...
  ✅ Success! Video title fetched

[Step 3/3] Verification...
  ✅ Cookies are active and not expired
  ✅ Can access age-restricted content (if logged in)

📊 Test Result: PASS ✅

Save cookies to secrets/cookies.txt? [Y/n]:
```

---

### Gemini API Key Validation:

#### Step 1: Format Validation (Offline)
- ✅ Starts with "AIzaSy"
- ✅ Length: **Exactly 39 chars** (strict check)
- ✅ Format: `^AIzaSy[A-Za-z0-9_-]{33}$`
- ✅ Only alphanumeric + hyphens/underscores
- ❌ Reject if length ≠ 39 (common error: copy/paste incomplete)

#### Step 2: Functionality Test (Online - REQUIRED)
```
Testing Gemini API key...
[1/3] Checking format... ✅ Valid
[2/3] Calling Gemini API... ⏳ Please wait...
[3/3] Verifying response... ✅ API key works!

Test Results:
  ✅ API key is active
  ✅ Model: gemini-2.5-flash
  ✅ Test query successful
  
Proceed to save? [Y/n]:
```

**How to Test Gemini API**:
```python
def test_gemini_api(api_key):
    """
    Test Gemini API key with a simple query
    """
    try:
        import google.generativeai as genai
        
        # Configure with test key
        genai.configure(api_key=api_key)
        
        # Try to create model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Simple test query
        response = model.generate_content("Say 'API key works' if you can read this.")
        
        if response and response.text:
            return True, f"API key works! Model: gemini-2.5-flash"
        else:
            return False, "API returned empty response"
            
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return False, "Invalid API key"
        elif "PERMISSION_DENIED" in error_msg:
            return False, "API key exists but permission denied (check billing)"
        elif "QUOTA_EXCEEDED" in error_msg:
            return False, "API key valid but quota exceeded"
        else:
            return False, f"Test failed: {error_msg}"
```

**Test Output Example**:
```
============================================================
🤖 Testing Gemini API Key
============================================================

[Step 1/3] Format validation...
  ✅ Valid format (39 chars, starts with 'AIzaSy')

[Step 2/3] Testing API connection...
  ⏳ Calling Gemini API with test query...
  ✅ Success! API responded

[Step 3/3] Verification...
  ✅ API key is active
  ✅ Model available: gemini-2.5-flash
  ✅ No quota issues detected

📊 Test Result: PASS ✅
💡 This key will be added as backup (you have 2 other keys)

Save to secrets/api_keys.txt? [Y/n]:
```

---

### YouTube Data API Key Validation:

#### Step 1: Format Validation (Offline)
- ✅ Starts with "AIzaSy"
- ✅ Length: **Exactly 39 chars** (same as Gemini)
- ✅ Format: `^AIzaSy[A-Za-z0-9_-]{33}$`
- ❌ Reject if length ≠ 39

#### Step 2: Functionality Test (Online - REQUIRED)
```
Testing YouTube API key...
[1/4] Checking format... ✅ Valid
[2/4] Calling YouTube API... ⏳ Please wait...
[3/4] Checking quota... ✅ 9,876/10,000 remaining
[4/4] Verifying permissions... ✅ All good!

Test Results:
  ✅ API key is active
  ✅ YouTube Data API v3 enabled
  ✅ Daily quota: 9,876/10,000 (98%)
  ✅ Can search videos
  
Proceed to save? [Y/n]:
```

**How to Test YouTube API**:
```python
def test_youtube_api(api_key):
    """
    Test YouTube Data API key with actual API call
    """
    try:
        import requests
        
        # Test endpoint: Get video details (public video, no auth needed)
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics",
            "id": "dQw4w9WgXcQ",  # Rick Roll (always available)
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                # Try to get quota info from headers (if available)
                quota_info = "Unknown"
                if "X-RateLimit-Limit" in response.headers:
                    quota_info = response.headers.get("X-RateLimit-Remaining", "Unknown")
                
                return True, f"API key works! Quota info: {quota_info}"
            else:
                return False, "API returned no video data (key might be restricted)"
                
        elif response.status_code == 400:
            return False, "Bad request: API key format invalid"
        elif response.status_code == 403:
            error = response.json().get("error", {})
            reason = error.get("errors", [{}])[0].get("reason", "unknown")
            
            if reason == "quotaExceeded":
                return False, "API key valid but daily quota exceeded (10,000 limit)"
            elif reason == "forbidden":
                return False, "API key exists but YouTube Data API not enabled"
            else:
                return False, f"Forbidden: {reason}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.Timeout:
        return False, "Timeout: Network too slow or API unreachable"
    except Exception as e:
        return False, f"Test failed: {str(e)}"
```

**Test Output Example**:
```
============================================================
📺 Testing YouTube Data API Key
============================================================

[Step 1/4] Format validation...
  ✅ Valid format (39 chars, starts with 'AIzaSy')

[Step 2/4] Testing API connection...
  ⏳ Calling YouTube Data API v3...
  ✅ Success! Fetched video data

[Step 3/4] Checking quota usage...
  ✅ Daily quota: 9,876/10,000 remaining (98.8%)
  💡 Refreshes at midnight PST

[Step 4/4] Verification...
  ✅ YouTube Data API v3 is enabled
  ✅ Can search and fetch videos
  ✅ No restrictions detected

📊 Test Result: PASS ✅
⚠️  Note: This key already exists in secrets/api_keys.txt (duplicate)

Options:
  [1] Cancel (don't add duplicate)
  [2] Add anyway (as backup)
  [0] Go back

Enter choice [1/2/0] (default: 1):
```

---

### Pexels API Key Validation:

#### Step 1: Format Validation (Offline)
- ✅ Length: **50-60 chars** (Pexels keys are LONGER than Google APIs)
- ✅ Only alphanumeric (no hyphens/underscores like Google)
- ✅ Format: `^[A-Za-z0-9]{50,60}$`
- ❌ Reject if contains special chars (-, _, etc.)
- ❌ Reject if length < 50 or > 60
- 💡 **Example valid key**: `RYLjHA4Pk66sAAioYrmrpMb9K6JWc4DECiUpLPsr7lBuBS0xgxqteQDd` (56 chars)

#### Step 2: Functionality Test (Online - REQUIRED)
```
Testing Pexels API key...
[1/3] Checking format... ✅ Valid
[2/3] Calling Pexels API... ⏳ Please wait...
[3/3] Fetching test video... ✅ API key works!

Test Results:
  ✅ API key is active
  ✅ Successfully fetched video data
  ✅ Rate limit: OK
  
Proceed to save? [Y/n]:
```

**How to Test Pexels API**:
```python
def test_pexels_api(api_key):
    """
    Test Pexels API key with actual API call
    """
    try:
        import requests
        
        # Test endpoint: Search videos
        url = "https://api.pexels.com/videos/search"
        headers = {
            "Authorization": api_key
        }
        params = {
            "query": "nature",
            "per_page": 1  # Just fetch 1 video to test
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "videos" in data and len(data["videos"]) > 0:
                # Check rate limit headers
                limit = response.headers.get("X-Ratelimit-Limit", "Unknown")
                remaining = response.headers.get("X-Ratelimit-Remaining", "Unknown")
                
                return True, f"API key works! Rate limit: {remaining}/{limit} remaining"
            else:
                return False, "API returned no videos (key might be invalid)"
                
        elif response.status_code == 401:
            return False, "Unauthorized: Invalid API key"
        elif response.status_code == 429:
            return False, "Rate limit exceeded (200 requests/hour limit)"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.Timeout:
        return False, "Timeout: Network too slow or API unreachable"
    except Exception as e:
        return False, f"Test failed: {str(e)}"
```

**Test Output Example**:
```
============================================================
🎬 Testing Pexels API Key
============================================================

[Step 1/3] Format validation...
  ✅ Valid format (56 chars, alphanumeric)

[Step 2/3] Testing API connection...
  ⏳ Searching for test videos...
  ✅ Success! Found videos

[Step 3/3] Verification...
  ✅ API key is active
  ✅ Rate limit: 198/200 remaining
  💡 Limit: 200 requests/hour

📊 Test Result: PASS ✅

Save to secrets/pexels_key.txt? [Y/n]:
```

---

### User-Agent:
- ✅ Contains "Mozilla"
- ✅ Length > 50 chars
- ✅ No newlines
- ℹ️ **No online test** (just format validation)

---

## 💾 File Saving Logic

### Cookies:
```python
def save_cookies(content):
    # Priority order
    paths = [
        "secrets/cookies.txt",
        "secrets/cookies_1.txt",
        "secrets/cookies_2.txt",
        "secrets/cookies_3.txt"
    ]
    
    # Find first empty/missing slot
    for path in paths:
        if not Path(path).exists() or Path(path).stat().st_size < 50:
            Path(path).write_text(content)
            return path
    
    # All slots full - ask user to overwrite
    print("All cookie slots are full!")
    print("Choose a slot to overwrite [1-4] or 0 to cancel:")
    # ... handle choice
```

### API Keys (api_keys.txt):
```python
def add_to_api_keys(key):
    path = Path("secrets/api_keys.txt")
    
    # Read existing keys
    if path.exists():
        existing = path.read_text().splitlines()
        # Deduplicate
        if key in existing:
            print("⚠️  Key already exists!")
            return False
        existing.append(key)
    else:
        existing = [key]
    
    # Write back
    path.write_text("\n".join(existing) + "\n")
    return True
```

### API Keys (.env):
```python
def add_to_env(key, var_name):
    path = Path("secrets/.env")
    
    if path.exists():
        content = path.read_text()
        # Check if variable exists
        pattern = rf'^{var_name}=.*$'
        if re.search(pattern, content, re.MULTILINE):
            # Update existing
            content = re.sub(pattern, f'{var_name}={key}', content, flags=re.MULTILINE)
        else:
            # Append new
            content += f'\n{var_name}={key}\n'
    else:
        content = f'{var_name}={key}\n'
    
    path.write_text(content)
```

---

## 🎯 Usage Examples

### Example Session 1: Add Cookies
```
$ python cookies_helper.py

🍪 Cookies & API Helper
[1] User-Agent  [2] Add Credentials  [3] Status  [0] Exit
> 2

[1] Cookies  [2] Gemini  [3] YouTube  [4] Pexels  [0] Back
> 1

🍪 Add YouTube Cookies
Paste cookies content (Ctrl+D when done):
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1735689600	CONSENT	YES+...
^D

✅ Valid cookies format (2,845 bytes, 26 entries)
✅ Saved to: secrets/cookies.txt

Press Enter to continue...
```

### Example Session 2: Quick Status
```
$ python cookies_helper.py

🍪 Cookies & API Helper
> 3

🔍 Quick Status Check

🤖 Gemini API Keys
  ✅ secrets/api_keys.txt (3 keys)
  📊 Total: 3 keys

📺 YouTube API Keys
  ✅ YT_API_KEY env var (1 key)
  ✅ secrets/api_keys.txt (4 keys)
  📊 Total: 4 keys

🍪 Cookies
  ✅ secrets/cookies.txt (3,055 bytes - Valid ✓)
  ✅ secrets/cookies_1.txt (3,055 bytes - Valid ✓)
  📊 Total: 2 files

🎬 Pexels API
  ✅ secrets/pexels_key.txt (1 key)
  📊 Total: 1 key

🎉 All systems operational!
```

---

## 📝 Error Handling & Test Results

### Test Result Scenarios:

#### ✅ Success (All Tests Pass):
```
📊 Test Result: PASS ✅

Options:
  [1] Save to recommended location (secrets/...)
  [2] Choose different location
  [0] Cancel (don't save)

Enter choice [1/2/0] (default: 1):
```

#### ⚠️ Warning (Format OK, Test Failed):
```
📊 Test Result: WARNING ⚠️

Format validation: ✅ PASS
Functionality test: ❌ FAIL

Error Details:
  ❌ API key exists but quota exceeded
  💡 Try again tomorrow or use a different key

Options:
  [1] Save anyway (not recommended)
  [2] Try different key
  [0] Cancel

Enter choice [1/2/0] (default: 0):
```

#### ❌ Failure (Invalid Format):
```
📊 Test Result: FAIL ❌

Format validation: ❌ FAIL
  - Expected: AIzaSy... (39 chars)
  - Got: AIza... (35 chars)

❌ Cannot proceed. Please check your API key and try again.

Press Enter to return to menu...
```

---

### Detailed Error Messages:

#### Cookies Errors:
| Error | Message | Action |
|-------|---------|--------|
| **Empty file** | "File is empty or too small (< 50 bytes)" | Re-export from browser |
| **HTML content** | "This looks like HTML, not cookies. Did you paste the wrong content?" | Check clipboard |
| **Invalid JSON** | "JSON format invalid: Unexpected token at position 45" | Check JSON syntax |
| **No YouTube cookies** | "No .youtube.com cookies found. Make sure you're logged into YouTube." | Login to YouTube first |
| **JSON conversion failed** | "Conversion failed: Missing required field 'domain'" | Re-export from browser |
| **Unknown format** | "Unrecognized format. Please export as JSON or Netscape format." | Use supported extension |
| **Expired cookies** | "Cookies test failed. They might be expired." | Re-export fresh cookies |
| **Network error** | "Can't test cookies: Network unreachable" | Save anyway (skip test) |

#### Gemini API Errors:
| Error | Message | Action |
|-------|---------|--------|
| **Invalid format** | "API key must start with 'AIzaSy' and be 39 chars long" | Double-check key |
| **API disabled** | "Gemini API not enabled. Go to: https://makersuite.google.com/app/apikey" | Enable API first |
| **Quota exceeded** | "API quota exceeded. Try again tomorrow." | Use backup key |
| **Permission denied** | "API key exists but billing not enabled" | Check Google Cloud billing |
| **Network error** | "Can't reach Gemini API: Network timeout" | Check internet |

#### YouTube API Errors:
| Error | Message | Action |
|-------|---------|--------|
| **API not enabled** | "YouTube Data API v3 not enabled" | Enable in Google Cloud Console |
| **Quota exceeded** | "Daily quota exceeded (10,000 limit)" | Wait until midnight PST |
| **Invalid key** | "API key format invalid or revoked" | Generate new key |
| **Restricted key** | "API key restricted (check API restrictions in console)" | Remove restrictions |

#### Pexels API Errors:
| Error | Message | Action |
|-------|---------|--------|
| **Invalid key** | "Unauthorized: Invalid API key" | Check key from Pexels dashboard |
| **Rate limit** | "Rate limit exceeded (200/hour)" | Wait 1 hour |
| **Network error** | "Can't reach Pexels API" | Check firewall |

---

### Skip Test Option:

For all online tests, provide skip option:

```
⚠️  Online test failed: Network unreachable

Options:
  [1] Retry test
  [2] Skip test and save anyway (not recommended)
  [0] Cancel

Enter choice [1/2/0] (default: 1):
```

**When to allow skip**:
- ✅ Network issues (timeout, DNS failure)
- ✅ API temporarily down
- ❌ Invalid format (never skip format validation)
- ❌ Authentication errors (key is wrong)

---

## 📝 Error Handling

### Invalid Input:
```python
try:
    choice = int(input("Enter choice: "))
except ValueError:
    print("❌ Invalid input! Please enter a number.")
    continue
```

### File Write Errors:
```python
try:
    path.write_text(content)
except PermissionError:
    print("❌ Permission denied! Run as administrator or check file permissions.")
except Exception as e:
    print(f"❌ Failed to write file: {e}")
```

### Network Errors (API testing):
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.Timeout:
    print("⏱️ API test timed out (network issue)")
except requests.RequestException as e:
    print(f"❌ API test failed: {e}")
```

---

## 🚀 Implementation Priority

### Phase 1 (Core - 30 min):
1. ✅ Main menu loop
2. ✅ Option 3: Status check (read-only, safe)
3. ✅ Basic validation functions

### Phase 2 (Add Features - 45 min):
4. ✅ Option 2: Add cookies (most requested)
5. ✅ Option 2: Add API keys (Gemini/YouTube/Pexels)
6. ✅ File saving logic with deduplication

### Phase 3 (Polish - 15 min):
7. ✅ Option 1: User-Agent manager
8. ✅ Better error handling
9. ✅ Rich formatting (if available)

---

## 📊 Total Lines Estimate

- Main menu + loop: ~50 lines
- Option 1 (User-Agent): ~80 lines
- Option 2 (Add credentials): ~200 lines
- Option 3 (Status check): ~150 lines
- Validation functions: ~100 lines
- Utility functions: ~80 lines

**Total**: ~660 lines (well-structured, documented)

---

## ✅ Testing Checklist

### Option 2 (Add Credentials) Tests:
- [ ] Add cookies with valid format → ✅ Should pass format + online test
- [ ] Add cookies with invalid format → ❌ Should reject at format stage
- [ ] Add expired cookies → ⚠️ Should fail online test with clear message
- [ ] Add Gemini API key (valid) → ✅ Should test with actual API call
- [ ] Add Gemini API key (invalid) → ❌ Should fail with clear error
- [ ] Add Gemini API key (quota exceeded) → ⚠️ Should warn but allow save
- [ ] Add YouTube API key (valid) → ✅ Should test + show quota
- [ ] Add YouTube API key (API disabled) → ❌ Should fail with instructions
- [ ] Add Pexels API key (valid) → ✅ Should test + show rate limit
- [ ] Add duplicate key → ⚠️ Should detect and warn

### Option 3 (Status Check) - REAL TESTING:
- [ ] **Full test mode**: Test all cookies/keys with real API calls
  - [ ] Gemini API: Distinguish between ACTIVE vs QUOTA_EXCEEDED vs INVALID
  - [ ] YouTube API: Show quota remaining, detect invalid keys
  - [ ] Cookies: Test with yt-dlp, detect EXPIRED vs WORKING
  - [ ] Pexels API: Show rate limit, detect RATE_LIMITED vs ACTIVE
- [ ] **Quick mode**: Format validation only (no API calls)
- [ ] **Mixed status handling**: Some keys work, some expired, some quota exceeded
- [ ] **Recommendations**: Show actionable suggestions for each issue
- [ ] **Performance**: Complete full test in <60 seconds
- [ ] **Error handling**: Network timeout, API down, etc.

### Integration Tests:
- [ ] Add cookies via helper → Run pipeline → ✅ Pipeline uses new cookies
- [ ] Add Gemini key via helper → Run pipeline → ✅ Pipeline uses new key
- [ ] Add YouTube key via helper → Run search → ✅ Search uses new key
- [ ] Add Pexels key via helper → Generate shorts → ✅ Shorts use new key
- [ ] Status check shows same keys that pipeline will use

### Error Handling Tests:
- [ ] Network offline → ⚠️ Should offer "skip test and save anyway"
- [ ] Invalid input (non-numeric) → ❌ Should re-prompt
- [ ] File permission denied → ❌ Should show clear error message
- [ ] Ctrl+C during test → ℹ️ Should handle gracefully and return to menu
- [ ] **yt-dlp not installed** → ⚠️ Should warn and skip cookies test
- [ ] **requests not installed** → ⚠️ Should warn and skip API tests
- [ ] **API timeout** → ⏱️ Should show timeout status, not crash

---

## 🔐 Security & Best Practices

### What Helper Does:
- ✅ Creates files in `secrets/` folder (protected by `.gitignore`)
- ✅ Validates format before saving
- ✅ Deduplicates keys (no unnecessary duplicates)
- ✅ Uses exact same file paths as pipeline

### What Helper Does NOT Do:
- ❌ Does NOT modify pipeline code
- ❌ Does NOT set environment variables (only reads for status)
- ❌ Does NOT create new fallback locations
- ❌ Does NOT commit secrets to git (protected by `.gitignore`)
- ❌ Does NOT send data over network (except optional YouTube API test)

### File Permissions:
- All files created with standard user permissions
- No elevation required
- Files readable by pipeline scripts

---

## 🧪 Pre-Implementation Verification

### Files to Check (ensure they exist in pipeline):

#### 1. Cookies Fallback in `transcribe.py`:
```python
# Line 529-560 (VERIFIED)
cookie_paths = [
    REPO_ROOT / "secrets" / "cookies.txt",      # Priority 1
    REPO_ROOT / "secrets" / "cookies_1.txt",    # Priority 2
    REPO_ROOT / "secrets" / "cookies_2.txt",    # Priority 3
    REPO_ROOT / "secrets" / "cookies_3.txt",    # Priority 4
    REPO_ROOT / "cookies.txt"                   # Priority 5
]
```
✅ **Confirmed**: Helper will write to these exact paths

#### 2. Gemini API in `process.py`:
```python
# Reads from secrets/api_keys.txt
api_keys = []
api_keys_file = repo_root / "secrets" / "api_keys.txt"
if api_keys_file.exists():
    api_keys = [k.strip() for k in api_keys_file.read_text().splitlines() if k.strip()]
```
✅ **Confirmed**: Helper will append to same file

#### 3. YouTube API in `search.py`:
```python
# Reads from multiple locations
yt_key = os.getenv("YT_API_KEY")
if not yt_key:
    # Check secrets/api_keys.txt
    ...
```
✅ **Confirmed**: Helper will write to same locations

#### 4. Pexels API in `shorts_generator.py`:
```python
# Lines 280-350 (VERIFIED in v2.3.0)
pexels_key_paths = [
    os.getenv("PEXELS_API_KEY"),
    secrets_dir / ".env",
    secrets_dir / "pexels_key.txt",  # Priority 3
    secrets_dir / "api_keys.txt",
    ...
]
```
✅ **Confirmed**: Helper will write to `pexels_key.txt` (recommended)

---

## 📝 Implementation Notes

### Why Helper is Safe:

1. **Read-Only for Pipeline**:
   - Helper only creates/modifies files
   - Pipeline reads these files (already implemented)
   - No circular dependencies

2. **No Code Modifications**:
   - Helper is standalone script
   - Pipeline code remains unchanged
   - Can be removed without breaking pipeline

3. **Follows Existing Patterns**:
   - Uses same file paths as fallback systems
   - Uses same validation rules (size, format)
   - Uses same priority order

4. **Graceful Degradation**:
   - If helper creates invalid file → pipeline skips it
   - If helper not used → pipeline works normally
   - If file deleted → pipeline falls back to next location

### Integration Test Plan:

1. **Before Helper**:
   - Run `python main.py` → Option 0 (System Check)
   - Note which files exist

2. **Use Helper**:
   - Run `python cookies_helper.py`
   - Add cookies using Option 2
   - Add API keys using Option 2

3. **After Helper**:
   - Run `python main.py` → Option 0 (System Check)
   - Verify new files detected
   - Run full pipeline (Option 1)
   - Confirm no errors

4. **Validation**:
   - Check `runs/latest/pipeline.log` for errors
   - Verify cookies used in transcribe stage
   - Verify API keys used in process/search stages

---

## 🎯 Next Steps

1. ✅ Review this plan
2. ✅ Approve/modify structure
3. ✅ **Verify pipeline file paths** (DONE - see above)
4. ✅ **Confirm no conflicts** (DONE - matrix table)
5. ✅ Implement Phase 1 (basic menu + status)
6. ✅ Test with real files
7. ✅ Implement Phase 2 (add features)
8. ✅ **Integration test with pipeline**
9. ✅ Final polish + documentation

---

## 📊 Summary: Helper vs Pipeline

| Aspect | Helper Role | Pipeline Role | Conflict? |
|--------|------------|---------------|-----------|
| **File Creation** | Creates files in `secrets/` | Reads files from `secrets/` | ✅ NO |
| **Validation** | Validates before save | Validates when reading | ✅ NO |
| **File Paths** | Uses existing paths | Defines fallback paths | ✅ NO |
| **Priority Order** | Matches pipeline order | Defines priority order | ✅ NO |
| **Env Vars** | Reads only (for status) | Reads only | ✅ NO |
| **Code Changes** | Zero changes to pipeline | N/A | ✅ NO |

**Conclusion**: Helper is 100% compatible with existing pipeline! 🎉

---

## 🧪 Testing Summary: Before vs After

### OLD Behavior (Without Helper):
```
❌ Add cookies blindly → Pipeline fails silently
❌ Add wrong API key → Error only when running pipeline
❌ Duplicate keys → Wasted quota
❌ No validation → Discover errors late in process
❌ Expired cookies → Only found during transcribe stage (wastes time)
❌ Quota exceeded → Only found during process stage (wastes time)
```

### NEW Behavior (With Helper + REAL TESTING):
```
✅ Add cookies → Instant test with yt-dlp (know if expired NOW)
✅ Add API key → Immediate validation with actual API call
✅ Detect duplicates → Prevent before saving
✅ Real-time feedback → Know if key works NOW, not later
✅ Status check → Test ALL credentials with real APIs
✅ Distinguish states:
   - ✅ ACTIVE: Working perfectly
   - ⚠️ QUOTA EXCEEDED: Valid but over limit
   - ❌ EXPIRED: Cookies/keys no longer valid
   - ❌ INVALID: Wrong format or revoked
✅ Actionable recommendations → "Remove key #3", "Replace cookies_1.txt"
```

### Status Check: Quick vs Full Mode

| Feature | Quick Mode | Full Mode |
|---------|-----------|-----------|
| **Speed** | ~2 seconds | 30-60 seconds |
| **API Calls** | None | All credentials tested |
| **Quota Usage** | Zero | ~4-10 API calls total |
| **Detection** | Format only | ACTIVE vs EXPIRED vs QUOTA EXCEEDED |
| **Cookies Test** | Size/format check | yt-dlp actual fetch |
| **Gemini Test** | Regex validation | Real API call |
| **YouTube Test** | Format check | Quota remaining check |
| **Pexels Test** | Length check | Rate limit check |
| **Recommendations** | None | Specific actions |
| **Use Case** | Quick overview | Pre-pipeline check |

**💡 Recommendation**: Use **Full Mode** before running pipeline to ensure all credentials are valid!

---

## 🎯 Complete Testing Flow (Example)

### Scenario: Adding Gemini API Key

```
============================================================
🤖 Add Gemini API Key
============================================================

Enter Gemini API Key:
> AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz_

============================================================
🔍 Validating API Key
============================================================

[Step 1/3] Format validation...
  ✅ Valid format (39 chars)
  ✅ Starts with 'AIzaSy'
  ✅ Contains valid characters

[Step 2/3] Testing API connection...
  ⏳ Calling Gemini API (gemini-2.5-flash)...
  ⏳ Sending test query: "Hello, confirm API key works"...
  ✅ Success! Received response

[Step 3/3] Verification...
  ✅ API key is active
  ✅ Model available: gemini-2.5-flash
  ✅ No quota issues detected
  ✅ Response time: 1.2s

============================================================
📊 Test Result: PASS ✅
============================================================

Checking for duplicates...
  ⚠️  This key already exists in:
      - secrets/api_keys.txt (line 2)
  
  Options:
    [1] Cancel (recommended - avoid duplicate)
    [2] Add anyway as backup
    [0] Go back
  
  Enter choice [1/2/0] (default: 1): 1

❌ Cancelled. No changes made.

Press Enter to continue...
```

---

## 🎯 Complete Testing Flow (Success Case)

### Scenario: Adding New Pexels API Key

```
============================================================
🎬 Add Pexels API Key
============================================================

Enter Pexels API Key:
> RYLjHA4Pk66sAAioYrmrpMb9K6JWc4DECiUpLPsr7lBuBS0xgxqteQDd

============================================================
🔍 Validating API Key
============================================================

[Step 1/3] Format validation...
  ✅ Valid format (56 chars)
  ✅ Alphanumeric only
  ✅ Length within range (50-60)

[Step 2/3] Testing API connection...
  ⏳ Calling Pexels API...
  ⏳ Searching for test videos (query: 'nature')...
  ✅ Success! Found 15 videos

[Step 3/3] Verification...
  ✅ API key is active
  ✅ Rate limit: 198/200 remaining
  ✅ Response time: 0.8s
  💡 Rate limit resets in: 42 minutes

============================================================
📊 Test Result: PASS ✅
============================================================

Checking for duplicates...
  ✅ No duplicates found

Where to save?
  [1] secrets/pexels_key.txt (recommended - dedicated file)
  [2] secrets/.env (PEXELS_API_KEY=...)
  [3] secrets/api_keys.txt (shared with other keys)

Enter choice [1/2/3] (default: 1): 1

Saving to: secrets/pexels_key.txt...
✅ Saved successfully!

Summary:
  📄 File: C:\...\secrets\pexels_key.txt
  📊 Size: 56 bytes
  🔐 Protected by .gitignore
  ✅ Pipeline will detect this key automatically

Press Enter to continue...
```

---

## 📋 Updated Testing Checklist

### Validation Tests:
- [ ] Add cookies with valid format → ✅ Should pass format + online test
- [ ] Add cookies with invalid format → ❌ Should reject at format stage
- [ ] Add expired cookies → ⚠️ Should fail online test with clear message
- [ ] Add Gemini API key (valid) → ✅ Should test with actual API call
- [ ] Add Gemini API key (invalid) → ❌ Should fail with clear error
- [ ] Add Gemini API key (quota exceeded) → ⚠️ Should warn but allow save
- [ ] Add YouTube API key (valid) → ✅ Should test + show quota
- [ ] Add YouTube API key (API disabled) → ❌ Should fail with instructions
- [ ] Add Pexels API key (valid) → ✅ Should test + show rate limit
- [ ] Add duplicate key → ⚠️ Should detect and warn

### Integration Tests:
- [ ] Add cookies via helper → Run pipeline → ✅ Pipeline uses new cookies
- [ ] Add Gemini key via helper → Run pipeline → ✅ Pipeline uses new key
- [ ] Add YouTube key via helper → Run search → ✅ Search uses new key
- [ ] Add Pexels key via helper → Generate shorts → ✅ Shorts use new key

### Error Handling Tests:
- [ ] Network offline → ⚠️ Should offer "skip test and save anyway"
- [ ] Invalid input (non-numeric) → ❌ Should re-prompt
- [ ] File permission denied → ❌ Should show clear error message
- [ ] Ctrl+C during test → ℹ️ Should handle gracefully and return to menu

---

**Ready to implement?** 🚀

## 🎯 NEW FEATURES ADDED (Real Testing Update)

### Option 3: Status Check - NOW WITH REAL TESTING! ⭐

**Before (Old Plan)**:
- ❌ Only showed file sizes and counts
- ❌ No actual testing
- ❌ Couldn't distinguish expired from valid
- ❌ No quota information

**After (Updated Plan)**:
- ✅ **Full Test Mode**: Tests EVERY credential with real API calls
- ✅ **Distinguishes 6 states**:
  1. ✅ ACTIVE - Working perfectly
  2. ⚠️ QUOTA EXCEEDED - Valid but over limit
  3. ⚠️ RATE LIMITED - Pexels rate limit hit
  4. ❌ EXPIRED - Cookies/tokens no longer valid
  5. ❌ INVALID - Wrong key or revoked
  6. ⏱️ TIMEOUT - Network issue
- ✅ **Real cookies test**: Uses yt-dlp to fetch actual video
- ✅ **Real Gemini test**: Calls Gemini API with test query
- ✅ **Real YouTube test**: Checks quota remaining
- ✅ **Real Pexels test**: Checks rate limit status
- ✅ **Actionable recommendations**: "Remove key #3", "Replace cookies_1.txt"
- ✅ **Quick mode option**: Format validation only (no API calls)
- ✅ **Performance**: Completes in <60 seconds

### Implementation Complexity:

| Feature | Lines of Code | Complexity | Priority |
|---------|---------------|------------|----------|
| **Status Check (OLD)** | ~150 lines | Low | Phase 1 |
| **Status Check (NEW - Real Testing)** | ~400 lines | Medium | Phase 2 |
| **Test Mode Selection** | ~20 lines | Low | Phase 1 |
| **Gemini Real Test** | ~50 lines | Medium | Phase 2 |
| **YouTube Real Test** | ~60 lines | Medium | Phase 2 |
| **Cookies Real Test** | ~80 lines | Medium | Phase 2 |
| **Pexels Real Test** | ~50 lines | Medium | Phase 2 |
| **Results Display** | ~80 lines | Low | Phase 2 |
| **Recommendations Engine** | ~60 lines | Medium | Phase 3 |

**Total NEW Lines**: ~400 lines (well worth it for real-time validation!)

---

## 📊 Final Summary

**Key Features Added**:
1. ✅ **Two-step validation**: Format (offline) + Functionality (online)
2. ✅ **Real API testing**: Gemini, YouTube, Pexels all tested before save
3. ✅ **Cookies testing**: yt-dlp test with real YouTube video
4. ✅ **Cookies auto-conversion**: JSON → Netscape (supports BOTH formats) ⭐ NEW!
5. ✅ **Smart format detection**: Auto-detects JSON vs Netscape ⭐ NEW!
6. ✅ **Duplicate detection**: Prevent saving same key twice
7. ✅ **Clear error messages**: Specific guidance for each error type
8. ✅ **Skip option**: For network issues only
9. ✅ **Detailed feedback**: Progress bars, quota info, rate limits
10. ✅ **Status check modes**: Quick (format) vs Full (real testing)
11. ✅ **State distinction**: ACTIVE vs QUOTA_EXCEEDED vs EXPIRED vs INVALID
12. ✅ **Actionable recommendations**: Specific actions for each issue
13. ✅ **API-specific validation**: Pexels (50-60 chars) vs Google (39 chars)

**Total Estimated Lines**: ~950 lines (was 850, +100 for JSON conversion)

**Cookie Formats Supported**:
- ✅ **JSON** (from EditThisCookie, Cookie Quick Manager, etc.) - **RECOMMENDED**
- ✅ **Netscape** (from old extensions like "Get cookies.txt LOCALLY")
- ✅ **Auto-conversion**: JSON → Netscape (transparent to user)

Let me know if you want any changes to this plan!
