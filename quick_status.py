"""
📊 عرض سريع لحالة جميع أنظمة الـ Fallback
==============================================

استخدم هذا السكريبت للتحقق السريع من حالة جميع الأنظمة.

الإصدار: v2.3.0
"""

from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parent

def quick_status():
    """عرض سريع لحالة جميع الأنظمة"""
    
    print("=" * 60)
    print("📊 حالة أنظمة الـ Fallback - عرض سريع")
    print("=" * 60)
    
    # Check key files
    checks = [
        ("🤖 Gemini API", REPO_ROOT / "secrets" / "api_keys.txt"),
        ("📺 YouTube API", REPO_ROOT / "secrets" / "api_keys.txt"),
        ("🎬 Pexels API", REPO_ROOT / "secrets" / "pexels_key.txt"),
        ("🍪 Cookies (رئيسي)", REPO_ROOT / "secrets" / "cookies.txt"),
        ("🍪 Cookies (احتياطي)", REPO_ROOT / "secrets" / "cookies_1.txt"),
        ("🔐 OAuth Client", REPO_ROOT / "secrets" / "client_secret.json"),
        ("🎫 OAuth Token", REPO_ROOT / "secrets" / "token.json"),
        ("⚙️ Config (.env)", REPO_ROOT / "secrets" / ".env"),
    ]
    
    all_good = True
    for name, path in checks:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {name:25s} ({size:,} bytes)")
        else:
            print(f"  ❌ {name:25s} (غير موجود)")
            all_good = False
    
    print("\n" + "=" * 60)
    
    # Environment variables
    env_vars = {
        "YT_API_KEY": "YouTube API",
        "GEMINI_API_KEY": "Gemini API",
        "PEXELS_API_KEY": "Pexels API",
    }
    
    print("🌍 متغيرات البيئة:")
    for var, desc in env_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var:20s} = {masked}")
        else:
            print(f"  ⚠️  {var:20s} (غير محدد)")
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 جميع الملفات الأساسية موجودة!")
    else:
        print("⚠️  بعض الملفات غير موجودة (اختياري)")
    
    print("\n💡 للاختبار الشامل:")
    print("   python test_all_fallback_systems.py")
    print("\n📚 للتوثيق الكامل:")
    print("   راجع: STORAGE_LOCATIONS.md")
    print("=" * 60)

if __name__ == "__main__":
    quick_status()
