# YouTubeTB - تثبيت بدون بيئة افتراضية

## ✅ مميزات هذه الطريقة
- **أسرع**: لا حاجة لإنشاء venv
- **أبسط**: تثبيت مباشر على system Python
- **مشاركة المكتبات**: استخدام نفس المكتبات لكل المشاريع

## ⚠️ تحذيرات
- **تضارب النسخ**: قد تتعارض مع مشاريع أخرى
- **Permissions**: قد تحتاج admin rights
- **Cleanup صعب**: حذف المكتبات أصعب من حذف venv

---

## 📋 المتطلبات الأساسية

### 1. Python 3.10 أو أحدث
```bash
python --version
# يجب أن يكون: Python 3.10.x أو أعلى
```

### 2. FFmpeg
```bash
# تحميل من: https://ffmpeg.org/download.html
# أو عبر chocolatey:
choco install ffmpeg

# تحقق:
ffmpeg -version
```

### 3. Git (للاستنساخ)
```bash
git --version
```

---

## 🚀 خطوات التثبيت

### الطريقة 1: تثبيت تلقائي (موصى به)

```bash
# 1. استنسخ المشروع
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored

# 2. شغل السكريبت التلقائي
install_system.bat

# 3. تحقق من التثبيت
python check_system.py
```

### الطريقة 2: تثبيت يدوي

```bash
# 1. استنسخ المشروع
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored

# 2. ثبت المكتبات
pip install -r requirements.txt

# 3. ثبت Playwright browsers
playwright install chromium

# 4. ثبت yt-dlp (إذا لم يكن مثبت)
pip install yt-dlp

# 5. تحقق من التثبيت
python check_system.py
```

---

## 🔑 إعداد Secrets

### نسخ ملفات Secrets

```bash
# على الجهاز الجديد:
mkdir secrets

# انسخ الملفات التالية إلى secrets/:
# - api_key.txt (Gemini API)
# - api_keys.txt (Gemini fallback keys)
# - client_secret.json (YouTube OAuth)
# - cookies.txt (YouTube cookies)
```

### أو استخدم Encrypted Secrets

```bash
# على الجهاز الأول (إذا لم تفعل هذا بعد):
python scripts\encrypt_secrets.py
git add secrets_encrypted/
git commit -m "Add encrypted secrets"
git push

# على الجهاز الجديد:
git pull
python scripts\decrypt_secrets.py
# أدخل الـ password
```

---

## ✅ التحقق من التثبيت

```bash
# فحص شامل
python check_system.py
```

**المخرجات المتوقعة:**
```
==================================================
YouTubeTB System Environment Check
==================================================

[1] Python Version:
✓ Python 3.11.5

[2] Critical Python Packages:
✓ google-generativeai
✓ playwright
✓ yt-dlp
✓ Pillow
✓ requests
✓ typer
✓ rich

[3] Optional Packages:
✓ arabic-reshaper
✓ python-bidi
✓ absl-py

[4] External Tools:
✓ ffmpeg: ffmpeg version 6.0
✓ yt-dlp: 2023.10.13

[5] Playwright Browsers:
✓ Chromium browser installed

[6] Secrets Files:
✓ api_key.txt
✓ client_secret.json
✓ cookies.txt

==================================================
✅ ALL CHECKS PASSED!
   You can run: python main.py
==================================================
```

---

## 🎯 تشغيل البرنامج

```bash
# تشغيل القائمة التفاعلية
python main.py

# أو مباشرة
python -m src.presentation.cli.run_pipeline "العادات الذرية"
```

---

## 🐛 حل المشاكل

### مشكلة 1: "ModuleNotFoundError"
```bash
# السبب: مكتبة ناقصة
# الحل:
pip install <missing-package>

# أو أعد تثبيت كل المكتبات:
pip install -r requirements.txt --force-reinstall
```

### مشكلة 2: "Permission denied"
```bash
# السبب: تحتاج admin rights
# الحل: شغل cmd as Administrator
# Right-click → Run as administrator
pip install -r requirements.txt
```

### مشكلة 3: تضارب نسخ المكتبات
```bash
# السبب: نسخة قديمة مثبتة
# الحل: حدّث المكتبة
pip install <package> --upgrade

# أو حدّث كل شي:
pip install -r requirements.txt --upgrade
```

### مشكلة 4: "FFmpeg not found"
```bash
# الحل 1: ثبت عبر chocolatey
choco install ffmpeg

# الحل 2: تحميل يدوي
# 1. حمل من: https://ffmpeg.org/download.html
# 2. فك الضغط إلى C:\ffmpeg
# 3. أضف C:\ffmpeg\bin إلى PATH
```

### مشكلة 5: Playwright browser not found
```bash
# الحل:
python -m playwright install chromium
```

---

## 🔄 التحديث

```bash
# سحب آخر تحديثات
git pull origin master

# تحديث المكتبات
pip install -r requirements.txt --upgrade
```

---

## 🗑️ إزالة التثبيت

```bash
# إزالة المشروع
cd ..
rmdir /s /q youtubetb-refactored

# (اختياري) إزالة المكتبات
pip uninstall -r requirements.txt -y
```

**ملاحظة**: إزالة المكتبات قد تؤثر على مشاريع Python أخرى!

---

## 📊 مقارنة: System vs Virtual Environment

| الميزة | System Python | Virtual Environment |
|--------|--------------|---------------------|
| السرعة | ⚡ أسرع | 🐢 أبطأ قليلاً |
| البساطة | ✅ بسيط جداً | ⚠️ خطوات إضافية |
| العزل | ❌ لا عزل | ✅ عزل كامل |
| تضارب النسخ | ⚠️ محتمل | ✅ مستحيل |
| التنظيف | ❌ صعب | ✅ حذف مجلد واحد |
| Disk Space | ✅ أقل | ⚠️ أكثر |
| للمبتدئين | ✅ موصى به | ⚠️ معقد |
| للمحترفين | ⚠️ خطر | ✅ موصى به |

---

## 💡 التوصية

- **للاستخدام الشخصي**: System Python (هذا الدليل) ✅
- **للتطوير**: Virtual Environment (`install_complete.bat`) ✅
- **للسيرفرات/الإنتاج**: Docker container 🐳

---

## 📞 الدعم

إذا واجهت مشاكل:
1. شغل `python check_system.py` لفحص المشكلة
2. راجع `docs/QUICK_START.md`
3. افتح issue على GitHub

---

**آخر تحديث**: 2025-10-24
