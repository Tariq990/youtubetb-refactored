#!/usr/bin/env python3
"""
Re-encrypt all secrets with PBKDF2 format (password: 2552025)
This encrypts ALL files in secrets/ directory.
"""

from pathlib import Path
import sys
import os

# Add scripts to path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "scripts"))

from encrypt_secrets import encrypt_file

# Configuration
PASSWORD = "2552025"
secrets_dir = repo_root / "secrets"
encrypted_dir = repo_root / "secrets_encrypted"

# Get ALL files in secrets/ directory (excluding subdirectories)
all_files = []
for item in secrets_dir.iterdir():
    if item.is_file() and not item.name.startswith('.'):
        all_files.append(item.name)

existing_files = sorted(all_files)

if not existing_files:
    print("❌ No secret files found!")
    print(f"   Looking in: {secrets_dir}")
    sys.exit(1)

print("🔐 Re-encrypting Secrets with PBKDF2 Format")
print("=" * 60)
print(f"📁 Found {len(existing_files)} file(s) to encrypt:")
for fname in existing_files:
    size = (secrets_dir / fname).stat().st_size
    print(f"   • {fname} ({size} bytes)")

# Generate random salt (same for all files in this batch)
salt = os.urandom(16)

# Create encrypted directory
encrypted_dir.mkdir(exist_ok=True)

# Encrypt each file
print(f"\n🔒 Encrypting files with PBKDF2 (password: {PASSWORD})...")
encrypted_count = 0

for fname in existing_files:
    file_path = secrets_dir / fname
    encrypted_path = encrypted_dir / f"{fname}.enc"
    
    try:
        # Encrypt file
        encrypted_data = encrypt_file(file_path, PASSWORD, salt)
        
        # Save encrypted file with salt prepended
        with open(encrypted_path, 'wb') as f:
            f.write(salt)  # First 16 bytes are the salt
            f.write(encrypted_data)  # Rest is encrypted content
        
        print(f"   ✅ {fname} → {encrypted_path.name}")
        encrypted_count += 1
        
    except Exception as e:
        print(f"   ❌ Failed to encrypt {fname}: {e}")

print(f"\n✅ Re-encryption complete!")
print(f"   📂 {encrypted_count}/{len(existing_files)} files encrypted")
print(f"   🔐 Password: {PASSWORD}")
print(f"\n📋 Next steps:")
print(f"   1. Test decryption: python scripts\\decrypt_secrets.py")
print(f"   2. Commit changes: git add secrets_encrypted/")
print(f"   3. Push to GitHub: git push")
print(f"\n🎯 All files now use PBKDF2 encryption (compatible with decrypt_secrets.py)!")
