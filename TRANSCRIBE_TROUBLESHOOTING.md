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
