#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام جلب الأغلفة من Google Books
"""
from pathlib import Path
import sys
import requests
import time
from urllib.parse import quote
from typing import Optional
import os

# Add repo root to path for imports
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# مجلد لحفظ الأغلفة المحملة
COVERS_DIR = repo_root / "tmp" / "test_covers_googlebooks"
COVERS_DIR.mkdir(parents=True, exist_ok=True)


def get_cover_from_googlebooks(
    title: str, 
    author: Optional[str] = None,
    language: str = "en",  # en, ar, etc.
    order_by: str = "relevance"  # relevance or newest
) -> Optional[str]:
    """
    جلب غلاف كتاب من Google Books API مع فلاتر متقدمة
    
    Args:
        title: اسم الكتاب
        author: اسم المؤلف (اختياري)
        language: اللغة (en=إنجليزي, ar=عربي, etc.)
        order_by: الترتيب (relevance=الأكثر صلة, newest=الأحدث)
    
    Returns:
        رابط الغلاف إذا وُجد، None إذا فشل
    """
    try:
        # بناء الاستعلام المتقدم
        if author:
            query = f'intitle:"{title}" inauthor:"{author}"'
        else:
            query = f'intitle:"{title}"'
        
        print(f"[Google Books] البحث عن: {title} - {author or 'N/A'}")
        print(f"[Google Books] اللغة: {language} | الترتيب: {order_by}")
        
        # Google Books API endpoint with filters
        url = f"https://www.googleapis.com/books/v1/volumes?q={quote(query)}&langRestrict={language}&orderBy={order_by}&maxResults=10&printType=books"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' not in data or len(data['items']) == 0:
            print("[Google Books] ✗ لا توجد نتائج")
            return None
        
        print(f"[Google Books] وُجد {len(data['items'])} نتيجة، جارٍ التحليل...")
        
        # البحث في جميع النتائج مع فلترة اللغة
        valid_results = []
        for idx, item in enumerate(data['items'], 1):
            volume_info = item.get('volumeInfo', {})
            book_title = volume_info.get('title', 'N/A')
            book_authors = ', '.join(volume_info.get('authors', ['Unknown']))
            published_date = volume_info.get('publishedDate', 'N/A')
            publisher = volume_info.get('publisher', 'N/A')
            book_language = volume_info.get('language', 'N/A')
            
            # فلترة اللغة: تجاهل النتائج غير المطلوبة
            if language and book_language != language:
                print(f"  [تجاهل] كتاب #{idx}: {book_title[:50]} (اللغة: {book_language} ≠ {language})")
                continue
            
            # معلومات التقييم (إذا متوفرة)
            average_rating = volume_info.get('averageRating', 0)
            ratings_count = volume_info.get('ratingsCount', 0)
            
            valid_results.append({
                'idx': len(valid_results) + 1,
                'volume_info': volume_info,
                'book_title': book_title,
                'book_authors': book_authors,
                'published_date': published_date,
                'publisher': publisher,
                'book_language': book_language,
                'average_rating': average_rating,
                'ratings_count': ratings_count
            })
        
        if not valid_results:
            print(f"[Google Books] ✗ لا توجد نتائج باللغة {language}")
            return None
        
        print(f"[Google Books] ✓ وُجد {len(valid_results)} نتيجة صالحة باللغة {language}")
        
        # معالجة النتائج الصالحة
        for result in valid_results:
            idx = result['idx']
            volume_info = result['volume_info']
            book_title = result['book_title']
            book_authors = result['book_authors']
            published_date = result['published_date']
            publisher = result['publisher']
            book_language = result['book_language']
            average_rating = result['average_rating']
            ratings_count = result['ratings_count']
            
            image_links = volume_info.get('imageLinks', {})
            
            # طباعة معلومات الكتاب
            print(f"  كتاب #{idx}: {book_title[:60]}")
            print(f"    المؤلف: {book_authors[:50]}")
            print(f"    الناشر: {publisher[:40]}")
            print(f"    تاريخ النشر: {published_date}")
            print(f"    اللغة: {book_language}")
            
            # عرض التقييم إذا وُجد
            if average_rating > 0:
                stars = "⭐" * int(average_rating)
                print(f"    التقييم: {average_rating:.1f} {stars} ({ratings_count:,} تقييم)")
            else:
                print(f"    التقييم: غير متوفر")
            
            # محاولة الحصول على أعلى جودة متاحة
            cover_url = None
            quality_level = None
            
            if 'extraLarge' in image_links:
                cover_url = image_links['extraLarge']
                quality_level = "extraLarge (أعلى جودة)"
            elif 'large' in image_links:
                cover_url = image_links['large']
                quality_level = "large (جودة عالية)"
            elif 'medium' in image_links:
                cover_url = image_links['medium']
                quality_level = "medium (جودة متوسطة)"
            elif 'small' in image_links:
                cover_url = image_links['small']
                quality_level = "small (جودة منخفضة)"
            elif 'thumbnail' in image_links:
                cover_url = image_links['thumbnail']
                quality_level = "thumbnail (صورة مصغرة)"
            elif 'smallThumbnail' in image_links:
                cover_url = image_links['smallThumbnail']
                quality_level = "smallThumbnail (صورة صغيرة جداً)"
            
            if cover_url:
                # تحسين جودة الصورة
                cover_url = cover_url.replace('http://', 'https://')
                
                # إزالة قيود الحجم من Google Books
                cover_url = cover_url.replace('&edge=curl', '')
                cover_url = cover_url.replace('zoom=1', 'zoom=3')
                
                # محاولة ترقية الجودة
                if 'zoom=' not in cover_url:
                    cover_url += '&zoom=3'
                
                print(f"    ✅ غلاف متاح ({quality_level})")
                print(f"    URL: {cover_url}")
                
                # تحميل الصورة للتحقق من صحتها
                try:
                    img_response = requests.get(cover_url, headers=headers, timeout=10)
                    img_response.raise_for_status()
                    
                    # حفظ الصورة محلياً
                    safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_'))[:50]
                    img_filename = f"{idx:02d}_{safe_title}.jpg"
                    img_path = COVERS_DIR / img_filename
                    
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    img_size_kb = len(img_response.content) / 1024
                    print(f"    💾 تم التحميل: {img_filename} ({img_size_kb:.1f} KB)")
                    print(f"    📂 الموقع: {img_path}")
                    
                except Exception as download_error:
                    print(f"    ⚠️ فشل التحميل: {download_error}")
                
                return cover_url
            else:
                print(f"    ✗ لا يوجد غلاف")
        
        print("[Google Books] ✗ لم يُعثر على غلاف في جميع النتائج")
        return None
        
    except requests.exceptions.Timeout:
        print("[Google Books] ✗ انتهى الوقت المحدد للطلب")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Google Books] ✗ خطأ في الاتصال: {e}")
        return None
    except Exception as e:
        print(f"[Google Books] ✗ خطأ: {e}")
        return None


def test_googlebooks_covers():
    """اختبار جلب أغلفة الكتب من Google Books"""
    
    print("="*70)
    print("  🧪 اختبار جلب أغلفة الكتب من Google Books")
    print("="*70)
    print(f"  📂 الأغلفة ستُحفظ في: {COVERS_DIR}")
    print("="*70)
    print()
    
    # كتب للاختبار (نفس الكتب من اختبار Amazon)
    test_books = [
        ("Zero to One", "Peter Thiel"),
        ("Atomic Habits", "James Clear"),
        ("The 48 Laws of Power", "Robert Greene"),
        ("Think and Grow Rich", "Napoleon Hill"),
    ]
    
    # إعدادات البحث
    print("⚙️ إعدادات البحث:")
    print("  - اللغة: الإنجليزية فقط (en)")
    print("  - الترتيب: حسب الصلة (relevance)")
    print("  - النوع: كتب فقط (printType=books)")
    print()
    
    results = []
    
    for i, (title, author) in enumerate(test_books, 1):
        print(f"\n{'='*70}")
        print(f"  اختبار #{i}: {title} - {author}")
        print(f"{'='*70}\n")
        
        try:
            # محاولة جلب الغلاف مع الفلاتر
            cover_url = get_cover_from_googlebooks(
                title=title, 
                author=author,
                language="en",  # إنجليزي فقط
                order_by="relevance"  # الأكثر صلة أولاً
            )
            
            if cover_url:
                print(f"\n✅ نجح!")
                print(f"Final URL: {cover_url}")
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
            time.sleep(0.5)
    
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
        print(f"\n📂 افتح المجلد لرؤية الأغلفة:")
        print(f"   {COVERS_DIR}")
    elif success_count > 0:
        print("\n⚠️ بعض الاختبارات نجحت")
        print(f"\n📂 افتح المجلد لرؤية الأغلفة:")
        print(f"   {COVERS_DIR}")
    else:
        print("\n❌ جميع الاختبارات فشلت")
        print("   - تحقق من اتصال الإنترنت")
        print("   - Google Books API قد يكون معطلاً مؤقتاً")


if __name__ == '__main__':
    test_googlebooks_covers()
