#!/usr/bin/env python3
"""
Test encryption compatibility between add_api_key.py and decrypt_secrets.py
"""

from pathlib import Path
import sys
import os

# Setup paths
repo_root = Path(__file__).resolve().parent
secrets_dir = repo_root / "secrets"
encrypted_dir = repo_root / "secrets_encrypted"
test_file = secrets_dir / "test_encryption.txt"

# Ensure directories exist
secrets_dir.mkdir(exist_ok=True)
encrypted_dir.mkdir(exist_ok=True)

# Create test file
test_content = "TEST KEY: AIzaSyTest123-abcdefghijklmnopqrstuvwxyz"
test_file.write_text(test_content, encoding='utf-8')
print(f"📝 Created test file: {test_file}")
print(f"   Content: {test_content}")

# Test 1: Encrypt with add_api_key.py method
print("\n🔒 Test 1: Encrypting with add_api_key.py method (PBKDF2)...")
from add_api_key import encrypt_file, ENCRYPTION_PASSWORD

success = encrypt_file(test_file, ENCRYPTION_PASSWORD)
if not success:
    print("❌ Encryption failed!")
    sys.exit(1)

encrypted_file = encrypted_dir / "test_encryption.txt.enc"
if not encrypted_file.exists():
    print(f"❌ Encrypted file not created: {encrypted_file}")
    sys.exit(1)

print(f"✅ Encrypted file created: {encrypted_file.name}")
print(f"   Size: {encrypted_file.stat().st_size} bytes")

# Test 2: Decrypt with decrypt_secrets.py method
print("\n🔓 Test 2: Decrypting with decrypt_secrets.py method...")
sys.path.insert(0, str(repo_root / "scripts"))
from decrypt_secrets import decrypt_file

try:
    decrypted_data = decrypt_file(encrypted_file, ENCRYPTION_PASSWORD)
    decrypted_content = decrypted_data.decode('utf-8')
    
    print(f"✅ Decryption successful!")
    print(f"   Decrypted content: {decrypted_content}")
    
    # Test 3: Verify content matches
    print("\n✅ Test 3: Verifying content integrity...")
    if decrypted_content == test_content:
        print("✅ Content matches perfectly!")
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ Encryption: add_api_key.py uses PBKDF2 with salt")
        print("   ✅ Decryption: decrypt_secrets.py can decrypt successfully")
        print("   ✅ Password '2552025' works correctly")
        print("   ✅ Content integrity verified")
    else:
        print(f"❌ Content mismatch!")
        print(f"   Expected: {test_content}")
        print(f"   Got: {decrypted_content}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Decryption failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print("\n🧹 Cleaning up test files...")
test_file.unlink(missing_ok=True)
encrypted_file.unlink(missing_ok=True)
print("✅ Test files deleted")

print("\n" + "=" * 60)
print("🎯 ENCRYPTION COMPATIBILITY VERIFIED!")
print("=" * 60)
print("\nYou can now:")
print("1. Run 'python add_api_key.py YOUR_KEY' to add and encrypt keys")
print("2. Push to GitHub (secrets_encrypted/ folder)")
print("3. Pull on another machine")
print("4. Run 'python scripts\\decrypt_secrets.py' with password '2552025'")
print("5. All secrets will decrypt successfully! ✅")
