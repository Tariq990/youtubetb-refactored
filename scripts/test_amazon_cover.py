#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام جلب الأغلفة من Amazon مع الكوكيز
"""
from pathlib import Path
import sys

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.amazon_cover import get_book_cover_from_amazon


def test_amazon_cover_with_cookies():
    """اختبار جلب غلاف كتاب من Amazon باستخدام الكوكيز"""
    
    print("="*70)
    print("  🧪 اختبار جلب أغلفة الكتب من Amazon")
    print("="*70)
    print()
    
    # كتب للاختبار
    test_books = [
        ("Zero to One", "Peter Thiel"),
        ("Atomic Habits", "James Clear"),
        ("The 48 Laws of Power", "Robert Greene"),
        ("Think and Grow Rich", "Napoleon Hill"),
    ]
    
    results = []
    
    for i, (title, author) in enumerate(test_books, 1):
        print(f"\n{'='*70}")
        print(f"  اختبار #{i}: {title} - {author}")
        print(f"{'='*70}\n")
        
        try:
            # محاولة جلب الغلاف
            cover_url = get_book_cover_from_amazon(
                title=title,
                author=author,
                use_playwright=True,
                cookies_path=None  # سيبحث تلقائياً
            )
            
            if cover_url:
                print(f"\n✅ نجح!")
                print(f"URL: {cover_url[:80]}...")
                results.append({
                    'book': f"{title} - {author}",
                    'status': 'نجح',
                    'url': cover_url
                })
            else:
                print(f"\n❌ فشل - لم يتم العثور على غلاف")
                results.append({
                    'book': f"{title} - {author}",
                    'status': 'فشل',
                    'url': None
                })
        
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            results.append({
                'book': f"{title} - {author}",
                'status': 'خطأ',
                'url': None,
                'error': str(e)
            })
    
    # ملخص النتائج
    print(f"\n\n{'='*70}")
    print("  📊 ملخص النتائج")
    print(f"{'='*70}\n")
    
    success_count = sum(1 for r in results if r['status'] == 'نجح')
    fail_count = len(results) - success_count
    
    for i, result in enumerate(results, 1):
        status_emoji = "✅" if result['status'] == 'نجح' else "❌"
        print(f"{status_emoji} {i}. {result['book']}")
        if result.get('url'):
            print(f"   URL: {result['url'][:60]}...")
        if result.get('error'):
            print(f"   Error: {result['error'][:60]}...")
        print()
    
    print(f"📈 الإحصائيات:")
    print(f"  نجح: {success_count}/{len(results)}")
    print(f"  فشل: {fail_count}/{len(results)}")
    print(f"  نسبة النجاح: {(success_count/len(results)*100):.1f}%")
    
    if success_count == len(results):
        print("\n🎉 ممتاز! جميع الاختبارات نجحت!")
    elif success_count > 0:
        print("\n⚠️ بعض الاختبارات نجحت")
    else:
        print("\n❌ جميع الاختبارات فشلت - تحقق من:")
        print("   - ملف cookies.txt موجود في secrets/ أو في الجذر")
        print("   - الكوكيز صالحة وغير منتهية الصلاحية")
        print("   - اتصال الإنترنت يعمل")


if __name__ == '__main__':
    test_amazon_cover_with_cookies()
