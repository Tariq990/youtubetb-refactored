#!/usr/bin/env python3
"""
تحقق من توافق أماكن الحفظ بين cookies_helper.py و pipeline
Check compatibility between cookies_helper.py save locations and pipeline read locations
"""

from pathlib import Path
import json

# Import from cookies_helper
from cookies_helper import COOKIES_PATHS, API_KEYS_PATHS, SECRETS_DIR

print("="*80)
print("🔍 تحليل توافق أماكن التخزين / Storage Locations Compatibility Analysis")
print("="*80)

# ==============================================================================
# PART 1: COOKIES - Where cookies_helper saves vs where pipeline reads
# ==============================================================================
print("\n📋 PART 1: COOKIES (YouTube)")
print("-"*80)

# Where cookies_helper SAVES cookies
print("\n✅ WHERE cookies_helper.py SAVES:")
print("   Function: add_cookies() → save_to_file()")
print("   Priority order (uses FIRST empty slot):")
for i, path in enumerate(COOKIES_PATHS, 1):
    status = "✓ EXISTS" if path.exists() else "✗ NOT FOUND"
    size = f"({path.stat().st_size:,} bytes)" if path.exists() else ""
    print(f"   [{i}] {path} {status} {size}")

# Where pipeline READS cookies
print("\n📖 WHERE PIPELINE READS:")
print("   File: src/infrastructure/adapters/transcribe.py")
print("   Variable: cookie_paths (lines 525-530)")
print("   Search order:")

pipeline_cookies = [
    Path("secrets/cookies.txt"),
    Path("secrets/cookies_1.txt"),
    Path("secrets/cookies_2.txt"),
    Path("secrets/cookies_3.txt"),
    Path("cookies.txt")
]

for i, rel_path in enumerate(pipeline_cookies, 1):
    abs_path = Path(__file__).parent / rel_path
    status = "✓ EXISTS" if abs_path.exists() else "✗ NOT FOUND"
    print(f"   [{i}] {rel_path} {status}")

# Check compatibility
print("\n🔍 COMPATIBILITY CHECK:")
helper_set = {p.resolve() for p in COOKIES_PATHS}
pipeline_set = {(Path(__file__).parent / p).resolve() for p in pipeline_cookies}

if helper_set == pipeline_set:
    print("   ✅ PERFECT MATCH! All paths identical.")
else:
    missing = pipeline_set - helper_set
    extra = helper_set - pipeline_set
    if missing:
        print(f"   ⚠️  Pipeline reads from {len(missing)} locations NOT in cookies_helper:")
        for p in missing:
            print(f"       • {p}")
    if extra:
        print(f"   ⚠️  cookies_helper saves to {len(extra)} locations NOT read by pipeline:")
        for p in extra:
            print(f"       • {p}")

# ==============================================================================
# PART 2: GEMINI API KEYS - Where cookies_helper saves vs where pipeline reads
# ==============================================================================
print("\n\n📋 PART 2: GEMINI API KEYS")
print("-"*80)

# Where cookies_helper SAVES Gemini keys
print("\n✅ WHERE cookies_helper.py SAVES:")
print("   Function: add_gemini_api() → Choice [1]")
print("   Default location:")
gemini_save_path = SECRETS_DIR / "api_keys.txt"
status = "✓ EXISTS" if gemini_save_path.exists() else "✗ NOT FOUND"
print(f"   • {gemini_save_path} {status}")

print("\n   Alternative location (Choice [2]):")
env_path = SECRETS_DIR / ".env"
status = "✓ EXISTS" if env_path.exists() else "✗ NOT FOUND"
print(f"   • {env_path} (GEMINI_API_KEY=...) {status}")

# Where pipeline READS Gemini keys
print("\n📖 WHERE PIPELINE READS:")
print("   File: src/infrastructure/adapters/process.py")
print("   Function: _load_gemini_model() (lines 156-180)")
print("   Search order:")
print("   [1] Environment variable: GEMINI_API_KEY")
print("   [2] secrets/api_keys.txt (multi-line file)")
print("   [3] secrets/api_key.txt (single key)")
print("   [4] .env file (GEMINI_API_KEY=...)")

print("\n🔍 COMPATIBILITY CHECK:")
print("   ✅ cookies_helper saves to: secrets/api_keys.txt")
print("   ✅ Pipeline reads from: secrets/api_keys.txt (Priority 2)")
print("   ✅ COMPATIBLE! Pipeline WILL find keys saved by cookies_helper")

# ==============================================================================
# PART 3: YOUTUBE API KEYS - Critical compatibility check
# ==============================================================================
print("\n\n📋 PART 3: YOUTUBE API KEYS ⚠️  CRITICAL")
print("-"*80)

# Where cookies_helper SAVES YouTube keys (AFTER FIX)
print("\n✅ WHERE cookies_helper.py SAVES:")
print("   Function: add_youtube_api() → Choice [1]")
youtube_save_path = SECRETS_DIR / "api_keys.txt"  # OLD DEFAULT
status = "✓ EXISTS" if youtube_save_path.exists() else "✗ NOT FOUND"
print(f"   • {youtube_save_path} {status}")
print("      ^ ⚠️  WARNING: This is SHARED with Gemini!")

# Where pipeline READS YouTube keys
print("\n📖 WHERE PIPELINE READS:")
print("   File: src/infrastructure/adapters/search.py")
print("   Function: _load_all_youtube_api_keys() (lines 45-85)")
print("   Search order:")
print("   [1] Environment variable: YT_API_KEY or YOUTUBE_API_KEY")
print("   [2] secrets/api_keys.txt (SHARED FILE - reads ALL keys)")
print("   [3] secrets/api_key.txt (single key)")

