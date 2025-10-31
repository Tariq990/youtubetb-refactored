# حل مشكلة Transcription Failures - YouTube IP Block

## 🚨 المشكلة
```
ERROR: Sign in to confirm you're not a bot
YouTube is blocking requests from your IP
```

---

## ✅ الحلول (بالترتيب)

### 1️⃣ **تحديث yt-dlp (الأهم!)**
```cmd
pip install --upgrade yt-dlp
```

**السبب**: yt-dlp يحتاج تحديث شهري لأن YouTube يغيّر آلية الحماية باستمرار.

**التحقق من النسخة**:
```cmd
yt-dlp --version
```
- ✅ يجب أن تكون `2024.10.22` أو أحدث
- ❌ إذا كانت `2024.08.xx` أو أقدم → حدّث فوراً

---

### 2️⃣ **تحديث الـ Cookies (مهم جداً!)**

**المشكلة**: cookies.txt انتهت صلاحيتها بعد استخدام مكثف

**الحل**:
1. افتح YouTube في متصفح **Chrome** أو **Edge**
2. سجّل دخول لحسابك
3. استخدم Extension لاستخراج Cookies:
   - [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - أو [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg)

4. حمّل ملف `cookies.txt` جديد واستبدل القديم:
   ```
   secrets/cookies.txt
   secrets/cookies_1.txt
   secrets/cookies_2.txt
   secrets/cookies_3.txt
   ```

**نصيحة**: حدّث الـ 4 ملفات كلهم بنفس الـ cookies الجديد.

---

### 3️⃣ **استخدم Proxies (للحالات الصعبة)**

إذا ما نفعت الحلول السابقة → استخدم Proxy لتغيير الـ IP.

**تعديل `transcribe.py`**:
```python
# في دالة run_yt_dlp_download_subs()، أضف:
cmd = [
    "yt-dlp",
    "--proxy", "socks5://127.0.0.1:1080",  # أو HTTP proxy
    "--cookies", str(cookie_path),
    # ... بقية الأوامر
]
```

**Proxy مجاني للتجربة**:
- استخدم VPN على جهازك (ProtonVPN مجاني)
- أو استخدم SOCKS5 proxy من https://www.proxy-list.download/SOCKS5

---

### 4️⃣ **إضافة Delay بين الكتب (تجنب IP Block)**

**تعديل `run_batch.py`**:
```python
# في نهاية process_books_batch()، زود الـ delay:
if idx < total_books:
    print("\n⏳ Waiting 30 seconds before next book...")
    time.sleep(30)  # بدل 5 → 30 ثانية
```

**الفائدة**: YouTube ما يشك إنك bot لما تبطئ الطلبات.

---

### 5️⃣ **استخدام YouTube Transcript API مع Cookies (خيار بديل)**

**المشكلة الحالية**: `youtube-transcript-api` ما تستخدم cookies بالكود الحالي.

**الحل المؤقت**: 
- استخدم VPN وغيّر الـ IP
- أو انتظر 1-2 ساعة لحد ما YouTube يرفع الحظر

---

## 🔧 الإجراء الموصى به (خطوة بخطوة)

### المرحلة الأولى: التحديث الفوري
```cmd
REM 1. حدّث yt-dlp
pip install --upgrade yt-dlp

REM 2. تحقق من النسخة
yt-dlp --version

REM 3. حدّث الـ cookies (يدوياً من Chrome)
```

### المرحلة الثانية: اختبار الحل
```cmd
REM جرّب نفس الفيديو المعطّل:
python -m src.infrastructure.adapters.transcribe --url "https://www.youtube.com/watch?v=tj5J6uDIH3s"
```

**النتيجة المتوقعة**:
- ✅ إذا اشتغل → المشكلة محلولة!
- ❌ إذا ما اشتغل → روح للخطوة 3 (Proxy)

### المرحلة الثالثة: استراتيجية طويلة المدى
1. **زود الـ delay** بين الكتب (30 ثانية بدل 5)
2. **استخدم VPN** لو تعالج أكثر من 10 كتب باليوم
3. **حدّث cookies** كل أسبوع

---

## 📊 متى تستخدم كل حل؟

| الحالة | الحل |
|--------|------|
| **أول مرة تشوف الخطأ** | حدّث yt-dlp + حدّث cookies |
| **الخطأ يتكرر باستمرار** | استخدم Proxy + زود الـ delay |
| **عالج 20+ كتاب بنفس اليوم** | حتمي تستخدم VPN |
| **كل الحلول فشلت** | انتظر ساعتين (YouTube ترفع الحظر تلقائياً) |

---

## 🧪 اختبار شامل

```cmd
REM اختبار 1: تحقق من yt-dlp
yt-dlp --version

REM اختبار 2: تحقق من cookies
dir secrets\cookies.txt

REM اختبار 3: جرّب فيديو بسيط
yt-dlp --cookies secrets\cookies.txt --list-subs "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

REM اختبار 4: شوف الـ User-Agent المستخدم
python cookies_helper.py
REM → Option 1 (View User-Agents)
```

---

## 🎯 الحل الأمثل (للاستخدام اليومي)

```python
# أضف هذا في run_batch.py (سطر 785):
if idx < total_books:
    # Dynamic delay based on success rate
    if results["failed"]:
        delay = 60  # إذا في فشل → زود الانتظار
    else:
        delay = 20  # Normal delay
    
    print(f"\n⏳ Waiting {delay} seconds before next book...")
    time.sleep(delay)
```

---

## ⚠️ تحذيرات مهمة

1. **لا تستخدم** حساب YouTube الرئيسي للـ cookies (استخدم حساب بديل)
2. **لا تعالج** أكثر من 15 كتاب بدون VPN
3. **حدّث yt-dlp** كل شهر (YouTube تغيّر الحماية باستمرار)
4. **لا تقلل** الـ delay عن 10 ثواني بين الكتب

---

## 📞 الدعم

إذا جربت كل الحلول وما زال الخطأ موجود:
1. انتظر 2-3 ساعات (الحظر مؤقت)
2. غيّر الـ IP (أعد تشغيل الراوتر أو استخدم VPN)
3. استخدم جهاز ثاني للتجربة

---

## 🚀 اقتراحات إضافية لتحسين الأداء

### 1️⃣ **استخدم Multiple YouTube Accounts**

**المشكلة**: حساب واحد يتحظر بسرعة عند الاستخدام المكثف.

**الحل**:
1. أنشئ 3-5 حسابات YouTube بديلة (Gmail مجاني)
2. استخرج cookies.txt من كل حساب
3. ضعها في:
   - `secrets/cookies.txt` (حساب 1)
   - `secrets/cookies_1.txt` (حساب 2)
   - `secrets/cookies_2.txt` (حساب 3)
   - `secrets/cookies_3.txt` (حساب 4)

**الفائدة**: 
- النظام يجرب الحسابات بالتتابع تلقائياً
- إذا حساب انحظر → ينتقل للثاني
- توزيع الحمل = أمان أكثر

---

### 2️⃣ **جدولة المعالجة (Scheduled Processing)**

**بدل** معالجة 20 كتاب دفعة واحدة:

```cmd
REM الطريقة القديمة (خطرة):
python main.py
REM → معالجة 20 كتاب بساعة واحدة → حظر IP

REM الطريقة الجديدة (آمنة):
REM صباح: 5 كتب
python -m src.presentation.cli.run_batch --file batch_morning.txt

REM ظهر: 5 كتب
python -m src.presentation.cli.run_batch --file batch_afternoon.txt

REM مساء: 5 كتب
python -m src.presentation.cli.run_batch --file batch_evening.txt
```

**الفائدة**:
- توزيع الحمل على 24 ساعة
- YouTube ما يشك بنشاط غير طبيعي
- راحة للـ IP والـ cookies

---

### 3️⃣ **استخدم Rotating Proxies (للمحترفين)**

**للاستخدام المكثف** (20+ كتاب يومياً):

```python
# ملف جديد: proxy_pool.py
PROXY_LIST = [
    "socks5://user:pass@proxy1.example.com:1080",
    "socks5://user:pass@proxy2.example.com:1080",
    "http://user:pass@proxy3.example.com:8080",
]

def get_random_proxy():
    return random.choice(PROXY_LIST)

# في transcribe.py، أضف:
proxy = get_random_proxy()
cmd = ["yt-dlp", "--proxy", proxy, "--cookies", cookies, ...]
```

**خدمات Proxy موصى بها**:
- **مجاني (محدود)**: ProtonVPN, TunnelBear
- **مدفوع (موثوق)**: Bright Data, Smartproxy, Oxylabs
- **التكلفة**: $10-50 شهرياً (يستحق لو تعالج 100+ فيديو)

---

### 4️⃣ **Monitor & Auto-Retry System (التطوير المستقبلي)**

**فكرة**: نظام ذكي يراقب معدل الفشل ويتكيف تلقائياً.

```python
# في run_batch.py، أضف:
class AdaptiveDelayManager:
    def __init__(self):
        self.failure_rate = 0.0
        self.base_delay = 30
    
    def calculate_delay(self, recent_failures):
        """يزيد الـ delay إذا زاد معدل الفشل"""
        if recent_failures >= 3:
            return self.base_delay * 3  # 90 ثانية
        elif recent_failures >= 2:
            return self.base_delay * 2  # 60 ثانية
        else:
            return self.base_delay       # 30 ثانية
    
    def should_pause(self, consecutive_failures):
        """توقف مؤقت إذا فشل 5 كتب متتالية"""
        if consecutive_failures >= 5:
            print("⚠️  Too many failures - pausing for 30 minutes")
            time.sleep(1800)  # 30 دقيقة
            return True
        return False
```

---

### 5️⃣ **Cache Downloaded Subtitles (تجنب Re-Download)**

**المشكلة**: إذا فشلت مرحلة Process → يعيد تحميل الترجمة من جديد.

**الحل**:
```python
# في transcribe.py، أضف:
def get_cached_subtitle(video_id):
    """تحقق من cache قبل التحميل"""
    cache_dir = REPO_ROOT / "cache" / "subtitles"
    cache_file = cache_dir / f"{video_id}.txt"
    
    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < 168:  # 7 أيام
            print(f"📦 Using cached subtitle (age: {age_hours:.1f}h)")
            return cache_file.read_text(encoding='utf-8')
    
    return None

# استخدمها قبل run_yt_dlp_download_subs()
cached = get_cached_subtitle(video_id)
if cached:
    return cached  # لا حاجة للتحميل!
```

**الفائدة**:
- يوفر API calls على YouTube
- يسرّع المعالجة (من 30 ثانية → 1 ثانية)
- يقلل فرص الحظر

---

### 6️⃣ **Health Check Before Batch Processing**

**قبل** بدء المعالجة، تحقق من صحة النظام:

```python
def preflight_health_check():
    """فحص شامل قبل المعالجة"""
    checks = {
        "yt-dlp version": check_ytdlp_version(),
        "cookies valid": check_cookies_validity(),
        "API keys": check_gemini_api(),
        "disk space": check_disk_space(),
        "network": check_internet_connection()
    }
    
    failures = [k for k, v in checks.items() if not v]
    
    if failures:
        print(f"❌ Pre-flight failed: {failures}")
        print("Fix these issues before processing")
        return False
    
    print("✅ All systems ready")
    return True

# في run_batch.py:
if not preflight_health_check():
    sys.exit(1)
```

---

### 7️⃣ **Detailed Logging & Analytics**

**أضف** تتبع شامل للأداء:

```python
# في run_batch.py:
import json
from datetime import datetime

def log_batch_analytics(results, duration):
    """حفظ إحصائيات المعالجة"""
    analytics = {
        "timestamp": datetime.now().isoformat(),
        "duration_minutes": duration / 60,
        "books_processed": len(results["success"]),
        "books_failed": len(results["failed"]),
        "success_rate": len(results["success"]) / len(results["total"]),
        "avg_time_per_book": duration / len(results["total"]),
        "ip_blocks": count_ip_block_errors(results),
        "cookies_rotations": count_cookies_rotations(results)
    }
    
    # حفظ في ملف
    log_file = REPO_ROOT / "analytics" / f"batch_{datetime.now():%Y%m%d_%H%M%S}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(analytics, f, indent=2)
    
    print(f"📊 Analytics saved: {log_file}")
```

**الفائدة**:
- تحليل الأنماط (متى يحصل الحظر؟)
- تحسين الـ delays بناءً على البيانات
- توقع المشاكل قبل حدوثها

---

### 8️⃣ **Smart Book Selection (أولويات ذكية)**

**بدل** معالجة الكتب بالترتيب، رتّبها حسب الأولوية:

```python
def prioritize_books(books):
    """رتب الكتب حسب الأولوية"""
    
    # 1. الكتب الشائعة (فيديوهات أكثر = فرص أكبر)
    # 2. الكتب القصيرة (فيديوهات 15-30 دقيقة)
    # 3. الكتب الحديثة (2020+)
    
    def score_book(book):
        score = 0
        
        # تحقق من شعبية الكتاب (من cache)
        if book in popularity_cache:
            score += popularity_cache[book] * 10
        
        # فضّل الكتب ذات الفيديوهات القصيرة
        if has_short_videos(book):
            score += 50
        
        return score
    
    return sorted(books, key=score_book, reverse=True)

# في run_batch.py:
books = read_books_from_file(file_path)
books = prioritize_books(books)  # رتّب قبل المعالجة
```

---

### 9️⃣ **Emergency Stop Mechanism**

**أضف** زر توقف طارئ:

```python
# في run_batch.py:
import signal

class EmergencyStop:
    def __init__(self):
        self.stop_requested = False
        signal.signal(signal.SIGINT, self.handle_stop)
    
    def handle_stop(self, sig, frame):
        print("\n🛑 Emergency stop requested!")
        print("Finishing current book and stopping...")
        self.stop_requested = True
    
    def should_stop(self):
        return self.stop_requested

# استخدمها:
emergency = EmergencyStop()

for book in books:
    if emergency.should_stop():
        print("🛑 Stopped by user")
        break
    
    process_book(book)
```

**الفائدة**:
- توقف نظيف (لا فقدان للبيانات)
- استئناف من نفس النقطة لاحقاً

---

### 🔟 **Notification System (إشعارات التقدم)**

**للمعالجة الطويلة** (20+ كتاب):

```python
# إشعارات Telegram (مثال):
import requests

def send_telegram_notification(message):
    """إرسال إشعار عبر Telegram Bot"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    
    try:
        requests.post(url, json=data, timeout=10)
    except Exception:
        pass  # فشل الإشعار لا يوقف المعالجة

# في run_batch.py:
send_telegram_notification(f"✅ Batch started: {len(books)} books")

# بعد كل 5 كتب:
if idx % 5 == 0:
    send_telegram_notification(f"📊 Progress: {idx}/{total} books")

# عند الانتهاء:
send_telegram_notification(f"🎉 Batch complete: {success}/{total} success")
```

---

## 📊 ملخص الأولويات

### ⚡ **نفّذها الآن** (Critical):
1. ✅ زيادة الـ delays (تم!) 
2. 🔄 تحديث yt-dlp
3. 🍪 تحديث الـ cookies
4. 📅 جدولة المعالجة (5 كتب/دفعة)

### 🎯 **نفّذها قريباً** (Important):
5. 👥 Multiple YouTube accounts
6. 💾 Cache subtitles
7. 🏥 Health check system
8. 📊 Analytics logging

### 🚀 **للمستقبل** (Optional):
9. 🌐 Rotating proxies
10. 🤖 Adaptive delays
11. 📱 Notifications
12. 🧠 Smart prioritization

---

## 🎁 Bonus: One-Liner Quick Fixes

```cmd
REM تحديث كل شي دفعة واحدة:
pip install --upgrade yt-dlp youtube-transcript-api google-generativeai && yt-dlp --version

REM اختبار سريع للنظام:
python -c "from src.infrastructure.adapters.transcribe import main; print('✅ System OK')"

REM تنظيف الـ cache (إذا امتلأ):
rmdir /s /q tmp\subs cache\subtitles

REM فحص حجم الـ runs (لتفريغ المساحة):
du -sh runs/*
```

---

**آخر تحديث**: 2025-10-31 (v2.3.2 - Enhanced delays + اقتراحات إضافية)
