#!/usr/bin/env python3
"""
Test all APIs used in the project
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("🧪 TESTING ALL APIs IN YOUTUBETB PROJECT")
print("="*70)

# Test 1: Gemini API
print("\n📝 [1/5] Testing Gemini API...")
print("-" * 70)
try:
    from src.infrastructure.adapters.process import _configure_model
    model = _configure_model(Path('config'))
    if model:
        print("✅ Gemini API Key found")
        try:
            resp = model.generate_content("Test: Say 'Hello' in one word")
            print(f"✅ Gemini API is WORKING")
            print(f"   Response: {resp.text[:50]}...")
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "SERVICE_DISABLED" in error_msg:
                print(f"❌ Gemini API is DISABLED in Google Cloud Console")
                print(f"   Error: {error_msg[:200]}")
                print(f"   Fix: Enable API at https://console.developers.google.com/apis/api/generativelanguage.googleapis.com")
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"❌ Gemini API QUOTA EXCEEDED")
                print(f"   Error: {error_msg[:200]}")
            else:
                print(f"❌ Gemini API Error: {error_msg[:200]}")
    else:
        print("❌ Gemini API Key NOT found")
except Exception as e:
    print(f"❌ Error testing Gemini: {e}")

# Test 2: YouTube Data API
print("\n📺 [2/5] Testing YouTube Data API...")
print("-" * 70)
try:
    import os
    
    # Check for API key
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        repo_root = Path(__file__).parent
        for f in [repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"]:
            if f.exists():
                api_key = f.read_text(encoding="utf-8").strip()
                break
    
    if api_key:
        print("✅ YouTube API Key found")
        
        # Try a simple API call
        from googleapiclient.discovery import build
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Test with a simple search
        request = youtube.search().list(
            part="snippet",
            q="test",
            maxResults=1,
            type="video"
        )
        response = request.execute()
        print(f"✅ YouTube Data API is WORKING")
        print(f"   Daily Quota: 10,000 points (each search = ~100 points)")
    else:
        print("❌ YouTube API Key NOT found")
except Exception as e:
    error_msg = str(e)
    if "403" in error_msg:
        print(f"❌ YouTube Data API is DISABLED or QUOTA EXCEEDED")
        print(f"   Error: {error_msg[:200]}")
    else:
        print(f"❌ Error testing YouTube API: {error_msg[:200]}")

# Test 3: YouTube Upload (OAuth)
print("\n🎬 [3/5] Testing YouTube Upload API (OAuth)...")
print("-" * 70)
try:
    repo_root = Path(__file__).parent
    client_secret = repo_root / "secrets" / "client_secret.json"
    token_file = repo_root / "secrets" / "token.json"
    
    if client_secret.exists():
        print("✅ client_secret.json found")
    else:
        print("❌ client_secret.json NOT found")
    
    if token_file.exists():
        print("✅ token.json found (OAuth authenticated)")
        
        # Try to validate token
        import json
        token_data = json.loads(token_file.read_text(encoding="utf-8"))
        if "access_token" in token_data:
            print("✅ Access token exists")
        if "refresh_token" in token_data:
            print("✅ Refresh token exists")
    else:
        print("❌ token.json NOT found (need OAuth authentication)")
        print("   Run: python scripts/generate_youtube_token.py")
except Exception as e:
    print(f"❌ Error testing YouTube OAuth: {e}")

# Test 4: Cookies (for YouTube and Amazon scraping)
print("\n🍪 [4/5] Testing Cookies...")
print("-" * 70)
try:
    repo_root = Path(__file__).parent
    cookies_paths = [
        repo_root / "secrets" / "cookies.txt",
        repo_root / "cookies.txt"
    ]
    
    cookies_found = False
    for cookies_path in cookies_paths:
        if cookies_path.exists():
            print(f"✅ Cookies found at: {cookies_path}")
            cookies_found = True
            
            # Check cookie content
            content = cookies_path.read_text(encoding="utf-8")
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
            print(f"   Total cookies: {len(lines)}")
            
            # Check for YouTube cookies
            youtube_cookies = [l for l in lines if 'youtube.com' in l.lower()]
            if youtube_cookies:
                print(f"   ✅ YouTube cookies: {len(youtube_cookies)}")
            else:
                print(f"   ⚠️  No YouTube cookies found")
            
            # Check for Amazon cookies
            amazon_cookies = [l for l in lines if 'amazon.com' in l.lower()]
            if amazon_cookies:
                print(f"   ✅ Amazon cookies: {len(amazon_cookies)}")
            else:
                print(f"   ⚠️  No Amazon cookies found")
            break
    
    if not cookies_found:
        print("❌ Cookies NOT found")
        print("   See: docs/COOKIES_SETUP.md")
except Exception as e:
    print(f"❌ Error testing cookies: {e}")

# Test 5: System Dependencies
print("\n🔧 [5/5] Testing System Dependencies...")
print("-" * 70)

# FFmpeg
try:
    import subprocess
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f"✅ FFmpeg: {version_line[:50]}")
    else:
        print("❌ FFmpeg not working properly")
except FileNotFoundError:
    print("❌ FFmpeg NOT installed")
except Exception as e:
    print(f"❌ FFmpeg error: {e}")

# yt-dlp
try:
    result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"✅ yt-dlp: version {result.stdout.strip()}")
    else:
        print("❌ yt-dlp not working properly")
except FileNotFoundError:
    print("❌ yt-dlp NOT installed")
except Exception as e:
    print(f"❌ yt-dlp error: {e}")

# Playwright
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        if p.chromium.executable_path:
            print(f"✅ Playwright Chromium installed")
        else:
            print("⚠️  Playwright installed but Chromium not found")
except ImportError:
    print("❌ Playwright NOT installed")
except Exception as e:
    print(f"⚠️  Playwright warning: {e}")

# Internet Connection
try:
    import socket
    socket.create_connection(("8.8.8.8", 53), timeout=3)
    print("✅ Internet connection OK")
except Exception:
    print("❌ No internet connection")

print("\n" + "="*70)
print("🏁 API TEST COMPLETE")
print("="*70)
