@echo off
chcp 65001 >nul
echo ============================================================
echo 🔑 Smart API Key Manager - YouTubeTB
echo ============================================================
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    echo 🔄 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the key manager
python add_api_key.py

echo.
echo ============================================================
echo Press any key to exit...
pause >nul
