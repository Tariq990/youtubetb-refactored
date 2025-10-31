# 🐍 Python Version Compatibility Fix

## ❌ Problem: Python 3.14+ Not Supported

**Error Message:**
```
RuntimeError: Cannot install on Python version 3.14.0; only versions >=3.10,<3.14 are supported.
```

**Root Cause:**  
The `numba` package (dependency of `openai-whisper`) does **not support Python 3.14+** yet.

---

## ✅ Solution: Downgrade to Python 3.10-3.13

### Option 1: Install Python 3.13 (Recommended)

1. **Uninstall Python 3.14:**
   - Open "Add or Remove Programs"
   - Search for "Python 3.14"
   - Uninstall

2. **Download Python 3.13:**
   - Visit: https://www.python.org/downloads/
   - Download: **Python 3.13.x** (latest 3.13 release)
   - **IMPORTANT:** Check "Add Python to PATH" during installation

3. **Verify Installation:**
   ```cmd
   python --version
   # Should show: Python 3.13.x
   ```

4. **Re-run Installation:**
   ```cmd
   cd C:\Users\Administrator\Desktop\youtubetb-refactored
   install_complete.bat
   ```

---

### Option 2: Use Python 3.12 (Alternative)

If Python 3.13 has issues, use 3.12:

1. Download: https://www.python.org/downloads/release/python-3120/
2. Install with "Add to PATH"
3. Verify: `python --version` → Should show 3.12.x
4. Run: `install_complete.bat`

---

### Option 3: Use `py` Launcher (If Multiple Versions Installed)

If you have multiple Python versions:

```cmd
# List installed versions
py --list

# Use specific version for venv
py -3.13 -m venv venv

# Activate and install
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔍 Verification Steps

After installing correct Python version:

```cmd
# 1. Check Python version
python --version
# Expected: Python 3.10.x, 3.11.x, 3.12.x, or 3.13.x

# 2. Check pip
python -m pip --version

# 3. Test numba installation (the problematic package)
python -m pip install numba
# Should succeed without errors

# 4. Clean old venv and reinstall
cd youtubetb-refactored
rmdir /s /q venv
install_complete.bat
```

---

## 📊 Supported Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.10.x | ✅ Supported | Stable |
| 3.11.x | ✅ Supported | Stable |
| 3.12.x | ✅ Supported | Stable |
| 3.13.x | ✅ Supported | **Recommended** |
| 3.14.x | ❌ NOT Supported | `numba` incompatible |
| 3.15+ | ❌ NOT Supported | Future releases |

---

## 🛠️ Quick Fix Commands

```cmd
# 1. Uninstall Python 3.14 (via Windows Settings)

# 2. Download and install Python 3.13
# From: https://www.python.org/downloads/

# 3. Verify
python --version

# 4. Clean workspace
cd C:\Users\Administrator\Desktop\youtubetb-refactored
rmdir /s /q venv

# 5. Reinstall
install_complete.bat
```

---

## 🔄 Alternative: Remove Whisper (If Not Needed)

If you don't need word-level subtitle alignment (optional feature):

1. Edit `requirements.txt`:
   ```diff
   - openai-whisper>=20231117
   ```

2. Install without whisper:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

**Note:** This removes word-level subtitle timing but keeps all core features.

---

## 📞 Support

- **Issue:** Python version incompatibility
- **Fix Time:** ~10 minutes (uninstall + reinstall)
- **Impact:** Blocks all installation until resolved

**Last Updated:** October 31, 2025
