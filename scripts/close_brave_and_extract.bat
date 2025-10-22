@echo off
echo ====================================================================
echo   اغلاق Brave واستخراج الكوكيز
echo ====================================================================
echo.

echo 1. اغلاق جميع عمليات Brave...
taskkill /F /IM brave.exe 2>nul
if %errorlevel% equ 0 (
    echo    تم اغلاق Brave بنجاح
) else (
    echo    Brave غير مفتوح او تم اغلاقه مسبقا
)

echo.
echo 2. الانتظار ثانيتين...
timeout /t 2 /nobreak >nul

echo.
echo 3. استخراج الكوكيز...
python extract_cookies.py

echo.
pause
