# 📝 YouTube Sync - Change Log

## التغييرات المطبّقة (2025-10-20)

### ✅ ملفات جديدة:

1. **`docs/DUPLICATE_CHECK_SYSTEM.md`** (التوثيق الكامل)
   - شرح مفصّل للنظام الجديد
   - أمثلة واقعية
   - استكشاف الأخطاء
   - طرق الرجوع للنظام القديم

2. **`YOUTUBE_SYNC_QUICKSTART.md`** (دليل سريع)
   - 3 خطوات للتفعيل
   - حل المشاكل الشائعة

### ✅ ملفات معدّلة:

1. **`src/infrastructure/adapters/database.py`** (+260 سطر)
   ```python
   # الدوال الجديدة:
   - extract_book_from_youtube_title()    # استخلاص اسم الكتاب من العنوان
   - sync_database_from_youtube()         # مزامنة من YouTube
   - ensure_database_synced()             # تأكد من المزامنة
   - _get_youtube_api_key()               # جلب API key
   - _get_channel_id_from_config()        # جلب Channel ID
   - _is_youtube_sync_enabled()           # فحص التفعيل
   - main()                               # CLI entry point
   ```

2. **`config/settings.json`** (+5 أسطر)
   ```json
   {
     "youtube_sync": {
       "enabled": true,
       "channel_id": "YOUR_CHANNEL_ID_HERE",
       "cache_duration_hours": 1
     }
   }
   ```

---

## 🔄 كيف تستخدم النظام الجديد؟

### **السيناريو 1: استخدام تلقائي (موصى به)**

```python
# في run_pipeline.py - في بداية run_full_pipeline():
from src.infrastructure.adapters.database import ensure_database_synced

def run_full_pipeline(query: str, ...):
    # أول شي: تأكد من database
    ensure_database_synced()
    
    # بعدين ابدأ pipeline عادي
    # ...
```

### **السيناريو 2: استخدام يدوي**

```bash
# شغّل sync يدوياً قبل ما تبدأ:
python -m src.infrastructure.adapters.database sync

# بعدين شغّل pipeline:
python main.py
```

---

## 🔙 كيف ترجع للطريقة القديمة؟

### **الطريقة 1: تعطيل الـ Sync**

في `config/settings.json`:
```json
{
  "youtube_sync": {
    "enabled": false  ← غيّرها
  }
}
```

### **الطريقة 2: حذف الكود (Rollback كامل)**

```bash
# 1. راجع هذا الـ commit
git log --oneline -5  # شوف آخر 5 commits

# 2. ارجع للـ commit قبل التغيير
git revert HEAD  # أو git reset --hard <commit-hash>

# 3. أو احذف الكود يدوياً:
# - احذف السطور 393-670 من database.py
# - احذف youtube_sync من settings.json
```

### **الطريقة 3: استخدام Git Tracking بدلاً من YouTube Sync**

```bash
# 1. عطّل YouTube sync (الطريقة 1 أعلاه)

# 2. احذف database.json من .gitignore
# (ابحث عن السطر "database.json" واحذفه)

# 3. تتبع الملف في Git
git add src/database.json
git commit -m "Track database.json in Git"
git push
```

---

## ✅ Checklist قبل التفعيل:

- [ ] عندك YouTube Data API v3 مفعّل في Google Cloud Console
- [ ] API key موجود في `secrets/api_key.txt`
- [ ] تعرف الـ Channel ID حقك
- [ ] أضفت Channel ID في `settings.json`
- [ ] اختبرت الـ sync يدوياً (`python -m ... sync`)
- [ ] العناوين على قناتك بالصيغة الصحيحة (`– Book Name | Book Summary`)

---

## 📊 مقارنة بين الطرق:

| الميزة | YouTube Sync (جديد) | Git Tracking (قديم) | Manual (أقدم) |
|--------|---------------------|---------------------|----------------|
| Cross-environment | ✅ ممتاز | ✅ جيد | ❌ لا |
| Setup | 🟡 متوسط | ✅ بسيط | ✅ بسيط |
| Maintenance | ✅ صفر | 🟡 commits | 🔴 يدوي |
| Speed | 🟡 1-2s | ✅ <0.01s | ✅ <0.01s |
| Reliability | ✅ عالية | 🟡 يعتمد على Git | 🔴 منخفضة |
| API Quota | 🟡 يستهلك | ✅ لا | ✅ لا |

**التوصية:**
- ✅ Local + Colab → **YouTube Sync**
- ✅ Local فقط → **Git Tracking**
- ❌ تجنّب **Manual** (عرضة للأخطاء)

---

## 🐛 المشاكل المحتملة والحلول:

### Problem 1: "403 Quota Exceeded"
```
الحل:
1. انتظر 24 ساعة (quota يتجدد يومياً)
2. أو عطّل الـ sync مؤقتاً:
   {"youtube_sync": {"enabled": false}}
```

### Problem 2: "Could not extract book"
```
الحل:
1. تأكد من صيغة العنوان: "– Book | Book Summary"
2. أو عدّل الـ regex في extract_book_from_youtube_title()
```

### Problem 3: "google-api-python-client not installed"
```
الحل:
pip install google-api-python-client
```

---

## 📞 Support

**إذا واجهت مشكلة:**

1. شيك `runs/.../pipeline.log` للـ errors
2. جرّب manual sync: `python -m src.infrastructure.adapters.database sync`
3. راجع التوثيق الكامل: `docs/DUPLICATE_CHECK_SYSTEM.md`
4. عطّل الـ sync مؤقتاً واستخدم الطريقة القديمة

---

## 📈 Next Steps (اختياري):

### التحسينات المستقبلية:

1. **Caching**: حفظ نتيجة الـ sync لمدة ساعة
2. **Incremental Sync**: جلب الفيديوهات الجديدة فقط
3. **Author Extraction**: استخلاص اسم المؤلف من العنوان
4. **Fuzzy Matching**: مقارنة ذكية بين أسماء الكتب

### الدمج في Pipeline:

```python
# TODO: إضافة في run_pipeline.py
from src.infrastructure.adapters.database import ensure_database_synced

def run_full_pipeline(query: str, ...):
    """Run complete pipeline with auto-sync."""
    
    # 1. Sync database if needed
    ensure_database_synced()
    
    # 2. Existing pipeline code
    # ...
```

---

**Status:** ✅ Ready to use  
**Version:** 1.0.0  
**Date:** 2025-10-20  
**Tested:** ✅ Code complete, awaiting user testing
