# 🚀 YouTube Sync - Quick Start

## التفعيل السريع (3 خطوات)

### 1️⃣ احصل على Channel ID

```bash
# طريقة 1: من YouTube Studio
1. افتح https://studio.youtube.com
2. Settings → Channel → Advanced settings
3. انسخ "Channel ID"

# طريقة 2: من أي فيديو على قناتك
1. افتح أي فيديو على قناتك
2. اضغط على اسم القناة
3. في URL، خذ الجزء بعد /channel/
   مثال: youtube.com/channel/UCxxx... → UCxxx...
```

### 2️⃣ أضف Channel ID للإعدادات

في `config/settings.json`:

```json
{
  "youtube_sync": {
    "enabled": true,
    "channel_id": "UCxxxxxxxxxxxxxxxxxx"  ← هنا!
  }
}
```

### 3️⃣ اختبار

```bash
# اختبار الـ sync يدوياً:
python -m src.infrastructure.adapters.database sync

# النتيجة المتوقعة:
# 🔄 SYNCING DATABASE FROM YOUTUBE CHANNEL
# ✅ Found 23 videos
# ✅ Added: Atomic Habits
# ✅ Added: Rich Dad Poor Dad
# ...
# ✅ DATABASE SYNCED SUCCESSFULLY! Total books: 20
```

---

## ✅ كل شي اشتغل؟

الآن الـ pipeline يشيك database.json تلقائياً:

```bash
python main.py
# إذا database.json فاضي → يسأل YouTube تلقائياً
# إذا مليان → يستخدمه مباشرة
```

---

## ❌ ما اشتغل؟

### مشكلة: "YouTube API key not found"

```bash
# تأكد إن الـ API key موجود:
ls secrets/api_key.txt  # Windows: dir secrets\api_key.txt

# أو في environment:
echo %GEMINI_API_KEY%  # Windows
echo $GEMINI_API_KEY   # Linux/Mac
```

### مشكلة: "Channel ID not configured"

```bash
# تأكد إن settings.json فيه channel_id
cat config/settings.json | grep channel_id  # Linux/Mac
type config\settings.json | findstr channel_id  # Windows
```

### مشكلة: "Could not extract book from title"

العناوين لازم تكون بهذا الشكل:
```
"[مقدمة] – [اسم الكتاب] | Book Summary"

✅ "How To FINALLY Break Free – Atomic Habits | Book Summary"
❌ "Amazing Book Review"  (ما في "–" و "| Book Summary")
```

---

## 🔄 تعطيل الـ Sync

في `config/settings.json`:

```json
{
  "youtube_sync": {
    "enabled": false  ← غيّرها لـ false
  }
}
```

---

## 📖 التوثيق الكامل

راجع: `docs/DUPLICATE_CHECK_SYSTEM.md`

---

**آخر تحديث:** 2025-10-20
