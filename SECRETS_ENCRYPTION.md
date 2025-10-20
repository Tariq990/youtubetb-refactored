# نظام تشفير الأسرار - Secrets Encryption System

## 🔐 ما هو هذا النظام؟ / What is this?

**بالعربية:**
نظام لتشفير ملفات الـ API keys والـ tokens باستخدام password، بحيث يمكنك:
- رفع الملفات المشفرة بأمان على GitHub
- العمل من Google Colab بإدخال password واحد فقط
- عدم الحاجة لإدخال المفاتيح يدوياً في كل مرة

**English:**
A system to encrypt API keys and tokens files with a password, allowing you to:
- Safely commit encrypted files to GitHub
- Work from Google Colab with just one password
- Avoid manually entering keys every time

---

## 📋 متطلبات / Requirements

تثبيت المكتبة المطلوبة:
```bash
pip install cryptography
```

أو من `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 🚀 دليل الاستخدام السريع / Quick Start Guide

### 1️⃣ تشفير الملفات (مرة واحدة على جهازك) / Encrypt Files (Once on your machine)

```bash
python scripts/encrypt_secrets.py
```

**ماذا يحدث:**
- يقرأ ملفات من مجلد `secrets/`:
  - `api_key.txt` (Gemini API key)
  - `client_secret.json` (YouTube OAuth)
  - `cookies.txt` (YouTube cookies)
  - `token.json` (YouTube token)
- يطلب منك password (اختر password قوي واحفظه!)
- يشفر الملفات ويحفظها في `secrets_encrypted/`
- ✅ الآن يمكنك رفع `secrets_encrypted/` على GitHub بأمان!

---

### 2️⃣ فك التشفير (على Colab أو أي جهاز جديد) / Decrypt Files (On Colab or new machine)

```bash
python scripts/decrypt_secrets.py
```

**ماذا يحدث:**
- يقرأ الملفات المشفرة من `secrets_encrypted/`
- يطلب منك الـ password (نفس الـ password المستخدم في التشفير)
- يفك تشفير الملفات ويحفظها في `secrets/`
- ✅ الآن يمكنك تشغيل المشروع!

---

## 📝 سير العمل الكامل / Complete Workflow

### على جهازك المحلي / On Your Local Machine

1. **تحضير الملفات:**
   ```bash
   # تأكد أن ملفاتك في secrets/
   ls secrets/
   # يجب أن ترى: api_key.txt, client_secret.json, cookies.txt, token.json
   ```

2. **تشفير الملفات:**
   ```bash
   python scripts/encrypt_secrets.py
   ```
   - أدخل password قوي (مثلاً: `MyStr0ng!P@ssw0rd`)
   - احفظ الـ password في مكان آمن!

3. **رفع على GitHub:**
   ```bash
   git add secrets_encrypted/
   git add .gitignore  # تأكد أن secrets/ محمي
   git commit -m "Add encrypted secrets"
   git push
   ```

---

### على Google Colab

1. **استنساخ المشروع:**
   ```python
   !git clone https://github.com/YOUR_USERNAME/youtubetb-refactored.git
   %cd youtubetb-refactored
   ```

2. **تثبيت المتطلبات:**
   ```python
   !pip install -q cryptography
   # أو تثبيت الكل:
   !pip install -q -r requirements.txt
   ```

3. **فك تشفير الأسرار:**
   ```python
   !python scripts/decrypt_secrets.py
   # سيطلب منك الـ password - أدخله (نفس المستخدم في التشفير)
   ```

4. **تشغيل المشروع:**
   ```python
   !python main.py
   # اختر Option 7 للـ batch processing
   ```

---

## 🔒 الأمان / Security

### ✅ ما هو آمن / What's Safe

- **ملفات `secrets_encrypted/*.enc`**: آمنة للرفع على GitHub
  - مشفرة بـ AES-128 عبر Fernet
  - تحتاج password لفك التشفير
  - بدون password، الملفات غير قابلة للقراءة

### ⚠️ ما يجب حمايته / What to Protect

- **مجلد `secrets/`**: يحتوي المفاتيح الأصلية - **لا ترفعه على GitHub!**
- **الـ Password**: احفظه في مكان آمن (مدير كلمات سر مثلاً)
- **ملف `.env`** (إن وُجد): قد يحتوي على passwords

---

## 📂 هيكل الملفات / File Structure

```
youtubetb-refactored/
├── secrets/                    # ⛔ Local only (in .gitignore)
│   ├── api_key.txt            # Gemini API key
│   ├── client_secret.json     # YouTube OAuth client
│   ├── cookies.txt            # YouTube cookies
│   └── token.json             # YouTube access token
│
├── secrets_encrypted/          # ✅ Safe for GitHub
│   ├── api_key.txt.enc        # Encrypted API key
│   ├── client_secret.json.enc # Encrypted OAuth
│   ├── cookies.txt.enc        # Encrypted cookies
│   ├── token.json.enc         # Encrypted token
│   └── encryption_metadata.json  # Encryption info
│
└── scripts/
    ├── encrypt_secrets.py     # Encryption script
    └── decrypt_secrets.py     # Decryption script
```

---

## 🛠️ استكشاف الأخطاء / Troubleshooting

### ❌ خطأ: "Wrong password"

**المشكلة:** الـ password المدخل غير صحيح

**الحل:**
- تأكد من الـ password (حساس لحالة الأحرف!)
- إذا نسيت الـ password:
  - أعد التشفير من جهازك المحلي (حيث ملفات `secrets/` الأصلية)
  - استخدم password جديد

---

### ❌ خطأ: "secrets/ directory not found"

**المشكلة:** مجلد `secrets/` غير موجود

**الحل:**
```bash
mkdir secrets
# انسخ ملفاتك:
cp /path/to/your/api_key.txt secrets/
cp /path/to/your/client_secret.json secrets/
# إلخ...
```

---

### ❌ خطأ: "secrets_encrypted/ directory not found"

**المشكلة:** على Colab، المجلد غير موجود في الـ repo

**الحل:**
- تأكد أنك رفعت `secrets_encrypted/` على GitHub
- تحقق من الـ repo على GitHub - يجب أن ترى المجلد
- أعد استنساخ الـ repo

---

## 🔄 إعادة التشفير / Re-encrypting

إذا أردت تغيير الـ password أو تحديث الملفات:

```bash
# 1. حدّث ملفات secrets/ الأصلية على جهازك
# 2. أعد التشفير:
python scripts/encrypt_secrets.py

# 3. رفع التحديث:
git add secrets_encrypted/
git commit -m "Update encrypted secrets"
git push
```

---

## 📚 مثال كامل: من الصفر على Colab / Complete Colab Example

```python
# ═══════════════════════════════════════════════════════
# 1. استنساخ المشروع / Clone the project
# ═══════════════════════════════════════════════════════
!git clone https://github.com/YOUR_USERNAME/youtubetb-refactored.git
%cd youtubetb-refactored

# ═══════════════════════════════════════════════════════
# 2. تثبيت المتطلبات / Install requirements
# ═══════════════════════════════════════════════════════
!pip install -q cryptography
!pip install -q -r requirements.txt

# ═══════════════════════════════════════════════════════
# 3. فك تشفير الأسرار / Decrypt secrets
# ═══════════════════════════════════════════════════════
!python scripts/decrypt_secrets.py
# أدخل password عند المطالبة

# ═══════════════════════════════════════════════════════
# 4. تثبيت Playwright (للـ TTS)
# ═══════════════════════════════════════════════════════
!pip install -q playwright
!python -m playwright install chromium

# ═══════════════════════════════════════════════════════
# 5. تثبيت FFmpeg
# ═══════════════════════════════════════════════════════
!apt-get install -qq ffmpeg

# ═══════════════════════════════════════════════════════
# 6. تشغيل المشروع / Run the project
# ═══════════════════════════════════════════════════════
!python main.py
# اختر Option 7 للـ batch processing
```

---

## 💡 نصائح / Tips

1. **استخدم password قوي:**
   - على الأقل 12 حرف
   - مزيج من أحرف كبيرة وصغيرة وأرقام ورموز
   - مثال: `YouTubeTB!2025@Secure`

2. **احفظ الـ password:**
   - استخدم مدير كلمات سر (1Password, Bitwarden, LastPass)
   - أو احفظه في ملف محلي خارج الـ repo

3. **لا تشارك الـ password:**
   - الـ password يعطي وصول كامل للـ API keys
   - شاركه فقط مع أشخاص موثوقين

4. **راجع `.gitignore`:**
   - تأكد أن `secrets/` محمي
   - تأكد أن `*.enc` ليست في `.gitignore`

---

## 📞 الدعم / Support

إذا واجهت مشاكل:
1. راجع قسم "استكشاف الأخطاء" أعلاه
2. تأكد من تثبيت `cryptography`: `pip install cryptography`
3. تحقق من أن الملفات موجودة في الأماكن الصحيحة

---

## 🎯 الخلاصة / Summary

✅ **للمرة الأولى (على جهازك):**
```bash
python scripts/encrypt_secrets.py
git add secrets_encrypted/
git push
```

✅ **على Colab (في كل مرة):**
```bash
git clone <your-repo>
cd youtubetb-refactored
pip install cryptography
python scripts/decrypt_secrets.py  # أدخل password
python main.py  # شغّل المشروع!
```

🔐 **مبسط:** مرة واحدة تشفير على جهازك → كل مرة فك تشفير بـ password → تشغيل! 🚀
