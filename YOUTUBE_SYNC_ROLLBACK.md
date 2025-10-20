# 🔙 ROLLBACK INSTRUCTIONS

## إذا صار خلل وتبغى ترجع للطريقة القديمة (بسرعة!)

---

## ⚡ الطريقة السريعة (5 ثوانٍ)

### في `config/settings.json`:

```json
{
  "youtube_sync": {
    "enabled": false  ← غيّر true إلى false
  }
}
```

**✅ خلاص! النظام القديم رجع يشتغل**

---

## 🔄 الطريقة الكاملة (إذا تبغى تحذف الكود)

### 1. Rollback Git:

```bash
# شوف آخر commits
git log --oneline -5

# ارجع قبل التغيير
git revert HEAD

# أو استخدم commit hash محدد:
git reset --hard <commit-before-youtube-sync>
```

### 2. حذف الكود يدوياً:

**في `database.py`:**
- احذف السطور 393-670 (كل شي بعد تعليق "YouTube Channel Sync")

**في `settings.json`:**
- احذف:
```json
"youtube_sync": {
  "enabled": true,
  "channel_id": "...",
  "cache_duration_hours": 1
}
```

### 3. حذف الملفات الجديدة:

```bash
rm docs/DUPLICATE_CHECK_SYSTEM.md
rm YOUTUBE_SYNC_QUICKSTART.md
rm YOUTUBE_SYNC_CHANGELOG.md
rm YOUTUBE_SYNC_ROLLBACK.md  # هذا الملف نفسه
```

---

## 📋 بديل: استخدام Git Tracking

إذا تبغى حل أفضل من Manual:

```bash
# 1. عطّل YouTube sync (الطريقة السريعة أعلاه)

# 2. افتح .gitignore واحذف السطر:
#    database.json

# 3. تتبع database.json في Git:
git add src/database.json
git commit -m "Track database.json"
git push

# الآن database.json يتزامن عبر Git
```

---

## ✅ كيف تتأكد إن الـ rollback نجح؟

```bash
# اختبار:
python main.py

# إذا ما طلع أي شي متعلق بـ "SYNCING DATABASE FROM YOUTUBE"
# → الـ rollback نجح! ✅
```

---

## 📞 إذا ما زال في مشكلة:

1. تأكد إن `enabled: false` في settings.json
2. امسح `database.json` وخليه فاضي: `echo {} > src/database.json`
3. شغّل pipeline من جديد

---

**ملاحظة:** هذا الـ rollback **ما يحذف** البيانات في `database.json` - بس يوقف الـ sync من YouTube.

---

**Last resort:** إذا كل شي فشل، انسخ backup من `database.py` قبل التعديلات!
