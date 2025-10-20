#!/usr/bin/env python3
"""
Decrypt secrets files encrypted with encrypt_secrets.py

This script decrypts files from secrets_encrypted/ folder using the same password
used during encryption. Decrypted files are restored to secrets/ folder.

Usage:
    python scripts/decrypt_secrets.py
    
The script will prompt for the password and decrypt all .enc files.
"""

from pathlib import Path
import getpass
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet encryption key from a password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt bytes (extracted from encrypted file)
        
    Returns:
        32-byte encryption key suitable for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # Must match encryption iterations
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def decrypt_file(encrypted_path: Path, password: str) -> bytes:
    """
    Decrypt a file that was encrypted with password-based encryption.
    
    Args:
        encrypted_path: Path to encrypted .enc file
        password: Decryption password
        
    Returns:
        Decrypted file contents
        
    Raises:
        InvalidToken: If password is incorrect
    """
    with open(encrypted_path, 'rb') as f:
        salt = f.read(16)  # First 16 bytes are the salt
        encrypted_data = f.read()  # Rest is encrypted content
    
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data


def main():
    """Main decryption workflow."""
    repo_root = Path(__file__).resolve().parents[1]
    encrypted_dir = repo_root / "secrets_encrypted"
    secrets_dir = repo_root / "secrets"
    
    # Validate encrypted directory exists
    if not encrypted_dir.exists():
        print("❌ Error: secrets_encrypted/ directory not found!")
        print(f"   Expected path: {encrypted_dir}")
        print("\n💡 Tip: If you're on a new machine:")
        print("   1. Clone the repo: git clone <your-repo-url>")
        print("   2. The secrets_encrypted/ folder should be in the repo")
        return
    
    # Find encrypted files
    encrypted_files = list(encrypted_dir.glob("*.enc"))
    
    if not encrypted_files:
        print("❌ No encrypted files found!")
        print(f"   Looking in: {encrypted_dir}")
        return
    
    print("🔓 YouTubeTB Secrets Decryption")
    print("=" * 50)
    print(f"\n📁 Found {len(encrypted_files)} encrypted file(s):")
    for enc_file in encrypted_files:
        size = enc_file.stat().st_size
        original_name = enc_file.stem  # Remove .enc extension
        print(f"   • {enc_file.name} → {original_name} ({size} bytes)")
    
    # Get password from user
    print("\n🔑 Enter decryption password:")
    password = getpass.getpass("   Password: ")
    
    # Create secrets directory
    secrets_dir.mkdir(exist_ok=True)
    
    # Decrypt each file
    print(f"\n🔓 Decrypting files...")
    decrypted_count = 0
    failed_count = 0
    
    for enc_file in encrypted_files:
        original_name = enc_file.stem  # Remove .enc extension
        output_path = secrets_dir / original_name
        
        try:
            # Decrypt file
            decrypted_data = decrypt_file(enc_file, password)
            
            # Save decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"   ✅ {enc_file.name} → {original_name}")
            decrypted_count += 1
            
        except InvalidToken:
            print(f"   ❌ {enc_file.name} - WRONG PASSWORD or corrupted file")
            failed_count += 1
        except Exception as e:
            print(f"   ❌ {enc_file.name} - Error: {e}")
            failed_count += 1
    
    # Summary
    print(f"\n📊 Decryption Summary:")
    print(f"   ✅ Successfully decrypted: {decrypted_count}")
    if failed_count > 0:
        print(f"   ❌ Failed: {failed_count}")
    
    if decrypted_count > 0:
        print(f"\n✅ Decryption complete!")
        print(f"   📂 Decrypted files saved to: {secrets_dir}")
        print(f"\n📋 Next steps:")
        print(f"   • Run your pipeline: python main.py")
        print(f"   • The secrets/ folder is in .gitignore (won't be committed)")
    else:
        print(f"\n❌ No files were decrypted. Please check:")
        print(f"   • Password is correct")
        print(f"   • Encrypted files are not corrupted")


if __name__ == "__main__":
    main()
