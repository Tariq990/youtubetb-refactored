# دليل البدء السريع - YouTubeTB

## 📦 التثبيت على Windows

### المتطلبات الأساسية:

1. **Python 3.10 أو أحدث**
   - تحميل من: https://www.python.org/downloads/
   - ✅ تأكد من تفعيل "Add Python to PATH" أثناء التثبيت

2. **FFmpeg**
   - تحميل من: https://www.gyan.dev/ffmpeg/builds/
   - اختر: `ffmpeg-release-essentials.zip`
   - فك الضغط وأضف مجلد `bin` إلى PATH

3. **Git** (اختياري)
   - تحميل من: https://git-scm.com/download/win

---

## 🚀 خطوات التشغيل

### 1. فك ضغط المشروع

```cmd
# فك ضغط youtubetb_refactored.zip إلى مجلد على جهازك
# مثلاً: C:\Users\YourName\youtubetb_refactored
```

### 2. فتح Command Prompt في مجلد المشروع

```cmd
cd C:\Users\YourName\youtubetb_refactored
```

### 3. إنشاء بيئة افتراضية

```cmd
python -m venv venv
```

### 4. تفعيل البيئة الافتراضية

```cmd
venv\Scripts\activate
```

**ملاحظة:** يجب أن ترى `(venv)` في بداية السطر

### 5. تثبيت المكتبات المطلوبة

```cmd
pip install -r requirements.txt
```

**ملاحظة:** قد يستغرق هذا عدة دقائق

### 6. إعداد ملف البيئة (.env)

```cmd
# انسخ ملف المثال
copy .env.example .env

# افتح .env بمحرر نصوص (Notepad)
notepad .env
```

**أضف API Keys الخاصة بك:**

```env
# YouTube API
YT_API_KEY=your_youtube_api_key_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 7. تشغيل البرنامج

```cmd
python main.py
```

---

## 🔑 الحصول على API Keys

### YouTube Data API:

1. اذهب إلى: https://console.cloud.google.com/
2. أنشئ مشروع جديد
3. فعّل YouTube Data API v3
4. أنشئ Credentials (API Key)
5. انسخ المفتاح إلى `.env`

### Gemini AI:

1. اذهب إلى: https://makersuite.google.com/app/apikey
2. أنشئ API Key
3. انسخه إلى `.env`

### ElevenLabs:

1. اذهب إلى: https://elevenlabs.io/
2. سجّل حساب
3. اذهب إلى Profile → API Keys
4. انسخ المفتاح إلى `.env`

---

## 📖 الاستخدام

### القائمة التفاعلية:

```cmd
python main.py
```

سترى قائمة بالخيارات:
1. إنشاء ملخص كتاب جديد
2. استئناف مشروع سابق
3. معالجة فيديو مباشر
4. إنشاء Short
5. معالجة قناة كاملة
6. فحص APIs
7. خروج

### الاستخدام المباشر:

```cmd
# إنشاء ملخص كتاب
python src/presentation/cli/run_pipeline.py --book "Atomic Habits"

# معالجة فيديو مباشر
python src/presentation/cli/process_direct_video.py --url "https://youtube.com/watch?v=..."

# إنشاء Short
python src/presentation/cli/generate_short.py --book "Atomic Habits"
```

---

## 📁 هيكل المخرجات

```
output/
└── Atomic_Habits_2025-10-17_12-30/
    ├── input_name.txt          # اسم الكتاب
    ├── search_results.json     # نتائج البحث
    ├── selected_video.json     # الفيديو المختار
    ├── transcript.txt          # النص المستخرج
    ├── script.txt              # السكريبت المعالج
    ├── audio.mp3               # الصوت المولد
    ├── final_video.mp4         # الفيديو النهائي
    └── metadata.json           # معلومات الرفع
```

---

## ⚙️ الإعدادات المتقدمة

### تعديل إعدادات المعالجة:

افتح ملف `.env` وعدّل:

```env
# مدة الفيديو
MIN_VIDEO_DURATION=900          # 15 دقيقة
MAX_VIDEO_DURATION=7200         # 2 ساعة

# طول السكريبت
MAX_SCRIPT_LENGTH=950           # 950 كلمة

# جودة الفيديو
VIDEO_WIDTH=1920
VIDEO_HEIGHT=1080
VIDEO_FPS=30
```

---

## 🐛 حل المشاكل الشائعة

### المشكلة: `FFmpeg not found`

**الحل:**
1. تأكد من تثبيت FFmpeg
2. أضف مجلد `bin` إلى PATH
3. أعد تشغيل Command Prompt

### المشكلة: `ModuleNotFoundError`

**الحل:**
```cmd
# تأكد من تفعيل البيئة الافتراضية
venv\Scripts\activate

# أعد تثبيت المكتبات
pip install -r requirements.txt
```

### المشكلة: `API Key not found`

**الحل:**
1. تأكد من وجود ملف `.env`
2. تأكد من إضافة API Keys
3. تأكد من عدم وجود مسافات زائدة

### المشكلة: أخطاء في الترميز (Encoding)

**الحل:**
```cmd
# تأكد من استخدام UTF-8
chcp 65001
```

---

## 📞 الدعم

للمساعدة:
1. راجع `README.md` للتوثيق الكامل
2. راجع `final_report.md` للتفاصيل التقنية
3. تحقق من ملفات السجلات في `logs/`

---

## ✅ قائمة التحقق

- [ ] Python 3.10+ مثبت
- [ ] FFmpeg مثبت ومضاف إلى PATH
- [ ] البيئة الافتراضية منشأة ومفعلة
- [ ] المكتبات مثبتة (`pip install -r requirements.txt`)
- [ ] ملف `.env` موجود ويحتوي على API Keys
- [ ] تم اختبار `python main.py`

---

<div align="center">

**🎉 الآن أنت جاهز للبدء! 🎉**

**قم بتشغيل:** `python main.py`

</div>

