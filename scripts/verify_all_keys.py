#!/usr/bin/env python3
"""
🔍 API Keys & Cookies Verification Tool
========================================

يفحص جميع مفاتيح API والكوكيز ويختبرها فعلياً
Checks all API keys and cookies and tests them actually

Author: YouTubeTB Project
Date: 2025-10-31
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("🔍 فحص شامل لجميع API Keys والكوكيز")
print("🔍 Comprehensive API Keys & Cookies Verification")
print("=" * 80)
print(f"📅 التاريخ | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ============================================================================
# PATHS
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent  # Go up from scripts/ to repo root
SECRETS_DIR = REPO_ROOT / "secrets"

print(f"\n📂 مجلد الأسرار | Secrets Directory:")
print(f"   {SECRETS_DIR}")
print(f"   {'✅ موجود' if SECRETS_DIR.exists() else '❌ غير موجود'}")

# ============================================================================
# 1. GEMINI API KEYS
# ============================================================================

print(f"\n{'=' * 80}")
print("1️⃣  فحص مفاتيح Gemini API")
print("=" * 80)

gemini_locations = [
    SECRETS_DIR / "api_key.txt",
    SECRETS_DIR / "api_keys.txt",
    SECRETS_DIR / "gemini" / "api_key.txt",
    SECRETS_DIR / "gemini" / "api_keys.txt",
    SECRETS_DIR / ".env"
]

gemini_keys_found = []

for loc in gemini_locations:
    if loc.exists():
        print(f"\n📄 {loc.relative_to(REPO_ROOT)}")
        try:
            content = loc.read_text(encoding='utf-8').strip()
            
            # Parse keys
            keys = []
            for line in content.split('\n'):
                line = line.strip()
                # Skip comments and empty
                if not line or line.startswith('#'):
                    continue
                # Check if it's .env format
                if '=' in line and loc.name == '.env':
                    key = line.split('=', 1)[1].strip().strip('"\'')
                    if key.startswith('AIzaSy'):
                        keys.append(key)
                elif line.startswith('AIzaSy'):
                    keys.append(line.split()[0])  # Get first word (key only)
            
            if keys:
                print(f"   ✅ عدد المفاتيح | Keys: {len(keys)}")
                for i, key in enumerate(keys, 1):
                    masked = f"{key[:10]}...{key[-4:]}" if len(key) > 15 else key
                    print(f"      {i}. {masked} ({len(key)} حرف)")
                    gemini_keys_found.append((key, str(loc.relative_to(REPO_ROOT))))
            else:
                print(f"   ⚠️  الملف فارغ أو لا يحتوي مفاتيح صالحة")
        except Exception as e:
            print(f"   ❌ خطأ في القراءة: {e}")
    else:
        print(f"❌ {loc.relative_to(REPO_ROOT)} - غير موجود")

print(f"\n📊 الإجمالي | Total Gemini Keys: {len(gemini_keys_found)}")

# ============================================================================
# 2. TEST GEMINI KEYS
# ============================================================================

if gemini_keys_found:
    print(f"\n{'=' * 80}")
    print("🧪 اختبار مفاتيح Gemini API (فعلياً)")
    print("=" * 80)
    
    try:
        import google.generativeai as genai
        
        working_keys = []
        quota_exceeded_keys = []
        failed_keys = []
        
        for i, (key, source) in enumerate(gemini_keys_found, 1):
            print(f"\n🔑 المفتاح {i}/{len(gemini_keys_found)} من {source}")
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                # Test with simple prompt
                print(f"   ⏳ جاري الاختبار...")
                response = model.generate_content("Say 'OK' only")
                
                if response and response.text:
                    print(f"   ✅ يعمل بنجاح! | Working!")
                    print(f"      الرد: {response.text.strip()}")
                    working_keys.append((key, source))
                else:
                    print(f"   ⚠️  رد فارغ | Empty response")
                    failed_keys.append((key, source, "Empty response"))
                    
            except Exception as e:
                error_msg = str(e)
                if "quota" in error_msg.lower() or "429" in error_msg:
                    print(f"   ⚠️  Quota exceeded (المفتاح استنفذ)")
                    quota_exceeded_keys.append((key, source))
                elif "invalid" in error_msg.lower() or "401" in error_msg:
                    print(f"   ❌ مفتاح غير صالح | Invalid key")
                    failed_keys.append((key, source, "Invalid"))
                else:
                    print(f"   ❌ خطأ: {error_msg[:60]}")
                    failed_keys.append((key, source, error_msg[:60]))
        
        # Summary
        print(f"\n{'=' * 80}")
        print("📊 ملخص اختبار Gemini")
        print("=" * 80)
        print(f"✅ مفاتيح تعمل | Working: {len(working_keys)}")
        print(f"⚠️  Quota exceeded: {len(quota_exceeded_keys)}")
        print(f"❌ فاشلة | Failed: {len(failed_keys)}")
        
        if working_keys:
            print(f"\n✅ المفاتيح العاملة:")
            for key, source in working_keys:
                print(f"   • {key[:10]}... من {source}")
        
    except ImportError:
        print("⚠️  google-generativeai غير مثبت | Not installed")
        print("   pip install google-generativeai")

# ============================================================================
# 3. YOUTUBE DATA API KEYS
# ============================================================================

print(f"\n{'=' * 80}")
print("2️⃣  فحص مفاتيح YouTube Data API")
print("=" * 80)

youtube_locations = [
    SECRETS_DIR / "youtube" / "api_keys.txt",
    SECRETS_DIR / "api_keys.txt",
    SECRETS_DIR / ".env"
]

youtube_keys_found = []

for loc in youtube_locations:
    if loc.exists():
        print(f"\n📄 {loc.relative_to(REPO_ROOT)}")
        try:
            content = loc.read_text(encoding='utf-8').strip()
            
            # Parse keys
            keys = []
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line and loc.name == '.env':
                    if 'YOUTUBE' in line:
                        key = line.split('=', 1)[1].strip().strip('"\'')
                        if key.startswith('AIzaSy'):
                            keys.append(key)
                elif line.startswith('AIzaSy'):
                    keys.append(line.split()[0])
            
            if keys:
                print(f"   ✅ عدد المفاتيح | Keys: {len(keys)}")
                for i, key in enumerate(keys, 1):
                    masked = f"{key[:10]}...{key[-4:]}"
                    print(f"      {i}. {masked}")
                    youtube_keys_found.append((key, str(loc.relative_to(REPO_ROOT))))
            else:
                print(f"   ⚠️  فارغ | Empty")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")

print(f"\n📊 الإجمالي | Total YouTube Keys: {len(youtube_keys_found)}")

# ============================================================================
# 4. TEST YOUTUBE KEYS
# ============================================================================

if youtube_keys_found:
    print(f"\n{'=' * 80}")
    print("🧪 اختبار مفاتيح YouTube Data API")
    print("=" * 80)
    
    try:
        import requests
        
        working_yt = []
        quota_yt = []
        failed_yt = []
        
        for i, (key, source) in enumerate(youtube_keys_found, 1):
            print(f"\n🔑 المفتاح {i}/{len(youtube_keys_found)} من {source}")
            try:
                url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key={key}"
                print(f"   ⏳ جاري الاختبار...")
                
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'items' in data:
                        print(f"   ✅ يعمل بنجاح! | Working!")
                        working_yt.append((key, source))
                    else:
                        print(f"   ⚠️  رد غير متوقع")
                        failed_yt.append((key, source, "Unexpected response"))
                elif response.status_code == 403:
                    error = response.json().get('error', {})
                    reason = error.get('errors', [{}])[0].get('reason', '')
                    if 'quota' in reason.lower():
                        print(f"   ⚠️  Quota exceeded")
                        quota_yt.append((key, source))
                    else:
                        print(f"   ❌ 403 Forbidden: {reason}")
                        failed_yt.append((key, source, f"403: {reason}"))
                elif response.status_code == 400:
                    print(f"   ❌ 400 Bad Request (مفتاح غير صالح)")
                    failed_yt.append((key, source, "400 Invalid"))
                else:
                    print(f"   ❌ Status {response.status_code}")
                    failed_yt.append((key, source, f"Status {response.status_code}"))
                    
            except Exception as e:
                print(f"   ❌ خطأ: {str(e)[:60]}")
                failed_yt.append((key, source, str(e)[:60]))
        
        # Summary
        print(f"\n{'=' * 80}")
        print("📊 ملخص اختبار YouTube")
        print("=" * 80)
        print(f"✅ مفاتيح تعمل | Working: {len(working_yt)}")
        print(f"⚠️  Quota exceeded: {len(quota_yt)}")
        print(f"❌ فاشلة | Failed: {len(failed_yt)}")
        
    except ImportError:
        print("⚠️  requests غير مثبت | Not installed")
        print("   pip install requests")

# ============================================================================
# 5. COOKIES FILES
# ============================================================================

print(f"\n{'=' * 80}")
print("3️⃣  فحص ملفات الكوكيز")
print("=" * 80)

cookie_files = [
    SECRETS_DIR / "cookies.txt",
    SECRETS_DIR / "cookies_1.txt",
    SECRETS_DIR / "cookies_2.txt",
    SECRETS_DIR / "cookies_3.txt",
    REPO_ROOT / "cookies.txt"
]

cookies_found = []

for cf in cookie_files:
    if cf.exists():
        size = cf.stat().st_size
        print(f"\n📄 {cf.relative_to(REPO_ROOT)}")
        print(f"   📊 الحجم | Size: {size:,} bytes")
        
        if size > 50:
            # Read and check format
            try:
                content = cf.read_text(encoding='utf-8', errors='ignore')
                
                if '# Netscape HTTP Cookie File' in content:
                    print(f"   ✅ تنسيق Netscape صحيح")
                    cookie_count = len([l for l in content.split('\n') if l and not l.startswith('#')])
                    print(f"   🍪 عدد الكوكيز | Cookies: ~{cookie_count}")
                    cookies_found.append((cf, size, cookie_count))
                elif '<html' in content.lower():
                    print(f"   ❌ تنسيق HTML (غير صالح!)")
                elif content.startswith('[') or content.startswith('{'):
                    print(f"   ⚠️  تنسيق JSON (يحتاج تحويل)")
                else:
                    print(f"   ⚠️  تنسيق غير معروف")
            except Exception as e:
                print(f"   ❌ خطأ في القراءة: {e}")
        else:
            print(f"   ❌ الملف صغير جداً (< 50 bytes) - على الأرجح فارغ")
    else:
        print(f"❌ {cf.relative_to(REPO_ROOT)} - غير موجود")

print(f"\n📊 الإجمالي | Total Valid Cookies: {len(cookies_found)}")

# ============================================================================
# 6. PEXELS API KEY
# ============================================================================

print(f"\n{'=' * 80}")
print("4️⃣  فحص مفتاح Pexels API")
print("=" * 80)

pexels_locations = [
    SECRETS_DIR / "pexels_key.txt",
    SECRETS_DIR / "pexels" / "api_key.txt",
    SECRETS_DIR / ".env"
]

pexels_key = None

for loc in pexels_locations:
    if loc.exists():
        print(f"\n📄 {loc.relative_to(REPO_ROOT)}")
        try:
            content = loc.read_text(encoding='utf-8').strip()
            
            # Parse key
            if '=' in content and loc.name == '.env':
                for line in content.split('\n'):
                    if 'PEXELS' in line:
                        pexels_key = line.split('=', 1)[1].strip().strip('"\'')
                        break
            else:
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                if lines:
                    pexels_key = lines[0]
            
            if pexels_key:
                print(f"   ✅ مفتاح موجود | Key found")
                print(f"      {pexels_key[:10]}... ({len(pexels_key)} حرف)")
                break
        except Exception as e:
            print(f"   ❌ خطأ: {e}")

if not pexels_key:
    print("❌ لم يتم العثور على مفتاح Pexels")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print(f"\n{'=' * 80}")
print("📊 الملخص النهائي | FINAL SUMMARY")
print("=" * 80)

print(f"\n1. Gemini API:")
print(f"   • المفاتيح الموجودة: {len(gemini_keys_found)}")

print(f"\n2. YouTube Data API:")
print(f"   • المفاتيح الموجودة: {len(youtube_keys_found)}")

print(f"\n3. Cookies:")
print(f"   • الملفات الصالحة: {len(cookies_found)}")

print(f"\n4. Pexels API:")
print(f"   • {'✅ موجود' if pexels_key else '❌ غير موجود'}")

print(f"\n{'=' * 80}")
print("✅ انتهى الفحص | Verification Complete")
print("=" * 80)
