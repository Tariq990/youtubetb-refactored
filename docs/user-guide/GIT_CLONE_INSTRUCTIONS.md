# تعليمات تنزيل المشروع على جهاز جديد

## الطريقة الأولى: تنزيل البرانش مباشرة

```bash
git clone -b project-review-and-improvements https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored
```

## الطريقة الثانية: تنزيل ثم التبديل للبرانش

```bash
git clone https://github.com/Tariq990/youtubetb-refactored.git
cd youtubetb-refactored
git checkout project-review-and-improvements
```

## خطوات ما بعد التنزيل

### 1. إنشاء بيئة افتراضية وتفعيلها

**على Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**على Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 3. إعداد ملف البيئة

```bash
copy .env.example .env
```

ثم قم بتعديل ملف `.env` وأضف المفاتيح الخاصة بك.

### 4. تشغيل الإعداد الأولي

**على Windows:**
```bash
setup.bat
```
أو
```bash
powershell -ExecutionPolicy Bypass -File setup_windows.ps1
```

### 5. تشغيل البرنامج

```bash
python main.py
```

## ملاحظات مهمة

- تأكد من تثبيت Python 3.8 أو أحدث
- تأكد من تثبيت FFmpeg وإضافته إلى PATH
- قم بإعداد ملف `secrets/cookies.txt` إذا كنت تحتاج للوصول إلى فيديوهات محمية
- راجع `docs/user-guide/WINDOWS_SETUP.md` لمزيد من التفاصيل
