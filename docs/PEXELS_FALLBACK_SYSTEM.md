# 🎬 Pexels API Fallback System

## ✅ ما تم إضافته؟

نظام **Fallback لـ Pexels API** الآن مطابق لأنظمة Fallback الأخرى (Gemini, YouTube, Cookies).

---

## 📂 المواقع المدعومة (بالترتيب)

| الأولوية | الموقع | الاستخدام |
|---------|--------|----------|
| **1** | `PEXELS_API_KEY` (env) | **متغير البيئة** - أعلى أولوية |
| **2** | `secrets/.env` | ملف .env الأساسي |
| **3** | `secrets/pexels_key.txt` | **موصى به** - ملف مخصص لـ Pexels |
| **4** | `secrets/api_keys.txt` | ملف API keys المشترك |
| **5** | `secrets/api_key.txt` | ملف API key القديم |
| **6** | `.env` | ملف .env في جذر المشروع |

---

## 🔍 كيف يعمل؟

### 1️⃣ البحث (Scan)
```python
# يفحص 6 مواقع بالترتيب:
1. Environment variable: PEXELS_API_KEY
2. secrets/.env (PEXELS_API_KEY=...)
3. secrets/pexels_key.txt (نص عادي)
4. secrets/api_keys.txt (سطر واحد أو أكثر)
5. secrets/api_key.txt (للتوافق القديم)
6. .env في الجذر
```

### 2️⃣ التحقق (Validate)
```python
# كل ملف يُتحقق منه:
✓ الملف موجود
✓ الحجم > 20 حرف (API key صالح)
✓ ليس تعليق (لا يبدأ بـ #)
✓ صيغة .env أو نص عادي
```

### 3️⃣ الاختيار (Select)
```python
# يستخدم أول API key صالح
if api_keys_found:
    primary = api_keys_found[0]  # الأساسي
    backups = api_keys_found[1:]  # احتياطي
```

---

## 🛠️ الإعداد والاستخدام

### الطريقة الموصى بها:

#### 1. احصل على API Key من Pexels:
```
🔗 https://www.pexels.com/api/
- سجل حساب مجاني
- انتقل إلى Dashboard
- انسخ API Key الخاص بك
```

#### 2. احفظ الـ API Key:

**الخيار 1: ملف مخصص (موصى به)**
```bash
# أنشئ ملف: secrets/pexels_key.txt
# الصق الـ API Key فقط (سطر واحد)
YOUR_PEXELS_API_KEY_HERE
```

**الخيار 2: ملف .env**
```bash
# أضف إلى: secrets/.env
PEXELS_API_KEY=YOUR_PEXELS_API_KEY_HERE
```

**الخيار 3: متغير البيئة**
```bash
# Windows (PowerShell):
$env:PEXELS_API_KEY="YOUR_KEY"

# Linux/Mac:
export PEXELS_API_KEY="YOUR_KEY"
```

---

## 📊 أمثلة الاستخدام

### مثال 1: ملف مخصص
```
secrets/pexels_key.txt:
├── 563492ad6f917000010000017a2c79b55b394f1899d14ac1bfe1
```

**النتيجة**:
```
[Pexels] ✓ Valid API key 3/6: pexels_key.txt
[Pexels] 🔑 Using primary API key from: pexels_key.txt
```

---

### مثال 2: ملف .env
```
secrets/.env:
├── GEMINI_API_KEY=AIza...
├── PEXELS_API_KEY=563492ad6f917000010000017a2c79b55b394f1899d14ac1bfe1
├── YT_API_KEY=AIza...
```

**النتيجة**:
```
[Pexels] ✓ Valid API key 2/6: .env
[Pexels] 🔑 Using primary API key from: .env
```

---

### مثال 3: ملفات متعددة (Fallback)
```
Input:
- secrets/.env ✅ (PEXELS_API_KEY=key1)
- secrets/pexels_key.txt ✅ (key2)
- secrets/api_keys.txt ✅ (key3 في السطر الأول)

Output:
[Pexels] ✓ Valid API key 2/6: .env
[Pexels] ✓ Valid API key 3/6: pexels_key.txt
[Pexels] ✓ Valid API key 4/6: api_keys.txt
[Pexels] 🔑 Using primary API key from: .env
[Pexels] 📋 2 backup API key(s) available for fallback
```

