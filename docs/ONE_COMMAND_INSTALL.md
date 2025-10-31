# 🚀 YouTubeTB - تثبيت بأمر واحد

## ⚡ الطريقة الأسرع والأسهل

### خطوة واحدة فقط:

```batch
# نزّل المشروع وشغّل:
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored
SETUP_ALL.bat
```

**هذا كل شيء!** 🎉

---

## 🎯 ماذا يفعل SETUP_ALL.bat؟

السكريبت **ذكي** ويتعامل مع كل شيء تلقائياً:

### 1. 🔍 يكتشف المشاكل
- ✅ هل Python مثبت؟ → إذا لا، ينزله ويثبته
- ✅ هل FFmpeg موجود؟ → إذا لا، ينزله ويثبته
- ✅ هل في venv قديم؟ → يحذفه وينشئ واحد جديد
- ✅ هل في مكتبات ناقصة؟ → يثبتها واحدة واحدة

### 2. 🔧 يصلح المشاكل
- ✅ Python 3.14 ومشكلة numba؟ → يثبت بدون openai-whisper
- ✅ صلاحيات Admin ناقصة؟ → يعيد التشغيل بصلاحيات
- ✅ PATH غير محدّث؟ → يحدثه تلقائياً
- ✅ تنزيل فشل؟ → يجرب طريقة بديلة

### 3. 📦 يثبت كل شيء
- ✅ Python (أي إصدار - بدون قيود)
- ✅ FFmpeg (من أكثر من مصدر)
- ✅ Virtual Environment جديد
- ✅ جميع المكتبات المطلوبة
- ✅ Playwright browsers
- ✅ فك تشفير الـ secrets (إذا موجودة)

### 4. ✅ يتحقق من النتيجة
- ✅ يختبر كل المكتبات المهمة
- ✅ يتأكد من FFmpeg
- ✅ يفحص ملفات الـ secrets
- ✅ يعطيك تقرير نهائي واضح

---

## 🎬 مثال على الاستخدام

```batch
C:\Users\YourName> git clone https://github.com/Tariq990/youtubetb-refactored.git
C:\Users\YourName> cd youtubetb-refactored
C:\Users\YourName\youtubetb-refactored> SETUP_ALL.bat

╔══════════════════════════════════════════════════════════╗
║         YouTubeTB - Smart Auto-Installer v3.0           ║
║     Detects Problems → Fixes → Installs → Verifies      ║
╚══════════════════════════════════════════════════════════╝

[1/10] 🔐 Checking administrator rights...
   ✅ Administrator rights confirmed

[2/10] 🐍 Checking Python installation...
   ✅ Python 3.14.0 detected
   ℹ️  Any Python version accepted (no restrictions)

[3/10] 🎬 Checking FFmpeg...
   ✅ FFmpeg already installed

[4/10] 🧹 Checking virtual environment...
   🗑️  Removing old virtual environment...
   ✅ Old venv removed

[5/10] 🏗️  Creating new virtual environment...
   ✅ Virtual environment created

[6/10] 📦 Upgrading pip and installing build tools...
   ✅ pip upgraded

[7/10] 📚 Installing Python dependencies...
   ℹ️  This may take 5-15 minutes depending on your Python version
   
   ⚠️  openai-whisper installation failed
   💡 This is normal for Python 3.14+ (numba incompatibility)
   🔧 Installing without whisper (word-level subtitles disabled)
   
   🔍 Verifying critical packages...
   ✅ google-generativeai
   ✅ playwright
   ✅ yt-dlp
   ✅ Pillow
   ✅ requests
   ✅ typer
   ✅ rich
   
   ✅ Python packages installed

[8/10] 🌐 Installing Playwright browsers...
   ✅ Chromium browser installed

[9/10] 🔐 Setting up secrets...
   📁 Found encrypted secrets
   🔑 Enter decryption password (or press Enter to skip):
   ****
   ✅ Secrets decrypted successfully

[10/10] ✅ Verifying installation...
   
   🐍 Python Packages:
      ✅ rich
      ✅ typer
      ✅ google.generativeai
   
   🛠️  External Tools:
      ✅ FFmpeg
   
   📂 Secrets:
      ✅ api_key.txt
      ✅ cookies.txt

╔══════════════════════════════════════════════════════════╗
║              ✅ INSTALLATION COMPLETE! ✅               ║
╚══════════════════════════════════════════════════════════╝

🚀 Quick Start:
   1. Activate venv:  venv\Scripts\activate
   2. Run program:    python main.py

Press any key to continue...
```

---

## ⚙️ خيارات متقدمة

### فك تشفير تلقائي (بدون كتابة password):

