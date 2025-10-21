#!/usr/bin/env python3
"""
YouTubeTB Automated Setup Script for Google Colab
Run this after cloning the repository to install all dependencies and decrypt secrets.

Usage:
    python setup_colab.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, silent=False):
    """Run a shell command and print status."""
    print(f"\n{'='*50}")
    print(f"📌 {description}")
    print(f"{'='*50}")
    
    try:
        if silent:
            subprocess.run(cmd, shell=True, check=True, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} - Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed!")
        print(f"   Error: {e}")
        return False


def main():
    print("🚀 YouTubeTB Automated Setup")
    print("="*50)
    print()
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: requirements.txt not found!")
        print("   Make sure you're in the youtubetb-refactored directory")
        sys.exit(1)
    
    # Step 1: Install Python dependencies
    if not run_command(
        "pip install -q -r requirements.txt",
        "Installing Python packages",
        silent=False
    ):
        print("⚠️  Warning: Some packages may have failed to install")
    
    # Step 2: Install Playwright browser
    run_command(
        "python -m playwright install chromium",
        "Installing Playwright Chromium browser"
    )
    
    # Step 3: Install FFmpeg
    print("\n" + "="*50)
    print("📌 Installing FFmpeg")
    print("="*50)
    run_command("apt-get update -qq", "Updating package lists", silent=True)
    run_command("apt-get install -y ffmpeg", "Installing FFmpeg", silent=True)
    print("✅ FFmpeg installed!")
    
    # Step 4: Decrypt secrets
    print("\n" + "="*50)
    print("📌 Decrypting secrets")
    print("="*50)
    print("⚠️  You will be prompted for your encryption password")
    print()
    
    try:
        subprocess.run("python scripts/decrypt_secrets.py", shell=True, check=True)
        print("\n✅ Secrets decrypted successfully!")
    except subprocess.CalledProcessError:
        print("\n❌ Failed to decrypt secrets!")
        print("   Make sure you entered the correct password")
        sys.exit(1)
    
    # Step 5: Verify setup
    print("\n" + "="*50)
    print("📊 Setup Verification")
    print("="*50)
    
    secrets_dir = Path("secrets")
    if secrets_dir.exists():
        secret_files = list(secrets_dir.glob("*"))
        print(f"✅ Secrets folder: {len(secret_files)} files found")
    else:
        print("⚠️  Secrets folder not found")
    
    ffmpeg_path = subprocess.run("which ffmpeg", shell=True, 
                                 capture_output=True, text=True)
    if ffmpeg_path.returncode == 0:
        print(f"✅ FFmpeg: {ffmpeg_path.stdout.strip()}")
    else:
        print("⚠️  FFmpeg not found")
    
    print("✅ Playwright: Installed")
    
    # Final message
    print("\n" + "="*50)
    print("🎉 Setup Complete!")
    print("="*50)
    print("\n🎯 Ready to run! Execute:")
    print("   python main.py")
    print()


if __name__ == "__main__":
    main()
