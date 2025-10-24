# Fix: YouTube Data API Quota Exceeded

## 🚨 المشكلة
```
⚠️ YouTube Data API: Quota exceeded - Wait or use another key
```

## 🔍 السبب
- YouTube Data API لديه **حد يومي**: 10,000 quota units
- كل بحث = ~100 units
- بعد ~100 بحث/يوم، ينتهي الـ quota
- يتم إعادة ضبطه في **منتصف الليل بتوقيت المحيط الهادئ (PST)**

---

## ✅ الحلول

### الحل 1: انتظر 24 ساعة (مجاني)
- الـ quota يتجدد تلقائياً كل يوم
- لا حاجة لأي إجراء
- **الوقت**: 24 ساعة max

### الحل 2: استخدم YouTube API key آخر (موصى به) ⭐
```bash
# 1. احصل على API key جديد من:
# https://console.cloud.google.com/apis/credentials

# 2. أضف الـ key الجديد في secrets/api_key.txt
# استبدل القديم أو احتفظ بالاثنين (انظر الحل 3)
```

### الحل 3: نظام Fallback (متعدد المفاتيح) - قريباً
حالياً، YouTube API يستخدم مفتاح واحد فقط:
- `secrets/api_key.txt` (مفتاح واحد)

**مقترح تحديث مستقبلي**:
- إضافة دعم `secrets/youtube_api_keys.txt` (مثل Gemini)
- Automatic fallback عند نفاد quota

### الحل 4: استخدم `--skip-api-check` (غير آمن)
```bash
# تجاوز فحص الـ API (مؤقت فقط!)
python -m src.presentation.cli.run_pipeline "الكتاب" --skip-api-check
```

**⚠️ تحذير**: قد تفشل مرحلة البحث لاحقاً!

### الحل 5: زد الحد اليومي (مدفوع)
```bash
# 1. افتح Google Cloud Console:
https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

# 2. اطلب زيادة الـ quota (يتطلب موافقة Google)
# القيمة الافتراضية: 10,000/day
# يمكن زيادتها إلى: 1,000,000/day (برسوم)
```

---

## 🔧 حلول مؤقتة

### استخدام مفتاح بديل حالياً
```bash
# 1. افتح secrets/api_key.txt
notepad secrets\api_key.txt

# 2. استبدل الـ API key:
# من: AIzaSyABC123... (نفذ quota)
# إلى: AIzaSyDEF456... (جديد)

# 3. احفظ الملف
```

### التحقق من استهلاك الـ Quota
```bash
# افتح Google Cloud Console:
https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

# شاهد:
# - Queries per day: 9,874 / 10,000
# - يتجدد في: Oct 25, 12:00 AM PST
```

---

## 📊 فهم YouTube API Quota

### Costs Table

| العملية | Quota Cost |
|---------|------------|
| Search | 100 units |
| Video details | 1 unit |
| Channel info | 1 unit |
| Upload video | 1,600 units |
| Update video | 50 units |

### مثال:
```
معالجة 20 كتاب:
- 20 × بحث (100) = 2,000 units
- 20 × تفاصيل فيديو (1) = 20 units
- 20 × رفع (1,600) = 32,000 units ❌ يتجاوز الحد!

الحل: قسّم على يومين:
- اليوم 1: معالجة 6 كتب (9,600 units)
- اليوم 2: معالجة 6 كتب
- اليوم 3: معالجة 8 كتب
```

---

## 🎯 أفضل الممارسات

### 1. استخدم عدة API keys (Rotation)
```bash
# احصل على 3-5 مفاتيح من مشاريع Google Cloud مختلفة
# قم بتدويرهم يومياً:
# اليوم 1: Key #1
# اليوم 2: Key #2
# اليوم 3: Key #3
```

### 2. راقب الاستهلاك
```bash
# شغل الفحص قبل كل batch:
python main.py
# Option 0 → شاهد "YouTube Data API" status
```

### 3. خطط المعالجة
```bash
# بدلاً من:
# books.txt: 20 كتاب دفعة واحدة ❌

# استخدم:
# day1.txt: 6 كتب
# day2.txt: 6 كتب
# day3.txt: 8 كتب
```

---

## 🔮 تحديثات مستقبلية

نعمل على:
- ✅ دعم `youtube_api_keys.txt` (multi-key fallback)
- ✅ Auto-rotation عند نفاد quota
- ✅ Quota usage tracking
- ✅ تحذيرات استباقية

---

## 📞 الدعم

إذا استمرت المشكلة:
1. تحقق من: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
2. شغل: `python -m src.infrastructure.adapters.api_validator`
3. راجع: `docs/API_KEY_FALLBACK.md`

---

**آخر تحديث**: 2025-10-24
