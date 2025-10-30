"""
🧪 اختبار شامل لجميع أنظمة الـ Fallback
==========================================

يختبر:
1. Gemini API (5 مواقع)
2. YouTube API (5 مواقع)
3. Cookies (5 مواقع)
4. Pexels API (6 مواقع)

الإصدار: v2.3.0
التاريخ: 2025-10-30
"""

import os
from pathlib import Path
import sys

# Setup path
REPO_ROOT = Path(__file__).resolve().parent

def print_header(title, emoji="🔍"):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"{emoji} {title}")
    print("=" * 60)

def print_result(priority, location, status, details=""):
    """Print formatted result"""
    icon = "✅" if status == "FOUND" else "❌"
    print(f"  {priority}. [{icon}] {location}")
    if details:
        print(f"      {details}")

def check_file_exists(path):
    """Check if file exists and get size"""
    if path.exists():
        size = path.stat().st_size
        return True, f"({size} bytes)"
    return False, ""

def check_env_var(var_name):
    """Check if environment variable exists"""
    value = os.getenv(var_name)
    if value:
        masked = value[:10] + "..." if len(value) > 10 else value
        return True, f"(set: {masked})"
    return False, ""

def test_gemini_api():
    """Test Gemini API fallback system"""
    print_header("Gemini API Fallback (5 مواقع)", "🤖")
    
    locations = [
        ("1", REPO_ROOT / "secrets" / "api_keys.txt", "نص عادي (متعدد)"),
        ("2", REPO_ROOT / "secrets" / "api_key.txt", "نص عادي (واحد)"),
        ("3", REPO_ROOT / "api_key.txt", "نص عادي (جذر)"),
        ("4", None, "GEMINI_API_KEY متغير بيئة"),
        ("5", REPO_ROOT / "secrets" / ".env", "GEMINI_API_KEY=..."),
    ]
    
    found_count = 0
    for priority, location, desc in locations:
        if location is None:  # Environment variable
            exists, details = check_env_var("GEMINI_API_KEY")
        else:
            exists, details = check_file_exists(location)
        
        status = "FOUND" if exists else "NOT FOUND"
        print_result(priority, desc, status, details)
        if exists:
            found_count += 1
    
    print(f"\n📊 النتيجة: {found_count} موقع متاح من أصل 5")
    return found_count

def test_youtube_api():
    """Test YouTube API fallback system"""
    print_header("YouTube Data API Fallback (5 مواقع)", "📺")
    
    locations = [
        ("1", None, "YT_API_KEY متغير بيئة"),
        ("2", REPO_ROOT / "secrets" / "api_keys.txt", "نص عادي (متعدد)"),
        ("3", REPO_ROOT / "secrets" / "api_key.txt", "نص عادي (واحد)"),
        ("4", REPO_ROOT / "api_key.txt", "نص عادي (جذر)"),
        ("5", REPO_ROOT / "secrets" / ".env", "YT_API_KEY=..."),
    ]
    
    found_count = 0
    for priority, location, desc in locations:
        if location is None:  # Environment variable
            exists, details = check_env_var("YT_API_KEY")
        else:
            exists, details = check_file_exists(location)
        
        status = "FOUND" if exists else "NOT FOUND"
        print_result(priority, desc, status, details)
        if exists:
            found_count += 1
    
    print(f"\n📊 النتيجة: {found_count} موقع متاح من أصل 5")
    return found_count

def test_cookies():
    """Test Cookies fallback system"""
    print_header("Cookies Fallback (5 مواقع)", "🍪")
    
    locations = [
        ("1", REPO_ROOT / "secrets" / "cookies.txt", "Netscape format (رئيسي)"),
        ("2", REPO_ROOT / "secrets" / "cookies_1.txt", "Netscape format (احتياطي 1)"),
        ("3", REPO_ROOT / "secrets" / "cookies_2.txt", "Netscape format (احتياطي 2)"),
        ("4", REPO_ROOT / "secrets" / "cookies_3.txt", "Netscape format (احتياطي 3)"),
        ("5", REPO_ROOT / "cookies.txt", "Netscape format (جذر)"),
    ]
    
    found_count = 0
    valid_count = 0
    for priority, location, desc in locations:
        exists, details = check_file_exists(location)
        
        # Additional validation for cookies
        if exists and location.exists():
            size = location.stat().st_size
            if size > 50:  # Valid size check
                valid_count += 1
                details += " ✓ Valid"
            else:
                details += " ⚠️  Too small"
        
        status = "FOUND" if exists else "NOT FOUND"
        print_result(priority, desc, status, details)
        if exists:
            found_count += 1
    
    print(f"\n📊 النتيجة: {found_count} موقع متاح ({valid_count} صالح) من أصل 5")
    return valid_count

