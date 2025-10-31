#!/usr/bin/env python3
"""Test YouTube API keys loading from dedicated folder"""

import sys
import os
from pathlib import Path

# Add adapters to path
sys.path.insert(0, 'src/infrastructure/adapters')

print("="*80)
print("🧪 TEST: Verify YouTube API Keys Loading")
print("="*80)
print()

# Import function
from search import _load_all_youtube_api_keys

# Load keys
keys = _load_all_youtube_api_keys()

print(f"✅ Loaded {len(keys)} YouTube API key(s)")
print()

# Check which files exist
print("📂 Files checked:")
base = Path(".").resolve()
yt_file = base / "secrets" / "youtube" / "api_keys.txt"
shared_file = base / "secrets" / "api_keys.txt"

if yt_file.exists():
    count = len([l for l in yt_file.read_text().splitlines() if l.strip() and not l.startswith('#')])
    print(f"  ✓ secrets/youtube/api_keys.txt (DEDICATED) - {count} keys")
else:
    print(f"  ✗ secrets/youtube/api_keys.txt - NOT FOUND")

if shared_file.exists():
    count = len([l for l in shared_file.read_text().splitlines() if l.strip() and not l.startswith('#')])
    print(f"  ✓ secrets/api_keys.txt (SHARED - fallback) - {count} keys")
else:
    print(f"  ✗ secrets/api_keys.txt - NOT FOUND")

print()
print("🔑 Keys loaded (preview):")
for i, k in enumerate(keys[:5], 1):
    print(f"  [{i}] {k[:15]}... ({len(k)} chars)")

if len(keys) > 5:
    print(f"  ... and {len(keys)-5} more")

print()
if keys:
    print("✅ SUCCESS! Pipeline CAN now read YouTube keys from dedicated folder!")
else:
    print("❌ FAILED! No keys loaded")

print("="*80)
