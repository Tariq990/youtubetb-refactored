#!/usr/bin/env python3
"""Quick test for preflight YouTube API check with enhanced error messages"""

import os
import requests
from pathlib import Path

print("="*80)
print("🧪 Testing Preflight YouTube API Check (Enhanced)")
print("="*80)
print()

repo_root = Path(".")
yt_keys = []

# 1. Environment variable
env_key = os.environ.get("YT_API_KEY")
if env_key:
    yt_keys.append(env_key.strip())
    print(f"✓ Found env key: {env_key[:15]}...")

# 2. Dedicated youtube folder
youtube_path = repo_root / "secrets" / "youtube" / "api_keys.txt"
if youtube_path.exists():
    content = youtube_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key = line.split('#')[0].strip()
            if key and key not in yt_keys:
                yt_keys.append(key)
    print(f"✓ Found {len([l for l in content.splitlines() if l.strip() and not l.startswith('#')])} keys in youtube/api_keys.txt")

# 3. Shared file
api_keys_path = repo_root / "secrets" / "api_keys.txt"
if api_keys_path.exists():
    content = api_keys_path.read_text(encoding="utf-8")
    count_before = len(yt_keys)
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key = line.split('#')[0].strip()
            if key and key not in yt_keys:
                yt_keys.append(key)
    new_keys = len(yt_keys) - count_before
    if new_keys > 0:
        print(f"✓ Found {new_keys} additional keys in api_keys.txt (shared)")

print()
print(f"📋 Total keys loaded: {len(yt_keys)}")
print()

# Test each key
print("Testing all keys:")
print("-"*80)

for i, yt_key in enumerate(yt_keys, start=1):
    print(f"\n[{i}/{len(yt_keys)}] Testing: {yt_key[:15]}...")
    
    try:
        test_url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": "test", "type": "video", "maxResults": 1, "key": yt_key}
        r = requests.get(test_url, params=params, timeout=10)
        
        if r.status_code == 200:
            print(f"  ✅ SUCCESS! Key {i} works")
            break  # Found working key
        elif r.status_code == 403 and "quota" in r.text.lower():
            print(f"  ⚠️  Quota exceeded (but key is valid)")
        else:
            # Enhanced error reporting
            error_msg = f"{r.status_code}"
            try:
                error_data = r.json()
                detailed = error_data.get("error", {}).get("message", "")
                if detailed:
                    error_msg = f"{r.status_code}: {detailed[:100]}"
                    print(f"  ❌ FAILED: {error_msg}")
                    
                    # Show more details
                    errors = error_data.get("error", {}).get("errors", [])
                    if errors:
                        for err in errors[:2]:  # Show first 2 errors
                            reason = err.get("reason", "")
                            domain = err.get("domain", "")
                            print(f"     • Reason: {reason}")
                            print(f"     • Domain: {domain}")
                else:
                    print(f"  ❌ FAILED: {error_msg}")
            except:
                print(f"  ❌ FAILED: {error_msg}")
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)[:100]}")

print()
print("="*80)