def test_pexels_api():
    """Test Pexels API fallback system"""
    print_header("Pexels API Fallback (6 مواقع)", "🎬")
    
    locations = [
        ("1", None, "PEXELS_API_KEY متغير بيئة"),
        ("2", REPO_ROOT / "secrets" / ".env", "PEXELS_API_KEY=..."),
        ("3", REPO_ROOT / "secrets" / "pexels_key.txt", "نص عادي (موصى به)"),
        ("4", REPO_ROOT / "secrets" / "api_keys.txt", "نص عادي (مشترك)"),
        ("5", REPO_ROOT / "secrets" / "api_key.txt", "نص عادي (قديم)"),
        ("6", REPO_ROOT / ".env", "PEXELS_API_KEY=... (جذر)"),
    ]
    
    found_count = 0
    for priority, location, desc in locations:
        if location is None:  # Environment variable
            exists, details = check_env_var("PEXELS_API_KEY")
        else:
            exists, details = check_file_exists(location)
        
        status = "FOUND" if exists else "NOT FOUND"
        print_result(priority, desc, status, details)
        if exists:
            found_count += 1
    
    print(f"\n📊 النتيجة: {found_count} موقع متاح من أصل 6")
    return found_count

def show_secrets_structure():
    """Show actual secrets/ folder structure"""
    print_header("هيكل المجلد secrets/ الفعلي", "📂")
    
    secrets_dir = REPO_ROOT / "secrets"
    if not secrets_dir.exists():
        print("❌ المجلد secrets/ غير موجود!")
        return
    
    print(f"\n{secrets_dir}/")
    
    # List all files
    files_found = []
    for item in sorted(secrets_dir.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            files_found.append((item.name, size))
            print(f"  ├── {item.name:30s} ({size:,} bytes)")
    
    # List subdirectories
    dirs = [d for d in secrets_dir.iterdir() if d.is_dir()]
    if dirs:
        print("\n  Subdirectories:")
        for d in sorted(dirs):
            print(f"  └── {d.name}/")
    
    print(f"\n📊 المجموع: {len(files_found)} ملف")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 اختبار شامل لجميع أنظمة الـ Fallback")
    print("=" * 60)
    print(f"📁 المشروع: {REPO_ROOT}")
    print(f"🗓️  التاريخ: 2025-10-30")
    print(f"📌 الإصدار: v2.3.0")
    
    # Run all tests
    gemini_count = test_gemini_api()
    youtube_count = test_youtube_api()
    cookies_count = test_cookies()
    pexels_count = test_pexels_api()
    
    # Show structure
    show_secrets_structure()
    
    # Final summary
    print_header("ملخص النتائج النهائي", "📊")
    
    results = [
        ("Gemini API", gemini_count, 5),
        ("YouTube API", youtube_count, 5),
        ("Cookies", cookies_count, 5),
        ("Pexels API", pexels_count, 6),
    ]
    
    all_passed = True
    for name, found, total in results:
        percentage = (found / total) * 100
        status = "✅" if found > 0 else "⚠️"
        print(f"  {status} {name:15s}: {found}/{total} ({percentage:.0f}%)")
        if found == 0:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 جميع الأنظمة تعمل بشكل صحيح!")
        print("✅ نظام الـ Fallback جاهز للاستخدام")
    else:
        print("⚠️  بعض الأنظمة تحتاج إلى إعداد")
        print("💡 راجع التوثيق: STORAGE_LOCATIONS.md")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
