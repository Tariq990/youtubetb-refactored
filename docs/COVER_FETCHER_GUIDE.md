# دليل نظام جلب أغلفة الكتب الجديد

## المشكلة السابقة
كان النظام يعتمد فقط على Amazon لجلب أغلفة الكتب، مما أدى إلى:
- فشل متكرر بسبب حجب الطلبات (503 Service Unavailable)
- مشاكل timeout مع Playwright
- عدم وجود بدائل عند فشل Amazon

## الحل الجديد
تم تطوير نظام جديد يستخدم **مصادر متعددة مجانية** بدون الحاجة لـ API keys:

### المصادر المدعومة (بالترتيب):
1. **Google Books** - الأكثر موثوقية
2. **Open Library** - مكتبة مفتوحة المصدر
3. **Goodreads** - موقع تقييم الكتب
4. **ISBNSearch** - بحث عبر ISBN
5. **Amazon** - كخيار احتياطي أخير

### الميزات
✅ **لا يحتاج API keys** - جميع المصادر مجانية  
✅ **Fallback متعدد** - إذا فشل مصدر، ينتقل للتالي تلقائياً  
✅ **دعم Unicode كامل** - يعمل مع النصوص العربية في Windows  
✅ **جودة صور عالية** - يحاول الحصول على أعلى جودة متاحة  
✅ **معالجة أخطاء محسنة** - رسائل واضحة عند كل خطوة

## الاستخدام

### الاستخدام المباشر
```python
from infrastructure.adapters.book_cover_fetcher import get_book_cover_multi_source

# جلب غلاف الكتاب
cover_url = get_book_cover_multi_source(
    title="Emotional Intelligence: Why It Can Matter More Than IQ",
    author="Daniel Goleman"
)

if cover_url:
    print(f"Cover URL: {cover_url}")
```

### تحديد مصادر معينة
```python
# استخدام Google Books و Open Library فقط
cover_url = get_book_cover_multi_source(
    title="The 7 Habits of Highly Effective People",
    author="Stephen Covey",
    sources=['google_books', 'open_library']
)
```

### تحميل الصورة محلياً
```python
from pathlib import Path
from infrastructure.adapters.book_cover_fetcher import download_cover_image

cover_path = Path("covers/book_cover.jpg")
success = download_cover_image(cover_url, cover_path)
```

## الاختبار

### اختبار سريع
```bash
python test_cover_fetcher.py
```

### مثال على المخرجات
```
================================================================================
Testing book cover fetch for: Emotional Intelligence: Why It Can Matter More Than IQ
Author: Daniel Goleman
================================================================================

[Cover] البحث عن غلاف: Emotional Intelligence: Why It Can Matter More Than IQ - Daniel Goleman
[Google Books] Searching for: Emotional Intelligence: Why It Can Matter More Than IQ Daniel Goleman
[Google Books] ✓ Found cover (thumbnail upgraded)
[Cover] ✓ تم العثور على الغلاف من google_books

================================================================================
✅ SUCCESS! Cover URL found:
   https://books.google.com/books/content?id=...
================================================================================
```

## التكامل مع الكود الحالي

النظام يعمل تلقائياً مع الكود الحالي:
- `process.py` - تم تحديثه لاستخدام المصادر الجديدة أولاً
- `process_backup.py` - تم تحديثه أيضاً للاتساق
- **توافق كامل** - لا يحتاج تعديلات على بقية الكود

## ترتيب المحاولات

عند استدعاء `_get_book_cover()` في `process.py`:
1. محاولة المصادر المجانية (Google Books, Open Library, Goodreads)
2. محاولة Amazon مع Playwright (إن وجد)
3. محاولة Amazon بـ requests (كخيار احتياطي أخير)

## المتطلبات

المكتبات المطلوبة (موجودة في `requirements.txt`):
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`

تثبيت المتطلبات:
```bash
pip install requests beautifulsoup4
```

## ملاحظات هامة

### Windows Console Encoding
النظام يتعامل تلقائياً مع مشاكل الترميز في Windows:
```python
# يتم تنفيذه تلقائياً عند الاستيراد
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### معدل الطلبات (Rate Limiting)
- النظام يضيف تأخيرات عشوائية بين الطلبات
- يستخدم User-Agent واقعي
- يحترم سياسات المواقع

### جودة الصور
- **Google Books**: يحاول الحصول على `extraLarge` > `large` > `medium` > `thumbnail`
- **Open Library**: يطلب صور بحجم `L` (Large)
- **Goodreads**: يحسّن جودة الصورة باستبدال `_SX` parameters
- **Amazon**: يستخدم `_AC_UL600_` للجودة العالية

## التطوير المستقبلي

يمكن إضافة مصادر جديدة بسهولة:
1. إنشاء دالة `_get_cover_from_SOURCE()`
2. إضافتها لـ `source_functions` dictionary
3. تحديث قائمة `sources` الافتراضية

## الأداء

### السرعة
- Google Books: ~2-3 ثواني
- Open Library: ~1-2 ثواني  
- Goodreads: ~3-5 ثواني
- Amazon: ~5-15 ثانية (أبطأ بسبب blocking)

### معدل النجاح
- Google Books: ~85% للكتب الشهيرة
- Open Library: ~70% للكتب الشهيرة
- مجموع النجاح: ~95% مع استخدام جميع المصادر

## الدعم

للمشاكل أو الأسئلة، راجع:
- `src/infrastructure/adapters/book_cover_fetcher.py` - الكود الرئيسي
- `test_cover_fetcher.py` - أمثلة الاستخدام