```batch
# ضع الـ password في متغير البيئة:
setx YTTB_SECRETS_PASSWORD "your_password_here"

# افتح نافذة CMD جديدة، ثم:
SETUP_ALL.bat
# سيفك التشفير تلقائياً بدون سؤال!
```

### تثبيت صامت (بدون توقف):

```batch
# عدّل SETUP_ALL.bat واحذف السطر الأخير:
# pause
```

---

## 🆚 مقارنة مع السكريبتات القديمة

| الميزة | SETUP_ALL.bat | install_complete.bat | install_system.bat |
|--------|---------------|----------------------|-------------------|
| **يكتشف المشاكل** | ✅ نعم | ⚠️ جزئي | ⚠️ جزئي |
| **يصلح تلقائياً** | ✅ نعم | ❌ لا | ❌ لا |
| **Python 3.14+** | ✅ يشتغل | ❌ يفشل | ❌ يفشل |
| **تنزيل FFmpeg** | ✅ تلقائي | ✅ تلقائي | ❌ يدوي |
| **محاولات بديلة** | ✅ نعم | ⚠️ محدود | ❌ لا |
| **تحقق نهائي** | ✅ شامل | ⚠️ بسيط | ⚠️ بسيط |
| **رسائل واضحة** | ✅ ✅ ✅ | ✅ | ⚠️ |
| **Admin auto-restart** | ✅ نعم | ❌ لا | ❌ لا |

**التوصية:** استخدم `SETUP_ALL.bat` دائماً! 🎯

---

## 🐛 حل المشاكل

### مشكلة: "Access Denied" أو "Permission Error"

```batch
# الحل: شغّل كـ Administrator
# Right-click على SETUP_ALL.bat → Run as administrator
```

> 💡 السكريبت يعيد التشغيل تلقائياً بصلاحيات إذا اكتشف عدم وجودها

---

### مشكلة: تنزيل Python أو FFmpeg فشل

```batch
# الحل 1: حاول مرة ثانية (قد تكون مشكلة إنترنت)
SETUP_ALL.bat

# الحل 2: نزّل يدوياً:
# Python: https://www.python.org/downloads/
# FFmpeg: https://ffmpeg.org/download.html
# ثم شغّل SETUP_ALL.bat مرة أخرى
```

---

### مشكلة: openai-whisper لم يثبت

```batch
# هذا طبيعي لـ Python 3.14+
# ✅ البرنامج يشتغل بدونه (فقط word-level subtitles معطلة)
# 💡 إذا تبي whisper، استخدم Python 3.13:
# 1. امسح Python 3.14
# 2. نزّل Python 3.13 من python.org
# 3. شغّل SETUP_ALL.bat مرة أخرى
```

---

### مشكلة: بعد التثبيت، `python main.py` يعطي أخطاء

```batch
# تأكد إنك مفعّل الـ venv:
venv\Scripts\activate

# ثم:
python main.py
```

> ⚠️ **مهم:** لازم تفعّل venv دائماً قبل تشغيل البرنامج!

---

## 📋 متطلبات النظام

- ✅ Windows 10/11
- ✅ اتصال إنترنت (لتنزيل المكونات)
- ✅ ~2 GB مساحة فارغة
- ⚠️ صلاحيات Administrator (السكريبت يطلبها تلقائياً)

---

## 🚀 بعد التثبيت

### 1. فعّل البيئة الافتراضية:

```batch
venv\Scripts\activate
```

### 2. شغّل البرنامج:

```batch
python main.py
```

### 3. اختر من القائمة:

```
1. Process single book
2. Process multiple books from books.txt
3. Resume failed run
...
```

---

## 📚 روابط مفيدة

- **دليل البداية السريعة:** `docs\QUICK_START.md`
- **حل المشاكل الشامل:** `docs\TROUBLESHOOTING.md`
- **إعداد الـ Cookies:** `docs\COOKIES_SETUP.md`
- **دليل Python Version:** `docs\PYTHON_VERSION_FIX.md`

---

## 💡 نصائح

### ✅ افعل:
- استخدم `SETUP_ALL.bat` للتثبيت الأول
- فعّل venv قبل تشغيل البرنامج
- اقرأ الرسائل أثناء التثبيت (توجهك للحلول)

### ❌ لا تفعل:
- لا تقاطع التثبيت أثناء تنزيل المكونات
- لا تحذف venv بعد التثبيت
- لا تشغل البرنامج بدون تفعيل venv

---

## 🎯 الخلاصة

**أمر واحد = تثبيت كامل:**

```batch
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored
SETUP_ALL.bat
```

**ثم شغّل:**

```batch
venv\Scripts\activate
python main.py
```

**هذا كل شيء!** 🎉

---

**آخر تحديث:** 31 أكتوبر 2025  
**الإصدار:** v3.0 - Smart Installer
