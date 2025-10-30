# Cookies Fallback System - نظام الفولباك للكوكيز

## 📋 نظرة عامة

نظام **Fallback للكوكيز** يعمل الآن بنفس طريقة عمل API keys (Gemini و YouTube و Pexels). النظام يبحث عن ملفات cookies في عدة مواقع ويستخدم أول ملف صالح بترتيب الأولوية.

## 🎯 المشكلة التي تم حلها

### قبل التحديث:
```python
# كان يبحث فقط في مكانين:
cookie_paths = [
    "secrets/cookies.txt",
    "cookies.txt"
]

# لا يوجد نظام fallback
# لا يوجد تحقق من صلاحية الملف
# رسائل خطأ غير واضحة
```

### بعد التحديث:
```python
# يبحث في 5 مواقع بترتيب الأولوية:
cookie_paths = [
    "secrets/cookies.txt",      # Priority 1: Main
    "secrets/cookies_1.txt",    # Priority 2: Fallback 1
    "secrets/cookies_2.txt",    # Priority 3: Fallback 2
    "secrets/cookies_3.txt",    # Priority 4: Fallback 3
    "cookies.txt"               # Priority 5: Root fallback
]

# مع نظام fallback ذكي
# تحقق من صلاحية كل ملف
# رسائل واضحة ومفصلة
```

## 🔄 كيف يعمل النظام؟

### 1️⃣ البحث عن الملفات (Scan)
```python
# النظام يفحص كل ملف cookies بالترتيب:
for idx, cookie_file in enumerate(cookie_paths, 1):
    if exists(cookie_file):
        # تحقق من الحجم (> 50 بايت)
        # تحقق من المحتوى (ليس HTML)
        # تحقق من الصيغة (صالح)
        if valid:
            cookies_found.append(cookie_file)
```

### 2️⃣ اختيار الملف الأساسي (Primary Selection)
```python
# استخدام أول ملف صالح:
if cookies_found:
    primary = cookies_found[0]  # أعلى أولوية
    backups = cookies_found[1:]  # ملفات احتياطية
```

### 3️⃣ الإبلاغ عن النتائج (Reporting)
```python
print(f"🍪 Cookies found: {len(cookies_found)} valid file(s)")
print(f"   Primary: {primary}")
if backups:
    print(f"   Backup: {len(backups)} fallback file(s)")
```

## 📂 مواقع البحث (بالترتيب)

| الأولوية | المسار | الاستخدام |
|---------|--------|----------|
| **1** | `secrets/cookies.txt` | **الملف الرئيسي** - استخدمه للكوكيز الأساسية |
| **2** | `secrets/cookies_1.txt` | احتياطي 1 - إذا انتهت صلاحية الرئيسي |
| **3** | `secrets/cookies_2.txt` | احتياطي 2 - حساب بديل |
| **4** | `secrets/cookies_3.txt` | احتياطي 3 - حساب إضافي |
| **5** | `cookies.txt` | احتياطي نهائي - في جذر المشروع |

## 🛠️ الإعداد والاستخدام

### خطوة 1: تصدير الكوكيز من المتصفح

#### Chrome / Edge:
1. ثبّت إضافة: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. افتح YouTube وسجل دخول
3. اضغط على أيقونة الإضافة
4. احفظ الملف باسم `cookies.txt`

#### Firefox:
1. ثبّت إضافة: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. افتح YouTube وسجل دخول
3. اضغط F12 → Console → اكتب `document.cookie`
4. صدّر باستخدام الإضافة

### خطوة 2: نقل الملف إلى المشروع

```bash
# انقل الملف إلى المجلد الصحيح:
move cookies.txt C:\path\to\project\secrets\cookies.txt

# أو إنشاء نسخ احتياطية:
copy cookies.txt secrets\cookies.txt
copy cookies_alt.txt secrets\cookies_1.txt
copy cookies_backup.txt secrets\cookies_2.txt
```

### خطوة 3: التحقق من النظام

```bash
# اختبر نظام الـ Fallback:
python scripts\test_cookies_fallback.py
```

**النتيجة المتوقعة:**
```
🍪 COOKIES FALLBACK SYSTEM TEST
============================================================

📂 Checking cookie file locations (in priority order):

1. [✅ VALID] C:\...\secrets\cookies.txt
   (15234 bytes, 187 lines)

2. [✅ VALID] C:\...\secrets\cookies_1.txt
   (14981 bytes, 182 lines)

3. [❌ Not found] C:\...\secrets\cookies_2.txt

============================================================
📊 RESULTS:
============================================================

✅ Found 2 valid cookies file(s)!

🔑 Primary cookies: C:\...\secrets\cookies.txt

📋 Backup cookies (1 file(s)):
   - C:\...\secrets\cookies_1.txt

💡 System will use PRIMARY cookies for all operations
   If primary fails → automatic fallback to backups
```

## 🔍 التحقق من الصلاحية (Validation)

النظام يتحقق من كل ملف cookies بهذه الطريقة:

### ✅ ملف صالح:
```
- الحجم > 50 بايت
- المحتوى ليس فارغ
- ليس HTML error page (لا يبدأ بـ <!DOCTYPE)
- له أسطر متعددة (cookies format)
```

### ⚠️ ملف غير صالح:
```
- حجم صغير جداً (< 50 بايت)
- ملف فارغ
- صفحة HTML (خطأ تنزيل)
- صيغة خاطئة
```

## 🔐 الأمان والخصوصية

