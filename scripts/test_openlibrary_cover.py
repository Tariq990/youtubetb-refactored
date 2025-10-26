#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام جلب الأغلفة من Open Library
"""
from pathlib import Path
import sys
import requests
import time
from urllib.parse import quote
from typing import Optional

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def get_cover_from_openlibrary(title: str, author: Optional[str] = None) -> Optional[str]:
    """
    جلب غلاف كتاب من Open Library
    
    Args:
        title: اسم الكتاب
        author: اسم المؤلف (اختياري)
    
    Returns:
        رابط الغلاف إذا وُجد، None إذا فشل
    """
    try:
        query = f"{title} {author}" if author else title
        print(f"[Open Library] البحث عن: {query}")
        
        # Open Library Search API
        url = f"https://openlibrary.org/search.json?q={quote(query)}&limit=10"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'docs' not in data or len(data['docs']) == 0:
            print("[Open Library] ✗ لا توجد نتائج")
            return None
        
        print(f"[Open Library] وُجد {len(data['docs'])} نتيجة، جارٍ التحليل...")
        
        # البحث في أول 10 نتائج
        for idx, doc in enumerate(data['docs'][:10], 1):
            book_title = doc.get('title', 'N/A')
            book_author = ', '.join(doc.get('author_name', [])) if 'author_name' in doc else 'Unknown'
            
            # محاولة جلب الغلاف بطرق متعددة
            cover_url = None
            
            # الطريقة 1: Cover ID (الأفضل - جودة عالية)
            if 'cover_i' in doc:
                cover_id = doc['cover_i']
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                print(f"  كتاب #{idx}: {book_title[:50]}")
                print(f"    المؤلف: {book_author[:40]}")
                print(f"    Cover ID: {cover_id}")
                
                # التحقق من أن الغلاف موجود فعلاً
                verify_response = requests.head(cover_url, timeout=5)
                if verify_response.status_code == 200:
                    print(f"    ✅ غلاف متاح (Cover ID)")
                    return cover_url
                else:
                    print(f"    ⚠️ Cover ID موجود لكن الرابط لا يعمل")
            
            # الطريقة 2: ISBN
            if 'isbn' in doc and len(doc['isbn']) > 0:
                isbn = doc['isbn'][0]
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                print(f"  كتاب #{idx}: {book_title[:50]}")
                print(f"    المؤلف: {book_author[:40]}")
                print(f"    ISBN: {isbn}")
                
                # التحقق من أن الغلاف موجود
                verify_response = requests.head(cover_url, timeout=5)
                if verify_response.status_code == 200:
                    print(f"    ✅ غلاف متاح (ISBN)")
                    return cover_url
                else:
                    print(f"    ⚠️ ISBN موجود لكن لا يوجد غلاف")
            
            # الطريقة 3: OCLC
            if 'oclc' in doc and len(doc['oclc']) > 0:
                oclc = doc['oclc'][0]
                cover_url = f"https://covers.openlibrary.org/b/oclc/{oclc}-L.jpg"
                print(f"  كتاب #{idx}: {book_title[:50]}")
                print(f"    المؤلف: {book_author[:40]}")
                print(f"    OCLC: {oclc}")
                
                verify_response = requests.head(cover_url, timeout=5)
                if verify_response.status_code == 200:
                    print(f"    ✅ غلاف متاح (OCLC)")
                    return cover_url
            
            # إذا لم يكن هناك غلاف، اطبع معلومات الكتاب فقط
            if idx <= 5:  # اطبع تفاصيل أول 5 كتب فقط
                if not ('cover_i' in doc or ('isbn' in doc and len(doc['isbn']) > 0)):
                    print(f"  كتاب #{idx}: {book_title[:50]}")
                    print(f"    المؤلف: {book_author[:40]}")
                    print(f"    ✗ لا يوجد غلاف")
        
        print("[Open Library] ✗ لم يُعثر على غلاف في جميع النتائج")
        return None
        
    except requests.exceptions.Timeout:
        print("[Open Library] ✗ انتهى الوقت المحدد للطلب")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Open Library] ✗ خطأ في الاتصال: {e}")
        return None
    except Exception as e:
        print(f"[Open Library] ✗ خطأ: {e}")
        return None


def test_openlibrary_covers():
    """اختبار جلب أغلفة الكتب من Open Library"""
    
    print("="*70)
    print("  🧪 اختبار جلب أغلفة الكتب من Open Library")
    print("="*70)
    print()
    
    # كتب للاختبار (نفس الكتب من اختبار Amazon)
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
            cover_url = get_cover_from_openlibrary(title=title, author=author)
            
            if cover_url:
                print(f"\n✅ نجح!")
                print(f"URL: {cover_url}")
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
        
        # تأخير بسيط بين الطلبات
        if i < len(test_books):
            time.sleep(1)
    
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
            print(f"   URL: {result['url']}")
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
        print("\n❌ جميع الاختبارات فشلت")
        print("   - تحقق من اتصال الإنترنت")
        print("   - Open Library قد يكون بطيئاً أو معطلاً مؤقتاً")


if __name__ == '__main__':
    test_openlibrary_covers()
