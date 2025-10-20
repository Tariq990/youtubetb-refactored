#!/usr/bin/env python3
"""
Encrypt sensitive secrets files with a password for safe GitHub storage.

This script encrypts files in secrets/ folder using password-based encryption (Fernet).
The encrypted files can be safely committed to GitHub and decrypted later with the password.

Usage:
    python scripts/encrypt_secrets.py
    
The script will prompt for a password and encrypt all files in secrets/ to secrets_encrypted/
"""

from pathlib import Path
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet encryption key from a password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt bytes (16 bytes recommended)
        
    Returns:
        32-byte encryption key suitable for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # High iteration count for security
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(file_path: Path, password: str, salt: bytes) -> bytes:
    """
    Encrypt a file's contents with password-based encryption.
    
    Args:
        file_path: Path to file to encrypt
        password: Encryption password
        salt: Salt for key derivation
        
    Returns:
        Encrypted file contents
    """
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    encrypted_data = fernet.encrypt(data)
    return encrypted_data


def main():
    """Main encryption workflow."""
    repo_root = Path(__file__).resolve().parents[1]
    secrets_dir = repo_root / "secrets"
    encrypted_dir = repo_root / "secrets_encrypted"
    
    # Validate secrets directory exists
    if not secrets_dir.exists():
        print("❌ Error: secrets/ directory not found!")
        print(f"   Expected path: {secrets_dir}")
        return
    
    # Get list of files to encrypt
    secret_files = [
        "api_key.txt",
        "client_secret.json",
        "cookies.txt",
        "token.json",
        ".env"  # Environment variables
    ]
    
    existing_files = [f for f in secret_files if (secrets_dir / f).exists()]
    
    if not existing_files:
        print("❌ No secret files found to encrypt!")
        print(f"   Looking for: {', '.join(secret_files)}")
        print(f"   In directory: {secrets_dir}")
        return
    
    print("🔐 YouTubeTB Secrets Encryption")
    print("=" * 50)
    print(f"\n📁 Found {len(existing_files)} file(s) to encrypt:")
    for fname in existing_files:
        size = (secrets_dir / fname).stat().st_size
        print(f"   • {fname} ({size} bytes)")
    
    # Get password from user
    print("\n🔑 Enter encryption password:")
    password = getpass.getpass("   Password: ")
    password_confirm = getpass.getpass("   Confirm password: ")
    
    if password != password_confirm:
        print("❌ Passwords don't match!")
        return
    
    if len(password) < 8:
        print("⚠️  Warning: Password is very short. Recommend at least 8 characters.")
        cont = input("   Continue anyway? (y/N): ")
        if cont.lower() != 'y':
            return
    
    # Generate random salt (will be stored with encrypted files)
    import os
    salt = os.urandom(16)
    
    # Create encrypted directory
    encrypted_dir.mkdir(exist_ok=True)
    
    # Encrypt each file
    print(f"\n🔒 Encrypting files...")
    encrypted_count = 0
    
    for fname in existing_files:
        file_path = secrets_dir / fname
        encrypted_path = encrypted_dir / f"{fname}.enc"
        
        try:
            # Encrypt file
            encrypted_data = encrypt_file(file_path, password, salt)
            
            # Save encrypted file with salt prepended
            with open(encrypted_path, 'wb') as f:
                f.write(salt)  # First 16 bytes are the salt
                f.write(encrypted_data)  # Rest is encrypted content
            
            print(f"   ✅ {fname} → {encrypted_path.name}")
            encrypted_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to encrypt {fname}: {e}")
    
    # Create metadata file
    metadata = {
        "encrypted_files": [f"{f}.enc" for f in existing_files],
        "original_files": existing_files,
        "encryption_method": "Fernet (AES-128)",
        "kdf": "PBKDF2-SHA256",
        "iterations": 100000,
        "note": "First 16 bytes of each .enc file is the salt"
    }
    
    metadata_path = encrypted_dir / "encryption_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Encryption complete!")
    print(f"   📂 Encrypted files saved to: {encrypted_dir}")
    print(f"   📝 Metadata saved to: {metadata_path.name}")
    print(f"\n📋 Next steps:")
    print(f"   1. Add 'secrets/' to .gitignore (keep originals local)")
    print(f"   2. Commit 'secrets_encrypted/' to GitHub (safe to share)")
    print(f"   3. Use 'scripts/decrypt_secrets.py' to decrypt on Colab/other machines")
    print(f"\n⚠️  IMPORTANT: Remember your password! It cannot be recovered.")


if __name__ == "__main__":
    main()
