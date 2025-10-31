# 📍 أماكن تخزين أنظمة الـ Fallback - دليل شامل

## 🗂️ نظرة عامة

جدول يوضح **أين تُخزّن** ملفات كل نظام fallback بالترتيب:

---

## 1️⃣ Gemini API (5 مواقع)

| الأولوية | الموقع الكامل | نوع الملف | الصيغة |
|---------|---------------|-----------|--------|
| **1** | `secrets/api_keys.txt` | نص عادي | سطر واحد أو أكثر |
| **2** | `secrets/api_key.txt` | نص عادي | سطر واحد |
| **3** | `api_key.txt` | نص عادي | سطر واحد (جذر المشروع) |
| **4** | `GEMINI_API_KEY` | متغير بيئة | `export GEMINI_API_KEY=...` |
| **5** | `secrets/.env` | ملف .env | `GEMINI_API_KEY=...` |

### مثال ملف `secrets/api_keys.txt`:
```
AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
AIzaSyD9876543210zyxwvutsrqponmlkjihgfedcba
AIzaSyD5555555555aaaaaaaaabbbbbbbbbcccccccc
```

### مثال ملف `secrets/.env`:
```env
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz
YT_API_KEY=AIzaSyD9876543210zyxwvutsrqponmlkjihgfedcba
PEXELS_API_KEY=563492ad6f917000010000017a2c79b55b394f18
```

---

## 2️⃣ YouTube Data API (5 مواقع)

| الأولوية | الموقع الكامل | نوع الملف | الصيغة |
|---------|---------------|-----------|--------|
| **1** | `YT_API_KEY` | متغير بيئة | `export YT_API_KEY=...` |
| **2** | `secrets/api_keys.txt` | نص عادي | سطر واحد أو أكثر |
| **3** | `secrets/api_key.txt` | نص عادي | سطر واحد |
| **4** | `api_key.txt` | نص عادي | سطر واحد (جذر المشروع) |
| **5** | `secrets/.env` | ملف .env | `YT_API_KEY=...` |

### مثال ملف `secrets/api_keys.txt` (متعدد المفاتيح):
```
AIzaSyD1111111111111111111111111111111111111  # YouTube Key 1
AIzaSyD2222222222222222222222222222222222222  # YouTube Key 2
AIzaSyD3333333333333333333333333333333333333  # YouTube Key 3
```

---

## 3️⃣ Cookies (5 مواقع)

| الأولوية | الموقع الكامل | نوع الملف | الصيغة |
|---------|---------------|-----------|--------|
| **1** | `secrets/cookies.txt` | Netscape format | HTTP Cookie File |
| **2** | `secrets/cookies_1.txt` | Netscape format | HTTP Cookie File |
| **3** | `secrets/cookies_2.txt` | Netscape format | HTTP Cookie File |
| **4** | `secrets/cookies_3.txt` | Netscape format | HTTP Cookie File |
| **5** | `cookies.txt` | Netscape format | HTTP Cookie File (جذر) |

### مثال ملف `secrets/cookies.txt`:
```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1735689600	VISITOR_INFO1_LIVE	abcdefghijk
.youtube.com	TRUE	/	TRUE	1735689600	CONSENT	YES+cb.20210328-17-p0
.youtube.com	TRUE	/	FALSE	1735689600	PREF	f6=40000000
.youtube.com	TRUE	/	TRUE	1735689600	SID	g.a000abcdefg...
```

### استخدام متعدد الحسابات:
- `secrets/cookies.txt` ← حساب أساسي (يومي)
- `secrets/cookies_1.txt` ← حساب احتياطي 1
- `secrets/cookies_2.txt` ← حساب بديل 2
- `secrets/cookies_3.txt` ← حساب طوارئ 3

---

## 4️⃣ Pexels API (6 مواقع) 🆕