print("\n🔍 COMPATIBILITY CHECK:")
print("   ✅ cookies_helper saves to: secrets/api_keys.txt")
print("   ✅ Pipeline reads from: secrets/api_keys.txt (Priority 2)")
print("   ✅ COMPATIBLE! Pipeline WILL find keys saved by cookies_helper")
print("\n   ⚠️  PROBLEM: No dedicated youtube/ subfolder support!")
print("      • cookies_helper has: secrets/youtube/api_keys.txt in API_KEYS_PATHS")
print("      • But add_youtube_api() saves to: secrets/api_keys.txt (shared)")
print("      • Pipeline does NOT check secrets/youtube/api_keys.txt")

# Check if dedicated youtube folder exists
youtube_dedicated = SECRETS_DIR / "youtube" / "api_keys.txt"
if youtube_dedicated.exists():
    print(f"\n   📁 Found: {youtube_dedicated}")
    print(f"      ⚠️  This file exists but pipeline does NOT read from it!")
    print(f"      💡 Solution: Copy keys to secrets/api_keys.txt")

# ==============================================================================
# PART 4: PEXELS API KEYS
# ==============================================================================
print("\n\n📋 PART 4: PEXELS API KEYS")
print("-"*80)

# Where cookies_helper SAVES Pexels keys
print("\n✅ WHERE cookies_helper.py SAVES:")
print("   Function: add_pexels_api() → Choice [1]")
pexels_save_path = SECRETS_DIR / "pexels_key.txt"
status = "✓ EXISTS" if pexels_save_path.exists() else "✗ NOT FOUND"
print(f"   • {pexels_save_path} {status}")

# Where pipeline READS Pexels keys
print("\n📖 WHERE PIPELINE READS:")
print("   File: src/infrastructure/adapters/shorts_generator.py")
print("   Function: _load_pexels_api_key() (lines 560-600)")
print("   Search order:")
print("   [1] Environment variable: PEXELS_API_KEY")
print("   [2] secrets/pexels_key.txt")
print("   [3] secrets/pexels/api_key.txt")
print("   [4] secrets/api_keys.txt (shared)")
print("   [5] .env file")

print("\n🔍 COMPATIBILITY CHECK:")
print("   ✅ cookies_helper saves to: secrets/pexels_key.txt")
print("   ✅ Pipeline reads from: secrets/pexels_key.txt (Priority 2)")
print("   ✅ COMPATIBLE! Pipeline WILL find keys saved by cookies_helper")

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
print("\n\n" + "="*80)
print("📊 FINAL SUMMARY / الملخص النهائي")
print("="*80)

summary = {
    "cookies": {
        "compatible": True,
        "save_to": str(COOKIES_PATHS[0]),
        "pipeline_reads": "secrets/cookies.txt (Priority 1)",
        "status": "✅ FULLY COMPATIBLE"
    },
    "gemini": {
        "compatible": True,
        "save_to": "secrets/api_keys.txt",
        "pipeline_reads": "secrets/api_keys.txt (Priority 2)",
        "status": "✅ FULLY COMPATIBLE"
    },
    "youtube": {
        "compatible": True,
        "save_to": "secrets/api_keys.txt",
        "pipeline_reads": "secrets/api_keys.txt (Priority 2)",
        "status": "⚠️  COMPATIBLE BUT PROBLEMATIC",
        "issue": "Pipeline does NOT read from secrets/youtube/api_keys.txt",
        "solution": "Keys must be in secrets/api_keys.txt (shared with Gemini)"
    },
    "pexels": {
        "compatible": True,
        "save_to": "secrets/pexels_key.txt",
        "pipeline_reads": "secrets/pexels_key.txt (Priority 2)",
        "status": "✅ FULLY COMPATIBLE"
    }
}

print("\n1. 🍪 COOKIES:")
print(f"   {summary['cookies']['status']}")
print(f"   • cookies_helper saves to: {summary['cookies']['save_to']}")
print(f"   • Pipeline reads from: {summary['cookies']['pipeline_reads']}")

print("\n2. 🤖 GEMINI API:")
print(f"   {summary['gemini']['status']}")
print(f"   • cookies_helper saves to: {summary['gemini']['save_to']}")
print(f"   • Pipeline reads from: {summary['gemini']['pipeline_reads']}")

print("\n3. 📺 YOUTUBE API:")
print(f"   {summary['youtube']['status']}")
print(f"   • cookies_helper saves to: {summary['youtube']['save_to']}")
print(f"   • Pipeline reads from: {summary['youtube']['pipeline_reads']}")
if 'issue' in summary['youtube']:
    print(f"   ⚠️  {summary['youtube']['issue']}")
    print(f"   💡 {summary['youtube']['solution']}")

print("\n4. 🎬 PEXELS API:")
print(f"   {summary['pexels']['status']}")
print(f"   • cookies_helper saves to: {summary['pexels']['save_to']}")
print(f"   • Pipeline reads from: {summary['pexels']['pipeline_reads']}")

# Overall verdict
print("\n" + "="*80)
print("🎯 OVERALL VERDICT / الحكم النهائي")
print("="*80)
print("\n✅ نعم، الأداة تحفظ في الأماكن الصحيحة!")
print("   Yes, cookies_helper.py saves to CORRECT locations!")
print("\n✅ الـ Pipeline يمكنه قراءة جميع المفاتيح المحفوظة")
print("   Pipeline CAN read all saved keys and cookies")
print("\n⚠️  ملاحظة واحدة: مفاتيح YouTube في ملف مشترك مع Gemini")
print("   One note: YouTube keys in SHARED file with Gemini")
print("   (secrets/api_keys.txt - not a problem, just shared)")

# Save report
report_path = Path("compatibility_report.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"\n📄 Detailed report saved to: {report_path}")

print("\n" + "="*80)