### ⚠️ تحذير هام:
```
الكوكيز تحتوي على معلومات حساسة!
- لا تشارك ملفات cookies مع أحد
- لا تنشرها على GitHub (موجودة في .gitignore)
- احذفها فوراً بعد انتهاء المشروع
```

### الحماية في المشروع:
```gitignore
# ملف .gitignore يحمي كل ملفات cookies:
secrets/
*.txt
cookies*.txt
```

## 📊 الأمثلة العملية

### مثال 1: ملف واحد صالح
```
Input:
- secrets/cookies.txt ✅ (صالح)

Output:
🍪 Primary: secrets/cookies.txt
📋 No backups available
```

### مثال 2: ملفات متعددة
```
Input:
- secrets/cookies.txt ✅ (صالح)
- secrets/cookies_1.txt ✅ (صالح)
- secrets/cookies_2.txt ❌ (غير موجود)

Output:
🍪 Primary: secrets/cookies.txt
📋 Backup: 1 fallback file (cookies_1.txt)
```

### مثال 3: لا يوجد ملفات
```
Input:
- جميع المواقع فارغة

Output:
❌ No valid cookies files found!
⚠️  Some videos may fail (age-restricted)

💡 To fix:
   1. Install 'Get cookies.txt LOCALLY' extension
   2. Login to YouTube
   3. Export cookies
   4. Save to: secrets/cookies.txt
```

## 🔄 التكامل مع Pipeline

### في `transcribe.py`:
```python
# النظام يبحث تلقائياً عن cookies:
cookies = find_valid_cookies()  # Fallback system

# استخدام مع yt-dlp:
if cookies:
    ydl_opts['cookiefile'] = str(cookies)
```

### في `run_pipeline.py` (Preflight):
```python
# التحقق من cookies قبل بدء Pipeline:
def _preflight_check():
    # ... other checks ...
    
    # Cookies check with fallback
    cookies_found = scan_cookies_files()
    
    if cookies_found:
        print(f"✓ {len(cookies_found)} cookies available")
    else:
        if require_cookies:
            raise Error("Cookies required!")
        else:
            print("⚠️  Proceeding without cookies")
```

## 🧪 الاختبار

### اختبار سريع:
```bash
python scripts\test_cookies_fallback.py
```

### اختبار كامل مع Pipeline:
```bash
python main.py
# اختر Option 0: System Check
```

### اختبار يدوي:
```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

cookie_paths = [
    REPO_ROOT / "secrets" / "cookies.txt",
    REPO_ROOT / "secrets" / "cookies_1.txt",
    # ... etc
]

for cp in cookie_paths:
    if cp.exists():
        size = cp.stat().st_size
        print(f"✓ {cp.name}: {size} bytes")
```

## 📈 الفوائد

### ✅ المزايا:
1. **Reliability**: إذا فشل ملف cookies → تبديل تلقائي للاحتياطي
2. **Multi-Account**: استخدام cookies من حسابات مختلفة
3. **Consistency**: نفس نظام API keys (موحد)
4. **Validation**: تحقق تلقائي من صلاحية الملفات
5. **User-Friendly**: رسائل واضحة ومفيدة

### ⚡ حالات الاستخدام:
- **Age-restricted videos**: تحتاج cookies صالحة
- **Members-only content**: cookies من حساب مشترك
- **Rate limiting**: تبديل cookies عند الحظر
- **Geographic restrictions**: cookies من مناطق مختلفة

## 🐛 استكشاف الأخطاء

### المشكلة: "No valid cookies found"
```bash
# الحل:
1. تأكد من تسجيل الدخول في YouTube
2. صدّر cookies باستخدام إضافة صحيحة
3. تحقق من المسار: secrets/cookies.txt
4. تحقق من الحجم: > 50 بايت
```

### المشكلة: "Cookies invalid format"
```bash
# الحل:
1. لا تفتح الملف في Notepad (قد يفسد الترميز)
2. استخدم إضافة متصفح موثوقة
3. تأكد من التصدير من YouTube.com (ليس من تطبيق)
4. أعد التصدير إذا لزم الأمر
```

### المشكلة: "Video still fails with cookies"
```bash
# الحل:
1. تأكد من أن cookies حديثة (< 30 يوم)
2. سجل دخول مجدداً وصدّر cookies جديدة
3. جرب cookies من حساب آخر (cookies_1.txt)
4. تحقق من أن الفيديو متاح في منطقتك
```

## 📝 الملاحظات الفنية

### التوافق مع yt-dlp:
```python
# yt-dlp يقبل ملفات cookies بصيغة Netscape:
# # Netscape HTTP Cookie File
# .youtube.com	TRUE	/	TRUE	0	...
```

### التحديث التلقائي:
```python
# الكوكيز تنتهي صلاحيتها، لذلك:
- راقب رسائل الخطأ "401 Unauthorized"
- صدّر cookies جديدة كل شهر
- احتفظ بنسخ احتياطية في cookies_1.txt
```

## 🎯 الخلاصة

نظام Fallback للكوكيز الآن **مطابق تماماً** لنظام API keys:

| Feature | API Keys | Cookies |
|---------|----------|---------|
| Multi-file support | ✅ | ✅ |
| Priority order | ✅ | ✅ |
| Auto-validation | ✅ | ✅ |
| Fallback on failure | ✅ | ✅ |
| Clear error messages | ✅ | ✅ |
| Test script | ✅ | ✅ |

---

**آخر تحديث**: 2025-10-30  
**الإصدار**: v2.3.0  
**التغييرات**: إضافة نظام Fallback كامل للكوكيز مطابق لـ API keys