| الأولوية | الموقع الكامل | نوع الملف | الصيغة |
|---------|---------------|-----------|--------|
| **1** | `PEXELS_API_KEY` | متغير بيئة | `export PEXELS_API_KEY=...` |
| **2** | `secrets/.env` | ملف .env | `PEXELS_API_KEY=...` |
| **3** | `secrets/pexels_key.txt` | نص عادي | سطر واحد (**موصى به**) |
| **4** | `secrets/api_keys.txt` | نص عادي | سطر واحد أو أكثر |
| **5** | `secrets/api_key.txt` | نص عادي | سطر واحد |
| **6** | `.env` | ملف .env | `PEXELS_API_KEY=...` (جذر) |

### مثال ملف `secrets/pexels_key.txt` (موصى به):
```
563492ad6f917000010000017a2c79b55b394f1899d14ac1bfe1
```

### مثال ملف `secrets/.env` (الكل في ملف واحد):
```env
# Gemini API
GEMINI_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz

# YouTube Data API
YT_API_KEY=AIzaSyD9876543210zyxwvutsrqponmlkjihgfedcba

# Pexels API
PEXELS_API_KEY=563492ad6f917000010000017a2c79b55b394f1899d14ac1bfe1

# OAuth (لا تضعها هنا - تُحفظ في ملفات منفصلة)
# client_secret.json و token.json
```

---

## 🗺️ هيكل المجلد `secrets/`

```
youtubetb_refactored/
├── secrets/                        ← المجلد الرئيسي (.gitignore محمي)
│   ├── .env                        ← ملف .env الأساسي (جميع الـ API keys)
│   │
│   ├── api_key.txt                 ← API key قديم (Gemini/YouTube مشترك)
│   ├── api_keys.txt                ← API keys متعددة (سطر لكل key)
│   │
│   ├── pexels_key.txt              ← Pexels API key مخصص (موصى به)
│   │
│   ├── cookies.txt                 ← Cookies أساسي (حساب 1)
│   ├── cookies_1.txt               ← Cookies احتياطي 1 (حساب 2)
│   ├── cookies_2.txt               ← Cookies احتياطي 2 (حساب 3)
│   ├── cookies_3.txt               ← Cookies احتياطي 3 (حساب 4)
│   │
│   ├── client_secret.json          ← OAuth credentials (YouTube Upload)
│   └── token.json                  ← OAuth token (auto-refresh)
│
├── .env                            ← ملف .env في الجذر (fallback نهائي)
├── cookies.txt                     ← Cookies في الجذر (fallback نهائي)
└── api_key.txt                     ← API key في الجذر (fallback نهائي)
```

---

## 📋 جدول شامل - كل الأنظمة

| النظام | الأولوية 1 | الأولوية 2 | الأولوية 3 | الأولوية 4 | الأولوية 5 | الأولوية 6 |
|--------|------------|------------|------------|------------|------------|------------|
| **Gemini** | `secrets/api_keys.txt` | `secrets/api_key.txt` | `api_key.txt` | `GEMINI_API_KEY` (env) | `secrets/.env` | - |
| **YouTube** | `YT_API_KEY` (env) | `secrets/api_keys.txt` | `secrets/api_key.txt` | `api_key.txt` | `secrets/.env` | - |
| **Cookies** | `secrets/cookies.txt` | `secrets/cookies_1.txt` | `secrets/cookies_2.txt` | `secrets/cookies_3.txt` | `cookies.txt` | - |
| **Pexels** | `PEXELS_API_KEY` (env) | `secrets/.env` | `secrets/pexels_key.txt` | `secrets/api_keys.txt` | `secrets/api_key.txt` | `.env` |

---

## 🔐 الأمان والحماية

### ملف `.gitignore` يحمي:
```gitignore
# Secrets folder (الحماية الرئيسية)
secrets/

# Individual files
*.env
cookies*.txt
api_key*.txt
pexels_key*.txt
client_secret.json
token.json

# Encrypted secrets (مسموح فقط للنسخ المشفرة)
!secrets_encrypted/
```

### ⚠️ تحذير هام:
```
لا تنشر هذه الملفات على GitHub أبداً!
- API Keys حساسة
- Cookies تحتوي على معلومات تسجيل دخول
- OAuth tokens تعطي وصول كامل لحسابك
```

