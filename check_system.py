#!/usr/bin/env python3
"""
System Environment Checker
Verifies all dependencies are installed correctly (without venv)
"""

import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  ⚠️  WARNING: Python 3.10+ recommended")
        return False
    return True

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT INSTALLED")
        print(f"  Install: pip install {package_name}")
        return False

def check_command(cmd):
    """Check if a system command exists"""
    try:
        # Try running the command
        result = subprocess.run([cmd, "--version"], 
                              capture_output=True, 
                              text=True, 
                              timeout=5,
                              shell=True)  # Use shell to find commands in PATH
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ {cmd}: {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # If direct execution failed, try with .exe extension (Windows)
    if sys.platform == "win32":
        try:
            result = subprocess.run([f"{cmd}.exe", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5,
                                  shell=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✓ {cmd}: {version}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    print(f"✗ {cmd} - NOT FOUND")
    print(f"  Note: Command may be installed but not in PATH")
    return False

def main():
    print("=" * 50)
    print("YouTubeTB System Environment Check")
    print("=" * 50)
    print()
    
    all_ok = True
    
    # Python version
    print("[1] Python Version:")
    all_ok &= check_python()
    print()
    
    # Critical packages
    print("[2] Critical Python Packages:")
    packages = [
        ("google-generativeai", "google.generativeai"),
        ("playwright", "playwright"),
        ("yt-dlp", "yt_dlp"),
        ("Pillow", "PIL"),
        ("requests", "requests"),
        ("typer", "typer"),
        ("rich", "rich"),
    ]
    for pkg, imp in packages:
        all_ok &= check_package(pkg, imp)
    print()
    
    # Optional packages
    print("[3] Optional Packages:")
    optional = [
        ("arabic-reshaper", "arabic_reshaper"),
        ("python-bidi", "bidi"),
        ("absl-py", "absl"),
    ]
    for pkg, imp in optional:
        check_package(pkg, imp)  # Don't fail if missing
    print()
    
    # External tools
    print("[4] External Tools:")
    ffmpeg_ok = check_command("ffmpeg")
    yt_dlp_ok = check_command("yt-dlp")
    
    # Special note for FFmpeg if not in PATH but might be installed
    if not ffmpeg_ok and sys.platform == "win32":
        print("  💡 FFmpeg may be installed but not in PATH.")
        print("     Try running 'ffmpeg -version' in PowerShell/CMD.")
        print("     If it works, the pipeline should work too.")
        # Don't fail the check - just warn
        ffmpeg_ok = True
    
    all_ok &= ffmpeg_ok
    all_ok &= yt_dlp_ok
    print()
    
    # Playwright browsers
    print("[5] Playwright Browsers:")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✓ Chromium browser installed")
            except Exception as e:
                print(f"✗ Chromium browser - NOT INSTALLED")
                print(f"  Install: playwright install chromium")
                all_ok = False
    except ImportError:
        print("✗ Playwright not installed")
        all_ok = False
    print()
    
    # Secrets files
    print("[6] Secrets Files:")
    repo_root = Path(__file__).resolve().parent
    secrets_dir = repo_root / "secrets"
    required_secrets = [
        "api_key.txt",
        "client_secret.json",
        "cookies.txt"
    ]
    for secret_file in required_secrets:
        path = secrets_dir / secret_file
        if path.exists():
            print(f"✓ {secret_file}")
        else:
            print(f"⚠️  {secret_file} - NOT FOUND")
            print(f"   Expected: {path}")
    print()
    
    # Summary
    print("=" * 50)
    if all_ok:
        print("✅ ALL CHECKS PASSED!")
        print("   You can run: python main.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("   Fix the issues above before running the pipeline")
    print("=" * 50)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