---

## 🎯 الفوائد

### ✅ المزايا:
1. **Multi-Source**: 6 مواقع مختلفة للبحث
2. **Fallback**: تبديل تلقائي إذا فشل الأول
3. **Flexibility**: دعم .env ونص عادي
4. **User-Friendly**: رسائل واضحة ومفيدة
5. **Consistent**: مطابق لأنظمة Fallback الأخرى

---

## 📝 الملفات المعدلة

### 1. `src/infrastructure/adapters/shorts_generator.py`
**الوظيفة**: `_fetch_pexels_videos()`

**التغييرات**:
- أضيف نظام Fallback كامل (6 مواقع)
- تحقق ذكي من الملفات
- دعم .env ونص عادي
- رسائل مفصلة

**قبل**:
```python
api_key = os.getenv("PEXELS_API_KEY")
if not api_key:
    # بحث بسيط في .env فقط
```

**بعد**:
```python
# نظام Fallback كامل (6 مواقع)
# تحقق من كل موقع
# استخدام أول API key صالح
# عرض backup keys المتاحة
```

---

### 2. `src/presentation/cli/check_apis.py`
**الوظيفة**: `check_pexels_api()`

**التغييرات**:
- نفس نظام Fallback
- تحقق من 6 مواقع
- دعم .env ونص عادي

---

## 🔐 الأمان

### ⚠️ تحذير:
```
API Keys حساسة!
- لا تشاركها مع أحد
- لا تنشرها على GitHub (.gitignore محمي)
- احذفها بعد انتهاء المشروع
```

### الحماية:
```gitignore
secrets/          # محمي بالكامل
*.env             # جميع ملفات .env
pexels_key.txt    # ملف Pexels المخصص
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: "No valid PEXELS_API_KEY found"
```bash
# الحل:
1. تأكد من API key صحيح (من pexels.com/api)
2. تحقق من الحفظ في أحد المواقع الصحيحة
3. تأكد من عدم وجود مسافات إضافية
4. تحقق من صيغة .env: PEXELS_API_KEY=...
```

### المشكلة: "401 Unauthorized"
```bash
# الحل:
1. API key منتهي أو غير صالح
2. احصل على key جديد من pexels.com
3. تحقق من نسخ الـ key كاملاً
```

---

## 🎯 المقارنة مع الأنظمة الأخرى

| الميزة | Gemini | YouTube | Cookies | Pexels |
|--------|--------|---------|---------|--------|
| Multi-file | ✅ | ✅ | ✅ | ✅ |
| Priority order | ✅ | ✅ | ✅ | ✅ |
| Validation | ✅ | ✅ | ✅ | ✅ |
| Fallback | ✅ | ✅ | ✅ | ✅ |
| .env support | ✅ | ✅ | ❌ | ✅ |
| Plain text | ✅ | ✅ | ✅ | ✅ |

**النتيجة**: ✅ **جميع الأنظمة متطابقة!**

---

## 📚 الموارد

### الحصول على API Key:
- 🔗 **Pexels API**: https://www.pexels.com/api/
- 📖 **Documentation**: https://www.pexels.com/api/documentation/
- 💰 **Pricing**: مجاني (200 requests/ساعة، 20,000 requests/شهر)

### ملفات المشروع:
- `src/infrastructure/adapters/shorts_generator.py` - نظام Fallback
- `src/presentation/cli/check_apis.py` - اختبار API
- `secrets/.env` - ملف .env الرئيسي
- `secrets/pexels_key.txt` - ملف مخصص (موصى به)

---

## 🎉 الخلاصة

**نظام الفولباك بشتغل ع Pexels API زي باقي الأنظمة** ✅

الآن:
- ✅ دعم 6 مواقع مختلفة
- ✅ تبديل تلقائي عند الفشل
- ✅ تحقق ذكي من الملفات
- ✅ رسائل واضحة ومفيدة
- ✅ متطابق مع Gemini/YouTube/Cookies

---

**الإصدار**: v2.3.0  
**التاريخ**: 2025-10-30  
**الحالة**: ✅ مكتمل  
**موقع API Key**: https://www.pexels.com/api/
