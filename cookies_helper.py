#!/usr/bin/env python3
"""
🍪 Cookies & API Helper v1.1
============================

Unified tool for managing:
- YouTube cookies (JSON → Netscape conversion)
- Gemini API keys
- YouTube Data API keys
- Pexels API keys

Features:
- Automatic format detection
- Pre-save testing with real API calls
- Multi-file fallback support
- Professional logging with rotation
- Automatic backups + rollback
- Input sanitization for security
- Progress indicators

Author: YouTubeTB Project
License: MIT
"""

import os
import sys
import json
import re
import time
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Required for API testing
try:
    import requests
except ImportError:
    print("⚠️  Warning: 'requests' not installed. API testing disabled.")
    print("   Install: pip install requests")
    requests = None

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️  Warning: 'google-generativeai' not installed. Gemini testing disabled.")
    print("   Install: pip install google-generativeai")
    genai = None

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Setup logging with file rotation"""
    log_file = Path("cookies_helper.log")
    
    # Create file handler with rotation (5MB max, 3 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler (warnings only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info("="*50)
    logging.info("Cookies Helper v1.1 started")
    logging.info("="*50)

# Call setup at module load
setup_logging()

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# File paths (absolute)
REPO_ROOT = Path(__file__).resolve().parent
SECRETS_DIR = REPO_ROOT / "secrets"

# Fallback locations for cookies
COOKIES_PATHS = [
    SECRETS_DIR / "cookies.txt",
    SECRETS_DIR / "cookies_1.txt",
    SECRETS_DIR / "cookies_2.txt",
    SECRETS_DIR / "cookies_3.txt",
    REPO_ROOT / "cookies.txt"
]

# API key file paths by type
API_KEYS_PATHS = {
    "gemini": [
        SECRETS_DIR / "api_keys.txt",
        SECRETS_DIR / "api_key.txt",
        SECRETS_DIR / ".env"
    ],
    "youtube": [
        SECRETS_DIR / "api_keys.txt",
        SECRETS_DIR / ".env"
    ],
    "pexels": [
        SECRETS_DIR / "pexels_key.txt",
        SECRETS_DIR / ".env",
        SECRETS_DIR / "api_keys.txt"
    ]
}

# Validation patterns
PATTERNS = {
    "google_api": re.compile(r'^AIzaSy[A-Za-z0-9_-]{33}$'),
    "pexels_api": re.compile(r'^[A-Za-z0-9]{50,60}$')
}

# API endpoints for testing
ENDPOINTS = {
    "youtube": "https://www.googleapis.com/youtube/v3/videos",
    "pexels": "https://api.pexels.com/videos/search",
    "test_video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_secrets_dir():
    """Create secrets/ directory if missing"""
    SECRETS_DIR.mkdir(exist_ok=True)
    logging.debug(f"Ensured secrets directory exists: {SECRETS_DIR}")

def read_multiline_input():
    """
    Read multi-line input until Ctrl+D or 'END'
    Returns: str (full content)
    """
    print("[Press Ctrl+D or type 'END' on new line when done]")
    lines = []
    try:
        while True:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
    except EOFError:
        pass
    
    content = "\n".join(lines)
    logging.debug(f"Read multiline input: {len(content)} bytes")
    return content

def mask_key(key, show_chars=10):
    """
    Mask API key/cookie value
    Example: AIzaSyD11m... (39 chars)
    """
    if len(key) <= show_chars:
        return key
    return f"{key[:show_chars]}... ({len(key)} chars)"

# ============================================================================
# COOKIE FORMAT DETECTION & CONVERSION
# ============================================================================

def detect_cookies_format(content):
    """
    Detect cookies format: json, netscape, html, or unknown
    Returns: str ('json' | 'netscape' | 'html' | 'unknown')
    """
    content = content.strip()
    
    # Check HTML (reject)
    if '<html>' in content.lower() or '<!doctype' in content.lower():
        logging.warning("Detected HTML format (rejected)")
        return 'html'
    
    # Check JSON
    if content.startswith('[') or content.startswith('{'):
        logging.info("Detected JSON format")
        return 'json'
    
    # Check Netscape
    if '# Netscape HTTP Cookie File' in content:
        logging.info("Detected Netscape format")
        return 'netscape'
    
    logging.warning("Unknown cookies format")
    return 'unknown'

def json_to_netscape(json_content):
    """
    Convert JSON cookies to Netscape format
    
    Args:
        json_content (str): JSON string from browser extension
        
    Returns:
        tuple: (netscape_content, error)
               netscape_content is None if error occurred
    """
    try:
        # Parse JSON
        cookies = json.loads(json_content)
        if not isinstance(cookies, list):
            cookies = [cookies]
        
        logging.info(f"Parsing {len(cookies)} cookies from JSON")
        
        # Start with Netscape header
        lines = [
            "# Netscape HTTP Cookie File",
            "# This is a generated file! Do not edit.",
            ""
        ]
        
        kept_count = 0
        
        # Convert each cookie
        for cookie in cookies:
            domain = cookie.get('domain', '')
            
            # Only keep YouTube/Google cookies
            if 'youtube.com' not in domain and 'google.com' not in domain:
                continue
            
            # Extract fields with defaults
            flag = "TRUE" if not cookie.get('hostOnly', False) else "FALSE"
            path = cookie.get('path', '/')
            secure = "TRUE" if cookie.get('secure', False) else "FALSE"
            expiration = int(cookie.get('expirationDate', 0))
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            # Build Netscape line (TAB-separated)
            line = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
            lines.append(line)
            kept_count += 1
        
        if kept_count == 0:
            logging.error("No YouTube/Google cookies found in JSON")
            return None, "No YouTube/Google cookies found in JSON"
        
        netscape_content = "\n".join(lines)
        logging.info(f"Converted {kept_count} cookies to Netscape format")
        return netscape_content, None
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        logging.error(f"Conversion error: {e}")
        return None, f"Conversion failed: {str(e)}"

def validate_netscape_format(content):
    """
    Validate Netscape format cookies
    
    Returns:
        tuple: (valid, error_message)
    """
    # Size check
    if len(content) < 50:
        logging.warning("Cookies file too small")
        return False, "File too small (< 50 bytes)"
    
    # Header check
    if "# Netscape HTTP Cookie File" not in content:
        logging.warning("Missing Netscape header")
        return False, "Missing Netscape header"
    
    # YouTube cookies check
    has_youtube = False
    for line in content.splitlines():
        if '.youtube.com' in line or '.google.com' in line:
            has_youtube = True
            break
    
    if not has_youtube:
        logging.warning("No YouTube/Google cookies found")
        return False, "No YouTube/Google cookies found"
    
    # Line count check
    cookie_lines = [l for l in content.splitlines() 
                    if l.strip() and not l.startswith('#')]
    if len(cookie_lines) < 5:
        logging.warning(f"Too few cookies: {len(cookie_lines)}")
        return False, "Too few cookies (< 5)"
    
    logging.info(f"Validated Netscape format: {len(cookie_lines)} cookies")
    return True, None

# ============================================================================
# API KEY VALIDATION
# ============================================================================

def validate_api_key_format(key, api_type):
    """
    Validate API key format (offline check)
    
    Args:
        key (str): API key to validate
        api_type (str): 'gemini', 'youtube', or 'pexels'
        
    Returns:
        tuple: (valid, error_message)
    """
    key = key.strip()
    
    if api_type in ['gemini', 'youtube']:
        # Google API keys
        if not key.startswith('AIzaSy'):
            return False, "Must start with 'AIzaSy'"
        
        if len(key) != 39:
            return False, f"Must be exactly 39 chars (got {len(key)})"
        
        if not PATTERNS['google_api'].match(key):
            return False, "Invalid characters (use alphanumeric + - _)"
        
        logging.info(f"Valid {api_type} key format")
        return True, None
    
    elif api_type == 'pexels':
        # Pexels API keys
        if len(key) < 50 or len(key) > 60:
            return False, f"Must be 50-60 chars (got {len(key)})"
        
        if not key.isalnum():
            return False, "Must be alphanumeric only (no special chars)"
        
        if not PATTERNS['pexels_api'].match(key):
            return False, "Invalid format"
        
        logging.info("Valid Pexels key format")
        return True, None
    
    return False, f"Unknown API type: {api_type}"

# ============================================================================
# API TESTING FUNCTIONS
# ============================================================================

def test_cookies_with_ytdlp(cookies_path):
    """
    Test cookies by fetching a YouTube video with yt-dlp
    
    Args:
        cookies_path (Path): Path to cookies file
        
    Returns:
        tuple: (success, message)
    """
    logging.info(f"Testing cookies: {cookies_path}")
    
    cmd = [
        "yt-dlp",
        "--cookies", str(cookies_path),
        "--skip-download",
        "--print", "title",
        ENDPOINTS['test_video']
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
            logging.info(f"Cookies test passed: {cookies_path}")
            return True, "Successfully fetched video title"
        
        logging.warning(f"Cookies test failed: {cookies_path}")
        return False, "Failed to fetch video data"
        
    except subprocess.TimeoutExpired:
        logging.error(f"Cookies test timeout: {cookies_path}")
        return False, "Timeout (network issue?)"
    
    except subprocess.CalledProcessError as e:
        error = e.stderr or e.stdout or ""
        logging.error(f"Cookies test error: {error[:100]}")
        
        if "403" in error or "Forbidden" in error:
            return False, "HTTP 403: Cookies expired"
        elif "401" in error:
            return False, "HTTP 401: Cookies invalid"
        return False, f"yt-dlp error: {error[:50]}"
    
    except FileNotFoundError:
        logging.error("yt-dlp not found")
        return False, "yt-dlp not installed"
    
    except Exception as e:
        logging.error(f"Cookies test exception: {e}")
        return False, f"Test failed: {str(e)}"

def test_gemini_api(api_key):
    """
    Test Gemini API key with real API call
    
    Returns:
        tuple: (success, message, details_dict)
    """
    if not genai:
        logging.warning("Gemini module not available")
        return False, "Module not installed", {}
    
    logging.info(f"Testing Gemini API: {mask_key(api_key)}")
    
    try:
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel('gemini-2.5-flash')  # type: ignore
        
        start = time.time()
        response = model.generate_content("Reply: 'API key works'")
        elapsed = time.time() - start
        
        if response and response.text:
            logging.info(f"Gemini API test passed: {elapsed:.1f}s")
            return True, "API key works", {
                "model": "gemini-2.5-flash",
                "response_time": round(elapsed, 1)
            }
        
        logging.warning("Gemini API empty response")
        return False, "Empty response", {}
        
    except Exception as e:
        error = str(e).upper()
        logging.error(f"Gemini API test failed: {e}")
        
        if "QUOTA_EXCEEDED" in error or "QUOTA EXCEEDED" in error:
            return False, "QUOTA_EXCEEDED", {}
        elif "API_KEY_INVALID" in error or "INVALID" in error:
            return False, "API_KEY_INVALID", {}
        elif "PERMISSION_DENIED" in error:
            return False, "PERMISSION_DENIED", {}
        return False, f"Error: {str(e)[:50]}", {}

def test_youtube_api(api_key):
    """
    Test YouTube Data API key
    
    Returns:
        tuple: (success, message, quota_info)
    """
    if not requests:
        logging.warning("Requests module not available")
        return False, "Module not installed", ""
    
    logging.info(f"Testing YouTube API: {mask_key(api_key)}")
    
    try:
        params = {
            "part": "snippet",
            "id": "dQw4w9WgXcQ",
            "key": api_key
        }
        
        response = requests.get(ENDPOINTS['youtube'], params=params, timeout=10)
        
        if response.status_code == 200:
            logging.info("YouTube API test passed")
            return True, "API key works", "Quota info unavailable"
        elif response.status_code == 403:
            error = response.json().get("error", {})
            reason = error.get("errors", [{}])[0].get("reason", "")
            if reason == "quotaExceeded":
                logging.warning("YouTube API quota exceeded")
                return False, "QUOTA_EXCEEDED", "10,000 limit"
            logging.error(f"YouTube API forbidden: {reason}")
            return False, f"Forbidden: {reason}", ""
        elif response.status_code == 400:
            logging.error("YouTube API invalid key format")
            return False, "Invalid API key format", ""
        else:
            logging.error(f"YouTube API HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}", ""
            
    except requests.Timeout:
        logging.error("YouTube API timeout")
        return False, "Timeout", ""
    except Exception as e:
        logging.error(f"YouTube API test exception: {e}")
        return False, f"Error: {str(e)[:50]}", ""

def test_pexels_api(api_key):
    """
    Test Pexels API key
    
    Returns:
        tuple: (success, message, rate_limit_info)
    """
    if not requests:
        logging.warning("Requests module not available")
        return False, "Module not installed", ""
    
    logging.info(f"Testing Pexels API: {mask_key(api_key)}")
    
    try:
        headers = {"Authorization": api_key}
        params = {"query": "nature", "per_page": 1}
        
        response = requests.get(
            ENDPOINTS['pexels'],
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            limit = response.headers.get("X-Ratelimit-Limit", "200")
            remaining = response.headers.get("X-Ratelimit-Remaining", "?")
            logging.info(f"Pexels API test passed: {remaining}/{limit}")
            return True, "API key works", f"{remaining}/{limit}"
        elif response.status_code == 401:
            logging.error("Pexels API unauthorized")
            return False, "Unauthorized", ""
        elif response.status_code == 429:
            logging.warning("Pexels API rate limited")
            return False, "RATE_LIMITED", "200/hour"
        else:
            logging.error(f"Pexels API HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}", ""
            
    except requests.Timeout:
        logging.error("Pexels API timeout")
        return False, "Timeout", ""
    except Exception as e:
        logging.error(f"Pexels API test exception: {e}")
        return False, f"Error: {str(e)[:50]}", ""

# ============================================================================
# FILE OPERATIONS
# ============================================================================

def find_empty_cookies_slot():
    """
    Find first empty cookies slot
    
    Returns:
        Path or None
    """
    for path in COOKIES_PATHS[:4]:  # Only writable slots
        if not path.exists() or path.stat().st_size < 50:
            logging.debug(f"Found empty slot: {path}")
            return path
    logging.debug("No empty slots found")
    return None

def clean_old_backups(file_path, keep=5):
    """Keep only last N backup files"""
    try:
        pattern = f"{file_path.stem}.*.bak"
        backups = sorted(
            file_path.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Delete old backups
        for backup in backups[keep:]:
            backup.unlink()
            logging.debug(f"Deleted old backup: {backup}")
    except Exception as e:
        logging.warning(f"Failed to clean backups: {e}")

def save_to_file(path, content):
    """
    Save content to file with backup and error handling
    
    Returns:
        tuple: (success, error_message)
    """
    backup_path = None
    
    try:
        # Create parent directory
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing file
        if path.exists() and path.stat().st_size > 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.with_suffix(f'.{timestamp}.bak')
            shutil.copy2(path, backup_path)
            logging.info(f"Created backup: {backup_path}")
        
        # Write new content
        path.write_text(content, encoding='utf-8')
        logging.info(f"Saved file: {path} ({len(content)} bytes)")
        
        # Verify written content
        if path.read_text(encoding='utf-8') != content:
            raise IOError("Content verification failed")
        
        # Clean old backups (keep last 5)
        clean_old_backups(path, keep=5)
        
        return True, None
        
    except PermissionError:
        logging.error(f"Permission denied: {path}")
        # Rollback
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(path))
            logging.info("Rolled back to backup")
        return False, "Permission denied"
    
    except OSError as e:
        logging.error(f"OS error saving {path}: {e}")
        # Rollback
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(path))
            logging.info("Rolled back to backup")
        
        if e.errno == 28:  # Disk full
            return False, "Disk full - free up space"
        elif e.errno == 36:  # Filename too long
            return False, "Filename too long"
        return False, f"OS error: {e.strerror}"
    
    except UnicodeEncodeError:
        logging.error(f"Unicode error: {path}")
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(path))
        return False, "Invalid characters in content"
    
    except Exception as e:
        logging.error(f"Unexpected error saving {path}: {e}")
        # Rollback
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(path))
            logging.info("Rolled back to backup")
        return False, f"Write failed: {str(e)}"

def append_to_api_keys(path, key):
    """
    Append API key to file (deduplicates)
    
    Returns:
        tuple: (success, message)
    """
    # Read existing
    existing = []
    if path.exists():
        existing = [k.strip() for k in path.read_text().splitlines() if k.strip()]
    
    # Deduplicate
    if key in existing:
        logging.warning(f"Key already exists in {path}")
        return False, "Key already exists"
    
    # Append
    existing.append(key)
    content = "\n".join(existing) + "\n"
    
    success, error = save_to_file(path, content)
    if success:
        logging.info(f"Appended key to {path}")
        return True, f"Saved to {path.name}"
    return False, error

def update_env_file(var_name, value):
    """
    Update or add variable in .env file (with sanitization)
    
    Returns:
        tuple: (success, message)
    """
    # Sanitize inputs
    var_name = var_name.strip().upper()
    value = value.strip()
    
    # Remove dangerous characters
    var_name = var_name.replace('\n', '').replace('\r', '')
    value = value.replace('\n', '').replace('\r', '')
    
    # Validate var name
    if not re.match(r'^[A-Z_][A-Z0-9_]*$', var_name):
        logging.error(f"Invalid env var name: {var_name}")
        return False, f"Invalid variable name: {var_name}"
    
    env_path = SECRETS_DIR / ".env"
    
    # Read existing
    if env_path.exists():
        content = env_path.read_text()
    else:
        content = ""
    
    # Update or append
    pattern = rf'^{var_name}=.*$'
    if re.search(pattern, content, re.MULTILINE):
        # Update existing
        content = re.sub(pattern, f'{var_name}={value}', content, flags=re.MULTILINE)
        logging.info(f"Updated env var: {var_name}")
    else:
        # Append new
        if content and not content.endswith('\n'):
            content += '\n'
        content += f'{var_name}={value}\n'
        logging.info(f"Added env var: {var_name}")
    
    success, error = save_to_file(env_path, content)
    if success:
        return True, f"Updated {env_path.name}"
    return False, error

# ============================================================================
# OPTION 1: USER-AGENT MANAGER
# ============================================================================

def option_1_user_agent():
    """
    User-Agent manager (simple implementation)
    """
    print("\n" + "="*60)
    print("👤 User-Agent Manager")
    print("="*60)
    print("\n⚠️  Note: This feature is not yet integrated with pipeline.")
    print("Press Enter to return to main menu...")
    input()
    logging.info("User-Agent manager accessed (not implemented)")

# ============================================================================
# OPTION 2: ADD CREDENTIALS
# ============================================================================

def add_cookies():
    """
    Add YouTube cookies (supports JSON & Netscape)
    """
    print("\n" + "="*60)
    print("🍪 Add YouTube Cookies")
    print("="*60)
    
    print("\nInstructions:")
    print("1. Export cookies from browser extension")
    print("   - EditThisCookie (Chrome) - JSON format ✅")
    print("   - Cookie Quick Manager (Firefox) - JSON ✅")
    print("   - Get cookies.txt LOCALLY - Netscape format")
    print("\n2. Login to YouTube.com first")
    print("\n3. Paste cookies below:")
    
    # Read input
    content = read_multiline_input()
    
    if not content.strip():
        print("❌ Empty input")
        return
    
    # Detect format
    print("\nDetecting format...")
    format_type = detect_cookies_format(content)
    
    if format_type == 'html':
        print("❌ This is HTML, not cookies!")
        return
    elif format_type == 'unknown':
        print("❌ Unknown format. Use JSON or Netscape.")
        return
    
    # Convert if needed
    if format_type == 'json':
        print(f"✅ Detected: JSON format")
        print("\nConverting to Netscape...")
        
        netscape, error = json_to_netscape(content)
        if error:
            print(f"❌ Conversion failed: {error}")
            return
        
        # Ensure netscape is not None before using it
        if netscape is None:
            print(f"❌ Conversion failed: No content")
            return
        
        print("✅ Converted successfully")
        cookie_count = len([l for l in netscape.splitlines() 
                           if l.strip() and not l.startswith('#')])
        print(f"   • Kept: {cookie_count} YouTube/Google cookies")
        print(f"   • Size: {len(netscape):,} bytes")
        
        final_content = netscape
    else:
        print(f"✅ Detected: Netscape format")
        final_content = content
    
    # Validate
    print("\nValidating...")
    valid, error = validate_netscape_format(final_content)
    if not valid:
        print(f"❌ Validation failed: {error}")
        return
    print("✅ Valid format")
    
    # Test with yt-dlp
    print("\nTesting cookies...")
    temp_path = Path("temp_cookies_test.txt")
    
    # Ensure final_content exists before writing
    if not final_content:
        print("❌ No content to save")
        return
    
    temp_path.write_text(final_content)
    
    try:
        success, message = test_cookies_with_ytdlp(temp_path)
        if success:
            print(f"✅ {message}")
        else:
            print(f"⚠️  Test failed: {message}")
            confirm = input("\nSave anyway? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
    finally:
        if temp_path.exists():
            temp_path.unlink()
    
    # Find slot
    slot = find_empty_cookies_slot()
    if not slot:
        print("\n⚠️  All slots full!")
        print("Choose slot to overwrite:")
        for i, path in enumerate(COOKIES_PATHS[:4], 1):
            size = path.stat().st_size if path.exists() else 0
            print(f"  [{i}] {path.name} ({size:,} bytes)")
        print("  [0] Cancel")
        
        choice = input("\nChoice: ").strip()
        if choice in ['1', '2', '3', '4']:
            slot = COOKIES_PATHS[int(choice) - 1]
        else:
            print("❌ Cancelled")
            return
    
    # Save
    print(f"\nSaving to: {slot}...")
    
    # Ensure final_content exists before saving
    if not final_content:
        print("❌ No content to save")
        return
    
    success, error = save_to_file(slot, final_content)
    
    if success:
        print(f"✅ Saved successfully!")
        print(f"   File: {slot}")
        print(f"   Size: {len(final_content):,} bytes")
    else:
        print(f"❌ Save failed: {error}")

def add_gemini_api():
    """Add Gemini API key"""
    print("\n" + "="*60)
    print("🤖 Add Gemini API Key")
    print("="*60)
    
    print("\nInstructions:")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Create API Key")
    print("3. Copy key (starts with 'AIzaSy...')")
    
    # Get key
    key = input("\nEnter Gemini API Key: ").strip()
    if not key:
        print("❌ Empty input")
        return
    
    # Sanitize
    key = key.replace('\n', '').replace('\r', '').strip('"').strip("'")
    
    # Validate format
    print("\nValidating format...")
    valid, error = validate_api_key_format(key, 'gemini')
    if not valid:
        print(f"❌ {error}")
        return
    print("✅ Valid format (39 chars)")
    
    # Test API
    print("\nTesting API...")
    success, message, details = test_gemini_api(key)
    if success:
        print(f"✅ {message}")
        print(f"   Model: {details.get('model')}")
        print(f"   Response time: {details.get('response_time')}s")
    else:
        print(f"⚠️  Test failed: {message}")
        if message != "QUOTA_EXCEEDED":
            confirm = input("\nSave anyway? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
    
    # Choose location
    print("\nWhere to save?")
    print("  [1] secrets/api_keys.txt (recommended)")
    print("  [2] secrets/.env (GEMINI_API_KEY=...)")
    print("  [0] Cancel")
    
    choice = input("\nChoice [1/2/0] (default: 1): ").strip() or '1'
    
    if choice == '1':
        path = SECRETS_DIR / "api_keys.txt"
        success, message = append_to_api_keys(path, key)
    elif choice == '2':
        success, message = update_env_file("GEMINI_API_KEY", key)
    else:
        print("❌ Cancelled")
        return
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")

def add_youtube_api():
    """Add YouTube API key"""
    print("\n" + "="*60)
    print("📺 Add YouTube Data API Key")
    print("="*60)
    
    print("\nInstructions:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Create API Key")
    print("3. Enable YouTube Data API v3")
    print("4. Copy key (starts with 'AIzaSy...')")
    
    # Get key
    key = input("\nEnter YouTube API Key: ").strip()
    if not key:
        print("❌ Empty input")
        return
    
    # Sanitize
    key = key.replace('\n', '').replace('\r', '').strip('"').strip("'")
    
    # Validate format
    print("\nValidating format...")
    valid, error = validate_api_key_format(key, 'youtube')
    if not valid:
        print(f"❌ {error}")
        return
    print("✅ Valid format (39 chars)")
    
    # Test API
    print("\nTesting API...")
    success, message, quota = test_youtube_api(key)
    if success:
        print(f"✅ {message}")
        if quota:
            print(f"   Quota: {quota}")
    else:
        print(f"⚠️  Test failed: {message}")
        if message != "QUOTA_EXCEEDED":
            confirm = input("\nSave anyway? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
    
    # Choose location
    print("\nWhere to save?")
    print("  [1] secrets/api_keys.txt (recommended)")
    print("  [2] secrets/.env (YT_API_KEY=...)")
    print("  [0] Cancel")
    
    choice = input("\nChoice [1/2/0] (default: 1): ").strip() or '1'
    
    if choice == '1':
        path = SECRETS_DIR / "api_keys.txt"
        success, message = append_to_api_keys(path, key)
    elif choice == '2':
        success, message = update_env_file("YT_API_KEY", key)
    else:
        print("❌ Cancelled")
        return
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")

def add_pexels_api():
    """Add Pexels API key"""
    print("\n" + "="*60)
    print("🎬 Add Pexels API Key")
    print("="*60)
    
    print("\nInstructions:")
    print("1. Go to: https://www.pexels.com/api/")
    print("2. Sign up for free account")
    print("3. Copy your API key from dashboard")
    
    # Get key
    key = input("\nEnter Pexels API Key: ").strip()
    if not key:
        print("❌ Empty input")
        return
    
    # Sanitize
    key = key.replace('\n', '').replace('\r', '').strip('"').strip("'")
    
    # Validate format
    print("\nValidating format...")
    valid, error = validate_api_key_format(key, 'pexels')
    if not valid:
        print(f"❌ {error}")
        return
    print(f"✅ Valid format ({len(key)} chars)")
    
    # Test API
    print("\nTesting API...")
    success, message, rate_limit = test_pexels_api(key)
    if success:
        print(f"✅ {message}")
        if rate_limit:
            print(f"   Rate limit: {rate_limit}")
    else:
        print(f"⚠️  Test failed: {message}")
        if message != "RATE_LIMITED":
            confirm = input("\nSave anyway? [y/N]: ").strip().lower()
            if confirm != 'y':
                return
    
    # Choose location
    print("\nWhere to save?")
    print("  [1] secrets/pexels_key.txt (recommended)")
    print("  [2] secrets/.env (PEXELS_API_KEY=...)")
    print("  [3] secrets/api_keys.txt (shared)")
    print("  [0] Cancel")
    
    choice = input("\nChoice [1/2/3/0] (default: 1): ").strip() or '1'
    
    if choice == '1':
        path = SECRETS_DIR / "pexels_key.txt"
        success, error = save_to_file(path, key + "\n")
        message = f"Saved to {path.name}" if success else error
    elif choice == '2':
        success, message = update_env_file("PEXELS_API_KEY", key)
    elif choice == '3':
        path = SECRETS_DIR / "api_keys.txt"
        success, message = append_to_api_keys(path, key)
    else:
        print("❌ Cancelled")
        return
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")

def option_2_add_credentials():
    """
    Add cookies or API keys (main dispatcher)
    """
    while True:
        print("\n" + "="*60)
        print("➕ Add Cookies or API Keys")
        print("="*60)
        print("\n  [1] 🍪 Cookies (YouTube)")
        print("  [2] 🤖 Gemini API Key")
        print("  [3] 📺 YouTube Data API Key")
        print("  [4] 🎬 Pexels API Key")
        print("  [0] Back to main menu")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            add_cookies()
        elif choice == '2':
            add_gemini_api()
        elif choice == '3':
            add_youtube_api()
        elif choice == '4':
            add_pexels_api()
        elif choice == '0':
            break
        else:
            print("❌ Invalid choice")

# ============================================================================
# OPTION 3: STATUS CHECK
# ============================================================================

def check_cookies_status(test_mode):
    """
    Check cookies files status
    """
    print("\n🍪 YouTube Cookies")
    print("-" * 60)
    
    working = 0
    expired = 0
    
    for path in COOKIES_PATHS:
        if not path.exists():
            print(f"  ❌ {path.name} - NOT FOUND")
            continue
        
        size = path.stat().st_size
        print(f"\n  {path.name}:")
        print(f"    Size: {size:,} bytes")
        
        if test_mode == 'full':
            success, message = test_cookies_with_ytdlp(path)
            if success:
                print(f"    ✅ WORKING - {message}")
                working += 1
            else:
                print(f"    ❌ EXPIRED - {message}")
                expired += 1
        else:
            print(f"    🔒 FORMAT VALID (not tested)")
    
    print(f"\n  📊 Summary:")
    print(f"    ✅ Working: {working}")
    print(f"    ❌ Expired: {expired}")
    if expired > 0:
        print(f"    💡 Recommendation: Replace expired cookies")

def check_gemini_status(test_mode):
    """Check Gemini API keys"""
    print("\n🤖 Gemini API Keys")
    print("-" * 60)
    
    working = 0
    quota_exceeded = 0
    invalid = 0
    
    # Check api_keys.txt
    api_keys_path = SECRETS_DIR / "api_keys.txt"
    if api_keys_path.exists():
        # Parse keys and strip inline comments
        keys = []
        for line in api_keys_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove inline comments (split on # or whitespace)
                key = line.split('#')[0].strip()
                if key:
                    keys.append(key)
        
        for idx, key in enumerate(keys, 1):
            # Skip if not Gemini key (check length)
            if len(key) != 39:
                continue
                
            print(f"\n  Key {idx}: {mask_key(key)}")
            
            if test_mode == 'full':
                success, message, details = test_gemini_api(key)
                if success:
                    print(f"    ✅ ACTIVE - {message}")
                    print(f"       Model: {details.get('model')}")
                    print(f"       Response: {details.get('response_time')}s")
                    working += 1
                elif message == "QUOTA_EXCEEDED":
                    print(f"    ⚠️  QUOTA EXCEEDED")
                    quota_exceeded += 1
                else:
                    print(f"    ❌ INVALID - {message}")
                    invalid += 1
            else:
                print(f"    🔒 FORMAT VALID (not tested)")
    
    # Check .env
    env_path = SECRETS_DIR / ".env"
    if env_path.exists():
        content = env_path.read_text()
        match = re.search(r'^GEMINI_API_KEY=(.+)$', content, re.MULTILINE)
        if match:
            key = match.group(1).strip()
            print(f"\n  .env: {mask_key(key)}")
            
            if test_mode == 'full':
                success, message, details = test_gemini_api(key)
                if success:
                    print(f"    ✅ ACTIVE - {message}")
                    if details.get('model'):
                        print(f"       Model: {details.get('model')}")
                    if details.get('response_time'):
                        print(f"       Response: {details.get('response_time')}s")
                    working += 1
                elif message == "QUOTA_EXCEEDED":
                    print(f"    ⚠️  QUOTA EXCEEDED")
                    quota_exceeded += 1
                else:
                    print(f"    ❌ {message}")
                    invalid += 1
    
    print(f"\n  📊 Summary:")
    print(f"    ✅ Working: {working}")
    print(f"    ⚠️  Quota exceeded: {quota_exceeded}")
    print(f"    ❌ Invalid: {invalid}")
    if quota_exceeded > 0:
        print(f"    💡 Recommendation: Use working keys, quota resets daily")

def check_youtube_status(test_mode):
    """Check YouTube API keys"""
    print("\n📺 YouTube Data API Keys")
    print("-" * 60)
    
    working = 0
    quota_exceeded = 0
    invalid = 0
    
    # Check api_keys.txt
    api_keys_path = SECRETS_DIR / "api_keys.txt"
    if api_keys_path.exists():
        # Parse keys and strip inline comments
        keys = []
        for line in api_keys_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove inline comments (split on # or whitespace)
                key = line.split('#')[0].strip()
                if key:
                    keys.append(key)
        
        for idx, key in enumerate(keys, 1):
            # Skip if not Google key
            if len(key) != 39:
                continue
                
            print(f"\n  Key {idx}: {mask_key(key)}")
            
            if test_mode == 'full':
                success, message, quota = test_youtube_api(key)
                if success:
                    print(f"    ✅ ACTIVE - {message}")
                    if quota:
                        print(f"       {quota}")
                    working += 1
                elif message == "QUOTA_EXCEEDED":
                    print(f"    ⚠️  QUOTA EXCEEDED")
                    quota_exceeded += 1
                else:
                    print(f"    ❌ INVALID - {message}")
                    invalid += 1
            else:
                print(f"    🔒 FORMAT VALID (not tested)")
    
    # Check .env
    env_path = SECRETS_DIR / ".env"
    if env_path.exists():
        content = env_path.read_text()
        match = re.search(r'^YT_API_KEY=(.+)$', content, re.MULTILINE)
        if match:
            key = match.group(1).strip()
            print(f"\n  .env: {mask_key(key)}")
            
            if test_mode == 'full':
                success, message, quota = test_youtube_api(key)
                if success:
                    print(f"    ✅ ACTIVE - {message}")
                    if quota:
                        print(f"       {quota}")
                    working += 1
                elif message == "QUOTA_EXCEEDED":
                    print(f"    ⚠️  QUOTA EXCEEDED")
                    quota_exceeded += 1
                else:
                    print(f"    ❌ {message}")
                    invalid += 1
    
    print(f"\n  📊 Summary:")
    print(f"    ✅ Working: {working}")
    print(f"    ⚠️  Quota exceeded: {quota_exceeded}")
    print(f"    ❌ Invalid: {invalid}")
    if invalid > 0:
        print(f"    💡 Recommendation: Remove invalid keys from api_keys.txt")

def check_pexels_status(test_mode):
    """Check Pexels API keys"""
    print("\n🎬 Pexels API Key")
    print("-" * 60)
    
    working = 0
    rate_limited = 0
    invalid = 0
    
    # Check pexels_key.txt
    pexels_path = SECRETS_DIR / "pexels_key.txt"
    if pexels_path.exists():
        key = pexels_path.read_text().strip()
        print(f"\n  pexels_key.txt: {mask_key(key)}")
        
        if test_mode == 'full':
            success, message, rate_limit = test_pexels_api(key)
            if success:
                print(f"    ✅ ACTIVE - {message}")
                if rate_limit:
                    print(f"       Rate limit: {rate_limit}")
                working += 1
            elif message == "RATE_LIMITED":
                print(f"    ⚠️  RATE LIMITED (200/hour)")
                rate_limited += 1
            else:
                print(f"    ❌ INVALID - {message}")
                invalid += 1
        else:
            print(f"    🔒 FORMAT VALID (not tested)")
    
    # Check .env
    env_path = SECRETS_DIR / ".env"
    if env_path.exists():
        content = env_path.read_text()
        match = re.search(r'^PEXELS_API_KEY=(.+)$', content, re.MULTILINE)
        if match:
            key = match.group(1).strip()
            print(f"\n  .env: {mask_key(key)}")
            
            if test_mode == 'full':
                success, message, rate_limit = test_pexels_api(key)
                if success:
                    print(f"    ✅ ACTIVE - {message}")
                    if rate_limit:
                        print(f"       Rate limit: {rate_limit}")
                    working += 1
                else:
                    print(f"    ❌ {message}")
    
    print(f"\n  📊 Summary:")
    print(f"    ✅ Working: {working}")
    print(f"    ⚠️  Rate limited: {rate_limited}")
    print(f"    ❌ Invalid: {invalid}")
    if rate_limited > 0:
        print(f"    💡 Recommendation: Wait for rate limit reset (1 hour)")

def option_3_status_check():
    """
    Quick status check with optional real testing
    """
    print("\n" + "="*60)
    print("🔍 Quick Status Check")
    print("="*60)
    
    print("\n⚠️  This will test ALL cookies/keys with real API calls.")
    print("   Takes 30-60 seconds and consumes quota.")
    
    print("\nOptions:")
    print("  [1] Full test (test everything)")
    print("  [2] Quick check (format only)")
    print("  [0] Back")
    
    choice = input("\nChoice [1/2/0] (default: 1): ").strip() or '1'
    
    if choice == '1':
        test_mode = 'full'
        logging.info("Starting FULL status check")
    elif choice == '2':
        test_mode = 'quick'
        logging.info("Starting QUICK status check")
    else:
        return
    
    print("\n" + "="*60)
    if test_mode == 'full':
        print("⏳ Testing all credentials (this may take 30-60s)...")
    print("="*60)
    
    # Check each system with progress
    systems = [
        ("🤖 Gemini API", check_gemini_status),
        ("📺 YouTube API", check_youtube_status),
        ("🍪 Cookies", check_cookies_status),
        ("🎬 Pexels API", check_pexels_status)
    ]
    
    total = len(systems)
    for idx, (name, func) in enumerate(systems, 1):
        print(f"\n[{idx}/{total}] {name}...")
        print("=" * 60)
        func(test_mode)
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    logging.info("Status check completed")
    
    print("\nPress Enter to continue...")
    input()

# ============================================================================
# MAIN MENU & LOOP
# ============================================================================

def show_main_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("🍪 Cookies & API Helper v1.1")
    print("="*60)
    print("\n  [1] 👤 Set User-Agent")
    print("  [2] ➕ Add Cookies or API Keys")
    print("  [3] 🔍 Quick Status Check")
    print("  [0] 🚪 Exit")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🍪 Cookies & API Helper v1.1")
    print("="*60)
    print("\nFeatures:")
    print("  • JSON → Netscape cookie conversion")
    print("  • Real API testing before save")
    print("  • Automatic backups + rollback")
    print("  • Professional logging")
    print("="*60)
    
    # Ensure secrets dir exists
    ensure_secrets_dir()
    
    # Main loop
    while True:
        show_main_menu()
        choice = input("\nEnter choice [0/1/2/3]: ").strip()
        
        if choice == '1':
            option_1_user_agent()
        elif choice == '2':
            option_2_add_credentials()
        elif choice == '3':
            option_3_status_check()
        elif choice == '0':
            print("\n👋 Goodbye!")
            logging.info("Cookies Helper exited normally")
            break
        else:
            print("\n❌ Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logging.warning("Interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
