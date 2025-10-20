#!/bin/bash
# YouTubeTB Automated Setup Script for Google Colab
# Run this after cloning the repository

set -e  # Exit on any error

echo "🚀 Starting YouTubeTB Setup..."
echo "================================"

# 1. Install Python dependencies
echo ""
echo "📦 Installing Python packages..."
pip install -q -r requirements.txt

# 2. Install Playwright browser
echo ""
echo "🌐 Installing Playwright Chromium..."
python -m playwright install chromium

# 3. Install FFmpeg
echo ""
echo "🎬 Installing FFmpeg..."
apt-get update -qq > /dev/null 2>&1
apt-get install -y ffmpeg > /dev/null 2>&1

# 4. Decrypt secrets
echo ""
echo "🔓 Decrypting secrets..."
echo "⚠️  You will be prompted for your encryption password"
python scripts/decrypt_secrets.py

# 5. Verify setup
echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Verification:"
echo "   • Secrets folder: $(ls -la secrets/ 2>/dev/null | wc -l) files"
echo "   • FFmpeg: $(which ffmpeg)"
echo "   • Playwright: Installed"
echo ""
echo "🎯 Ready to run! Execute: python main.py"
