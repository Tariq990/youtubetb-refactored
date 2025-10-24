@echo off
chcp 65001 >nul
title Encrypt Secrets

echo.
echo ========================================
echo   تشفير المفاتيح السرية
echo   Encrypt Secrets
echo ========================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ البيئة الافتراضية غير موجودة!
    echo ❌ Virtual environment not found!
    echo.
    echo Please run install_complete.bat first
    pause
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate.bat

:: Check if secrets folder exists
if not exist "secrets" (
    echo ❌ مجلد secrets غير موجود!
    echo ❌ secrets/ folder not found!
    echo.
    echo Please create secrets/ folder with your API keys first.
    pause
    exit /b 1
)

:: Show files to be encrypted
echo 📁 الملفات التي سيتم تشفيرها:
echo 📁 Files to be encrypted:
echo.
dir /b secrets\*.txt secrets\*.json 2>nul

echo.
echo ⚠️  تأكد من:
echo ⚠️  Make sure:
echo    1. جميع ملفاتك في secrets/ محدثة
echo       All your files in secrets/ are updated
echo    2. احفظ كلمة المرور في مكان آمن
echo       Save the password in a safe place
echo    3. لا تنسى كلمة المرور!
echo       Don't forget the password!
echo.

pause

:: Run encryption
python scripts\encrypt_secrets.py

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ تم التشفير بنجاح!
    echo   ✅ Encryption Successful!
    echo ========================================
    echo.
    echo الخطوات التالية:
    echo Next steps:
    echo.
    echo 1. تحقق من وجود الملفات في secrets_encrypted/
    echo    Verify files exist in secrets_encrypted/
    echo.
    echo 2. ارفع على GitHub:
    echo    Push to GitHub:
    echo    git add secrets_encrypted/
    echo    git commit -m "Update encrypted secrets"
    echo    git push
    echo.
    echo 3. لا ترفع مجلد secrets/ الأصلي!
    echo    Don't push original secrets/ folder!
    echo.
) else (
    echo.
    echo ❌ فشل التشفير!
    echo ❌ Encryption failed!
    echo.
)

pause
