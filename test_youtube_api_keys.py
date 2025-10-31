#!/usr/bin/env python3
"""Test YouTube API keys to find the problem"""

import requests
import sys

# The 3 keys from youtube/api_keys.txt
keys = [
    "AIzaSyD11mUVE7OtxHgsdV6kfJsDQZvAHStjNbA",
    "AIzaSyAUxXkiTOaEEUdFk7VVJC0vRZU1KTF_qoY",
    "AIzaSyDWA-KyDTunzqBredT1w0B9NpV-aNB-jKU"
]

print("="*80)
print("🧪 Testing YouTube API Keys")
print("="*80)
print()

endpoint = "https://www.googleapis.com/youtube/v3/videos"
test_video_id = "dQw4w9WgXcQ"

for i, key in enumerate(keys, 1):
    print(f"[{i}/3] Testing: {key[:15]}...")
    
    try:
        params = {
            "part": "snippet",
            "id": test_video_id,
            "key": key
        }
        
        resp = requests.get(endpoint, params=params, timeout=10)
        
        if resp.status_code == 200:
            print(f"  ✅ SUCCESS! Key works")
        elif resp.status_code == 403:
            error = resp.json().get("error", {})
            reason = error.get("errors", [{}])[0].get("reason", "unknown")
            message = error.get("message", "")
            
            if "quotaExceeded" in reason:
                print(f"  ⚠️  QUOTA EXCEEDED (but key is valid)")
            elif "API_NOT_ENABLED" in message or "has not been used" in message:
                print(f"  ❌ API NOT ENABLED")
                print(f"     Message: {message[:100]}")
            else:
                print(f"  ❌ FORBIDDEN: {reason}")
                print(f"     Message: {message[:100]}")
        elif resp.status_code == 400:
            error = resp.json().get("error", {})
            message = error.get("message", "")
            print(f"  ❌ BAD REQUEST (400)")
            print(f"     Message: {message}")
            print(f"     Full response: {resp.text[:300]}")
        else:
            print(f"  ❌ HTTP {resp.status_code}")
            print(f"     Response: {resp.text[:200]}")
    
    except requests.Timeout:
        print(f"  ❌ TIMEOUT")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    
    print()

print("="*80)
print("💡 Diagnosis:")
print("="*80)
print()
print("If you see '400 Bad Request':")
print("  1. API key is INVALID or REVOKED")
print("  2. YouTube Data API v3 is NOT ENABLED for this key")
print("  3. Need to create NEW API keys")
print()
print("If you see '403 Quota Exceeded':")
print("  1. API key is VALID")
print("  2. Just wait 24 hours for quota reset")
print()
print("If you see '403 API Not Enabled':")
print("  1. Go to: https://console.cloud.google.com/apis/library")
print("  2. Search: YouTube Data API v3")
print("  3. Click ENABLE")