---

## 🛠️ الإعداد السريع

### الطريقة 1: ملف واحد لكل شيء (`secrets/.env`)
```bash
# أنشئ ملف: secrets/.env
# أضف كل الـ API keys:

GEMINI_API_KEY=AIzaSyD1234567890...
YT_API_KEY=AIzaSyD9876543210...
PEXELS_API_KEY=563492ad6f91700001...
```

### الطريقة 2: ملفات منفصلة (أفضل للتنظيم)
```bash
# Gemini
echo "AIzaSyD1234..." > secrets/api_key.txt

# YouTube (متعدد)
cat > secrets/api_keys.txt << EOF
AIzaSyD1111111111111111111111111111111111111
AIzaSyD2222222222222222222222222222222222222
AIzaSyD3333333333333333333333333333333333333
EOF

# Pexels (مخصص)
echo "563492ad6f91700001..." > secrets/pexels_key.txt

# Cookies (من المتصفح)
# تصدير باستخدام إضافة "Get cookies.txt LOCALLY"
# حفظ في: secrets/cookies.txt
```

---

## 🧪 التحقق من الإعداد

### اختبار كل الأنظمة:
```bash
# اختبار شامل
python main.py
# Option 0: System Check

# اختبار Cookies فقط
python scripts\test_cookies_fallback.py

# اختبار Pexels فقط
# سيتم فحصه تلقائياً في System Check
```

### النتيجة المتوقعة:
```
✅ Gemini API: Working (api_keys.txt)
✅ YouTube API: Working (key 1/3)
✅ Cookies: Found 2 valid files (cookies.txt + cookies_1.txt)
✅ Pexels API: Working (pexels_key.txt)
```

---

## 📊 مثال عملي - إعداد كامل

### البنية الموصى بها:
```
secrets/
├── .env                          ← كل المتغيرات
│   ├── GEMINI_API_KEY=...
│   ├── YT_API_KEY=...
│   └── PEXELS_API_KEY=...
│
├── api_keys.txt                  ← YouTube keys احتياطية (3 keys)
│   ├── AIzaSyD111...
│   ├── AIzaSyD222...
│   └── AIzaSyD333...
│
├── pexels_key.txt                ← Pexels مخصص
│   └── 563492ad6f9170...
│
├── cookies.txt                   ← حساب يوتيوب رئيسي
├── cookies_1.txt                 ← حساب احتياطي 1
├── cookies_2.txt                 ← حساب احتياطي 2
│
├── client_secret.json            ← OAuth credentials
└── token.json                    ← OAuth token (يتم تحديثه تلقائياً)
```

---

## 🎯 الخلاصة

### أين تُخزّن؟

| النظام | الموقع الأساسي الموصى به | ملفات احتياطية |
|--------|---------------------------|-----------------|
| **Gemini** | `secrets/api_keys.txt` | `secrets/api_key.txt`, `.env` |
| **YouTube** | `secrets/api_keys.txt` (متعدد) | environment variable, `.env` |
| **Cookies** | `secrets/cookies.txt` | `cookies_1.txt`, `cookies_2.txt`, `cookies_3.txt` |
| **Pexels** | `secrets/pexels_key.txt` | `secrets/.env`, environment variable |

### الطريقة الأبسط (للمبتدئين):
```bash
# ضع كل شيء في: secrets/.env
GEMINI_API_KEY=...
YT_API_KEY=...
PEXELS_API_KEY=...

# وضع cookies في: secrets/cookies.txt
```

### الطريقة الأفضل (للإنتاج):
```bash
# ملفات منفصلة للتنظيم:
secrets/api_keys.txt       ← YouTube (متعدد)
secrets/pexels_key.txt     ← Pexels (مخصص)
secrets/cookies.txt        ← Cookies (رئيسي)
secrets/cookies_1.txt      ← Cookies (احتياطي)
secrets/.env               ← بقية المتغيرات
```

---

**الإصدار**: v2.3.0  
**التاريخ**: 2025-10-30  
**جميع الأنظمة**: محمية في `.gitignore` ✅
