# YouTubeTB - YouTube Book Summary Generator

<div align="center">

**نظام احترافي لإنشاء ملخصات كتب فيديو ورفعها على يوتيوب**

[![Python](https://img.shields.io/badge/Python-Any_Version-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0.0-orange.svg)](CHANGELOG.md)

> ⚡ **NEW:** One-command installer with smart auto-fixes! Run `SETUP_ALL.bat` and you're done! See [ONE_COMMAND_INSTALL.md](docs/ONE_COMMAND_INSTALL.md)

</div>

---

## 📖 نظرة عامة

**YouTubeTB** هو نظام متكامل لإنشاء ملخصات كتب بشكل تلقائي على هيئة فيديوهات يوتيوب احترافية. يستخدم النظام الذكاء الاصطناعي لمعالجة النصوص وتحويلها إلى محتوى صوتي ومرئي جذاب.

### الميزات الرئيسية:

- ✅ **بحث ذكي** - البحث عن أفضل ملخصات الكتب على يوتيوب
- ✅ **استخراج نصوص** - استخراج النصوص من الفيديوهات تلقائياً
- ✅ **معالجة بالذكاء الاصطناعي** - إعادة صياغة وتحسين المحتوى باستخدام Gemini AI
- ✅ **تحويل نص لصوت** - توليد صوت احترافي باستخدام ElevenLabs
- ✅ **إنتاج فيديو** - إنشاء فيديو كامل مع تأثيرات بصرية
- ✅ **رفع تلقائي** - رفع الفيديو على يوتيوب مع metadata كامل
- ✅ **إنشاء Shorts** - توليد فيديوهات قصيرة من المحتوى الطويل
- 🆕 **معالجة دفعات ذكية** - معالجة عدة كتب تلقائياً مع تجنب التكرار وإكمال الناقص

---

## 🚀 البدء السريع (Windows)

### ⚡ الطريقة الأسهل - أمر واحد فقط:

```cmd
# 1. نزّل المشروع
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored

# 2. شغّل التثبيت الذكي (يكتشف المشاكل ويصلحها تلقائياً)
SETUP_ALL.bat
```

**هذا كل شيء!** السكريبت يتعامل مع كل شيء:
- ✅ يثبت Python (أي إصدار - بدون قيود)
- ✅ يثبت FFmpeg تلقائياً
- ✅ ينشئ بيئة افتراضية نظيفة
- ✅ يثبت جميع المكتبات (حتى لو Python 3.14+)
- ✅ يكتشف ويصلح المشاكل تلقائياً
- ✅ يفك تشفير الـ secrets
- ✅ يتحقق من كل شيء

📖 **دليل مفصّل:** [`docs/ONE_COMMAND_INSTALL.md`](docs/ONE_COMMAND_INSTALL.md)

---

### الطريقة البديلة - ملفات BAT منفصلة:

```cmd
# 1. فك ضغط المشروع
# 2. افتح Command Prompt في مجلد المشروع
# 3. شغّل setup.bat
setup.bat

# 4. عدّل ملف .env وأضف API keys
notepad .env

# 5. شغّل البرنامج
run.bat
```

### الطريقة اليدوية:

```cmd
# 1. إنشاء بيئة افتراضية
python -m venv venv

# 2. تفعيل البيئة
venv\Scripts\activate

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. إعداد البيئة
copy .env.example .env
notepad .env

# 5. تشغيل البرنامج
python main.py
```

**📚 للتفاصيل الكاملة، راجع [QUICK_START.md](QUICK_START.md)**

---

## 🔑 المتطلبات

### البرامج الأساسية:

1. **Python 3.10+**
   - تحميل: https://www.python.org/downloads/
   - ✅ فعّل "Add Python to PATH"

2. **FFmpeg**
   - تحميل: https://www.gyan.dev/ffmpeg/builds/
   - أضف `bin` إلى PATH

### API Keys المطلوبة:

1. **YouTube Data API v3**
   - الحصول عليه: https://console.cloud.google.com/

2. **Google Gemini AI**
   - الحصول عليه: https://makersuite.google.com/app/apikey

3. **ElevenLabs TTS**
   - الحصول عليه: https://elevenlabs.io/

4. **YouTube OAuth** (للرفع)
   - ملف `client_secrets.json` من Google Cloud Console

### 🍪 Cookies Setup (مطلوب):

**لماذا Cookies؟**
- لتحميل فيديوهات محظورة بالعمر (age-restricted)
- لجلب أغلفة الكتب من Amazon

**الطريقة:**
1. ثبّت Extension: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. سجّل دخول على YouTube و Amazon
3. صدّر cookies من كل موقع
4. ادمج الملفين في `secrets/cookies.txt`

**📖 دليل مفصّل: [docs/COOKIES_SETUP.md](docs/COOKIES_SETUP.md)**

---

## 📖 الاستخدام

### القائمة التفاعلية:

```cmd
python main.py
```

### الأوامر المباشرة:

```cmd
# إنشاء ملخص كتاب كامل
python src/presentation/cli/run_pipeline.py --book "Atomic Habits"

# معالجة فيديو موجود
python src/presentation/cli/process_direct_video.py --url "https://youtube.com/watch?v=..."

# إنشاء Short
python src/presentation/cli/generate_short.py --book "Atomic Habits"

# معالجة قناة كاملة
python src/presentation/cli/process_channel.py --channel-id "UCxxxxx"

# فحص APIs
python src/presentation/cli/check_apis.py
```

### 🆕 المعالجة الدفعية الذكية (Intelligent Batch Processing):

```cmd
# معالجة عدة كتب من ملف نصي
python -m src.presentation.cli.run_batch

# استخدام ملف مخصص
python -m src.presentation.cli.run_batch --file my_books.txt

# إعادة معالجة الكتب المكتملة
python -m src.presentation.cli.run_batch --no-skip

# تحديد خصوصية يوتيوب
python -m src.presentation.cli.run_batch --privacy unlisted
```

**الميزات:**
- ✅ يتجنب تلقائياً الكتب المكتملة (حالة: `done`)
- ♻️ يكمل الكتب الناقصة من آخر مرحلة (حالة: `processing`)
- 🚀 يعالج الكتب الجديدة من الصفر
- 📊 يعرض خطة ما قبل التنفيذ (Pre-flight Plan)
- 📈 يعرض ملخص نهائي شامل مع الإحصائيات

**📚 دليل كامل:** [BATCH_QUICK_START.md](BATCH_QUICK_START.md) | [docs/user-guide/BATCH_PROCESSING.md](docs/user-guide/BATCH_PROCESSING.md)

---

## 🏗️ البنية المعمارية

المشروع مبني على **Clean Architecture** مع **Hexagonal Architecture**:

```
src/
├── core/                    # Domain Layer (منطق العمل الأساسي)
│   ├── domain/
│   │   ├── entities/        # الكيانات الأساسية
│   │   ├── value_objects/   # القيم المركبة
│   │   ├── services/        # خدمات النطاق
│   │   └── exceptions/      # الاستثناءات المخصصة
│   └── ports/               # الواجهات البرمجية
│
├── application/             # Application Layer (حالات الاستخدام)
│   ├── use_cases/           # Use Cases
│   └── dtos/                # Data Transfer Objects
│
├── infrastructure/          # Infrastructure Layer (التفاصيل التقنية)
│   ├── adapters/            # المحولات (APIs, Database)
│   │   ├── youtube/         # YouTube API
│   │   ├── ai/              # Gemini AI
│   │   ├── media/           # Media Processing
│   │   └── storage/         # File Storage
│   ├── config/              # الإعدادات
│   └── repositories/        # قواعد البيانات
│
├── presentation/            # Presentation Layer (الواجهات)
│   ├── cli/                 # Command Line Interface
│   └── api/                 # REST API (مستقبلاً)
│
└── shared/                  # Shared Services (خدمات مشتركة)
    ├── logging/             # نظام التسجيل
    ├── errors/              # معالجة الأخطاء
    ├── monitoring/          # المراقبة
    └── output/              # إدارة المخرجات
```

---

## 🎯 الأنظمة الذكية

### 1. نظام الاستثناءات الذكي

```python
from src.core.domain.exceptions import VideoSearchException

try:
    videos = search_videos(query)
except VideoSearchException as e:
    print(f"Error: {e.message}")
    print(f"Recovery: {e.recovery_strategy}")
```

### 2. نظام التسجيل الموحد

```python
from src.shared.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing started", book="Atomic Habits")
logger.error("Processing failed", error=str(e))
```

### 3. معالج الأخطاء المركزي

```python
from src.shared.errors import get_error_handler

error_handler = get_error_handler()

@error_handler.with_error_handling("search_videos", max_retries=3)
def search_videos(query: str):
    # Your code here
    pass
```

### 4. نظام المراقبة

```python
from src.shared.monitoring import get_metrics_tracker

tracker = get_metrics_tracker()

with tracker.track_operation("search_videos"):
    videos = search_videos(query)

metrics = tracker.get_summary()
```

### 5. نظام المخرجات

```python
from src.shared.output import get_output_manager

output = get_output_manager()

output.print_header("Starting Pipeline")
output.print_success("Found 10 videos!")

with output.progress("Processing", total=10) as progress:
    for i in range(10):
        process_item(i)
        progress.update(1)
```

---

## 📁 المخرجات

```
output/
└── Atomic_Habits_2025-10-17_12-30/
    ├── input_name.txt          # اسم الكتاب المدخل
    ├── search_results.json     # نتائج البحث
    ├── selected_video.json     # معلومات الفيديو المختار
    ├── transcript.txt          # النص المستخرج
    ├── script.txt              # السكريبت المعالج
    ├── audio.mp3               # الصوت المولد
    ├── video.mp4               # الفيديو بدون صوت
    ├── final_video.mp4         # الفيديو النهائي
    ├── thumbnail.png           # الصورة المصغرة
    ├── metadata.json           # معلومات الرفع
    └── logs/                   # سجلات العملية
```

---

## ⚙️ الإعدادات

### ملف .env:

```env
# YouTube API
YT_API_KEY=your_youtube_api_key
YT_CLIENT_SECRETS_FILE=client_secrets.json

# Gemini AI
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB

# Processing
MAX_SCRIPT_LENGTH=950
MIN_VIDEO_DURATION=900
MAX_VIDEO_DURATION=7200

# Video Settings
VIDEO_WIDTH=1920
VIDEO_HEIGHT=1080
VIDEO_FPS=30
```

---

## 🐛 حل المشاكل

### FFmpeg not found

```cmd
# تأكد من تثبيت FFmpeg وإضافته إلى PATH
ffmpeg -version
```

### ModuleNotFoundError

```cmd
# تأكد من تفعيل البيئة الافتراضية
venv\Scripts\activate

# أعد تثبيت المكتبات
pip install -r requirements.txt
```

### API Key errors

```cmd
# تأكد من وجود ملف .env
# تأكد من صحة API keys
# تأكد من عدم وجود مسافات زائدة
```

### أخطاء الترميز (Arabic)

```cmd
# استخدم UTF-8
chcp 65001
```

---

## 📚 التوثيق

- **[QUICK_START.md](QUICK_START.md)** - دليل البدء السريع
- **[CHANGELOG.md](CHANGELOG.md)** - سجل التغييرات
- **[final_report.md](../youtubetb_analysis/final_report.md)** - التقرير الفني الشامل
- **[delivery_summary.md](../youtubetb_analysis/delivery_summary.md)** - ملخص التسليم

---

## 🤝 المساهمة

المشروع مفتوح المصدر ونرحب بالمساهمات:

1. Fork المشروع
2. أنشئ branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. افتح Pull Request

---

## 📄 الترخيص

هذا المشروع مرخص تحت **MIT License** - راجع ملف [LICENSE](LICENSE) للتفاصيل.

---

## 🙏 شكر وتقدير

- **YouTube Data API** - للبحث والبيانات
- **Google Gemini** - للذكاء الاصطناعي
- **ElevenLabs** - لتحويل النص لصوت
- **MoviePy** - لمعالجة الفيديو
- **Rich** - لواجهة CLI جميلة

---

## 📞 الدعم

- 📧 البريد الإلكتروني: support@youtubetb.com
- 🐛 الإبلاغ عن مشاكل: [GitHub Issues](https://github.com/Tariq990/youtubetb/issues)
- 📖 التوثيق: [Wiki](https://github.com/Tariq990/youtubetb/wiki)

---

<div align="center">

**صُنع بـ ❤️ بواسطة Manus AI**

**النسخة 2.0.0** - إعادة هيكلة كاملة واحترافية

[⬆ العودة للأعلى](#youtubetb---youtube-book-summary-generator)

</div>

