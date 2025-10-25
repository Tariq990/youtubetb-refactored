#!/usr/bin/env python3
"""
Smart API Key Manager - YouTubeTB
Automatically detects key type and adds to appropriate file with encryption
"""

import os
import sys
import requests
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


# Encryption password (stored securely in code)
ENCRYPTION_PASSWORD = "2552025"


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet encryption key from a password using PBKDF2.
    MATCHES encrypt_secrets.py and decrypt_secrets.py implementation.
    
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
        iterations=100000,  # High iteration count for security (matches encrypt_secrets.py)
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(file_path: Path, password: str) -> bool:
    """
    Encrypt a single file with password using PBKDF2 (compatible with decrypt_secrets.py)
    """
    try:
        # Generate random salt (16 bytes)
        salt = os.urandom(16)
        
        # Derive key using PBKDF2
        key = derive_key_from_password(password, salt)
        fernet = Fernet(key)
        
        # Read original file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Encrypt
        encrypted = fernet.encrypt(data)
        
        # Save to encrypted folder with salt prepended
        enc_dir = file_path.parent.parent / "secrets_encrypted"
        enc_dir.mkdir(exist_ok=True)
        enc_file = enc_dir / f"{file_path.name}.enc"
        
        with open(enc_file, 'wb') as f:
            f.write(salt)  # First 16 bytes are the salt
            f.write(encrypted)  # Rest is encrypted content
        
        print(f"   ✅ Encrypted: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Encryption failed: {e}")
        return False


def test_youtube_api(api_key: str) -> dict:
    """Test if API key is a valid YouTube Data API key"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "test",
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        
        if r.status_code == 200:
            return {
                "type": "youtube",
                "valid": True,
                "status": "✅ Working",
                "quota": "Full quota available"
            }
        elif r.status_code == 403:
            error_msg = r.json().get("error", {}).get("message", "")
            if "quota" in error_msg.lower():
                return {
                    "type": "youtube",
                    "valid": True,
                    "status": "⚠️  Quota exceeded",
                    "quota": "Exhausted (wait for reset)"
                }
            elif "blocked" in error_msg.lower():
                return {
                    "type": "youtube",
                    "valid": False,
                    "status": "❌ API not enabled",
                    "error": "YouTube Data API not enabled in project"
                }
            else:
                return {
                    "type": "youtube",
                    "valid": False,
                    "status": "❌ Forbidden",
                    "error": error_msg[:100]
                }
        else:
            return {
                "type": "youtube",
                "valid": False,
                "status": f"❌ HTTP {r.status_code}",
                "error": r.text[:100]
            }
            
    except requests.exceptions.Timeout:
        return {
            "type": "youtube",
            "valid": False,
            "status": "❌ Timeout",
            "error": "Connection timeout"
        }
    except Exception as e:
        return {
            "type": "youtube",
            "valid": False,
            "status": "❌ Error",
            "error": str(e)[:100]
        }


def test_gemini_api(api_key: str) -> dict:
    """Test if API key is a valid Gemini API key"""
    try:
        import google.generativeai as genai  # type: ignore
        
        # Configure with test key
        genai.configure(api_key=api_key)  # type: ignore
        
        # Try to create model
        model = genai.GenerativeModel('gemini-2.5-flash')  # type: ignore
        
        # Test with simple prompt
        response = model.generate_content("ping")
        
        if response:
            return {
                "type": "gemini",
                "valid": True,
                "status": "✅ Working",
                "model": "gemini-2.5-flash"
            }
        else:
            return {
                "type": "gemini",
                "valid": False,
                "status": "❌ No response",
                "error": "Model didn't respond"
            }
            
    except Exception as e:
        error_msg = str(e)
        
        if "429" in error_msg or "quota" in error_msg.lower():
            return {
                "type": "gemini",
                "valid": True,
                "status": "⚠️  Quota exceeded",
                "quota": "Exhausted (wait for reset)"
            }
        elif "API key not valid" in error_msg or "invalid" in error_msg.lower():
            return {
                "type": "gemini",
                "valid": False,
                "status": "❌ Invalid key",
                "error": "API key not valid"
            }
        else:
            return {
                "type": "gemini",
                "valid": False,
                "status": "❌ Error",
                "error": error_msg[:100]
            }


def detect_api_type(api_key: str) -> dict:
    """Automatically detect API key type by testing both services"""
    print(f"\n🔍 Detecting API key type: {api_key[:10]}...")
    print("="*60)
    
    results = {
        "youtube": None,
        "gemini": None,
        "detected_type": None,
        "is_valid": False,
        "works_on_both": False
    }
    
    # Test YouTube first (faster)
    print("📺 Testing YouTube Data API...")
    youtube_result = test_youtube_api(api_key)
    results["youtube"] = youtube_result
    print(f"   {youtube_result['status']}")
    
    # Always test Gemini too
    print("\n🤖 Testing Gemini AI API...")
    gemini_result = test_gemini_api(api_key)
    results["gemini"] = gemini_result
    print(f"   {gemini_result['status']}")
    
    # Check if works on both services
    youtube_valid = youtube_result["valid"]
    gemini_valid = gemini_result["valid"]
    
    if youtube_valid and gemini_valid:
        results["detected_type"] = "both"
        results["is_valid"] = True
        results["works_on_both"] = True
        print(f"\n🎉 SPECIAL: Key works on BOTH services!")
        print(f"   Will be added to both YouTube and Gemini files")
        return results
    elif youtube_valid:
        results["detected_type"] = "youtube"
        results["is_valid"] = True
        print(f"\n   ✅ Detected: YouTube Data API key only")
        return results
    elif gemini_valid:
        results["detected_type"] = "gemini"
        results["is_valid"] = True
        print(f"\n   ✅ Detected: Gemini AI API key only")
        return results
    
    # Both failed
    print("\n❌ Key is not valid for YouTube or Gemini")
    return results


def add_key_to_file(api_key: str, key_type: str, repo_root: Path) -> bool:
    """Add API key to appropriate file based on type"""
    
    success_count = 0
    
    # Handle "both" type - add to both files
    if key_type == "both":
        print(f"\n📂 Adding to BOTH YouTube and Gemini files...")
        
        # Add to YouTube
        yt_file = repo_root / "secrets" / "api_keys.txt"
        if yt_file.exists():
            existing_content = yt_file.read_text(encoding="utf-8")
            if api_key in existing_content:
                print(f"   ⚠️  Already exists in api_keys.txt")
            else:
                with open(yt_file, 'a', encoding="utf-8") as f:
                    f.write(f"\n{api_key}")
                print(f"   ✅ Added to api_keys.txt (YouTube)")
                success_count += 1
        else:
            yt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(yt_file, 'w', encoding="utf-8") as f:
                f.write(f"# YouTube Data API Keys\n")
                f.write(f"{api_key}\n")
            print(f"   ✅ Created api_keys.txt and added key (YouTube)")
            success_count += 1
        
        # Add to Gemini
        gemini_file = repo_root / "secrets" / "api_key.txt"
        if gemini_file.exists():
            existing_content = gemini_file.read_text(encoding="utf-8")
            if api_key in existing_content:
                print(f"   ⚠️  Already exists in api_key.txt")
            else:
                # Append to multi-line Gemini file
                with open(gemini_file, 'a', encoding="utf-8") as f:
                    f.write(f"\n{api_key}")
                print(f"   ✅ Added to api_key.txt (Gemini)")
                success_count += 1
        else:
            gemini_file.parent.mkdir(parents=True, exist_ok=True)
            gemini_file.write_text(api_key, encoding="utf-8")
            print(f"   ✅ Created api_key.txt and added key (Gemini)")
            success_count += 1
        
        return success_count > 0
    
    # Handle single service types
    if key_type == "youtube":
        file_path = repo_root / "secrets" / "api_keys.txt"
        key_name = "YouTube Data API"
    elif key_type == "gemini":
        file_path = repo_root / "secrets" / "api_key.txt"
        key_name = "Gemini AI API"
    else:
        print(f"❌ Unknown key type: {key_type}")
        return False
    
    # Check if key already exists
    if file_path.exists():
        existing_content = file_path.read_text(encoding="utf-8")
        if api_key in existing_content:
            print(f"⚠️  Key already exists in {file_path.name}")
            return False
    
    # Add key to file
    try:
        # For YouTube (multi-key file)
        if key_type == "youtube":
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                # Add new key at the end
                with open(file_path, 'a', encoding="utf-8") as f:
                    f.write(f"\n{api_key}")
            else:
                # Create new file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.write(f"# YouTube Data API Keys\n")
                    f.write(f"{api_key}\n")
        
        # For Gemini (single-key file)
        elif key_type == "gemini":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file_path.exists():
                # Append to multi-line file
                with open(file_path, 'a', encoding="utf-8") as f:
                    f.write(f"\n{api_key}")
            else:
                file_path.write_text(api_key, encoding="utf-8")
        
        print(f"✅ Added {key_name} key to {file_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add key: {e}")
        return False


def auto_encrypt_secrets(repo_root: Path) -> bool:
    """Automatically encrypt all secrets using stored password"""
    print("\n🔐 Auto-encrypting secrets...")
    print("="*60)
    
    secrets_dir = repo_root / "secrets"
    if not secrets_dir.exists():
        print("❌ Secrets directory not found")
        return False
    
    # Files to encrypt
    files_to_encrypt = [
        "api_key.txt",
        "api_keys.txt",
        "client_secret.json",
        "cookies.txt",
        "token.json",
        ".env"
    ]
    
    encrypted_count = 0
    for filename in files_to_encrypt:
        file_path = secrets_dir / filename
        if file_path.exists():
            if encrypt_file(file_path, ENCRYPTION_PASSWORD):
                encrypted_count += 1
    
    print(f"\n✅ Encrypted {encrypted_count} file(s)")
    return encrypted_count > 0


def auto_git_push(repo_root: Path) -> bool:
    """Automatically commit and push encrypted secrets"""
    print("\n📤 Auto-pushing to GitHub...")
    print("="*60)
    
    try:
        import subprocess
        
        # Add encrypted files
        result = subprocess.run(
            ["git", "add", "secrets_encrypted/"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Git add failed: {result.stderr}")
            return False
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", "Auto-add API key with encryption"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                print("⚠️  No changes to commit (already up-to-date)")
                return True
            else:
                print(f"❌ Git commit failed: {result.stderr}")
                return False
        
        print("✅ Committed changes")
        
        # Push
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Git push failed: {result.stderr}")
            return False
        
        print("✅ Pushed to GitHub")
        return True
        
    except Exception as e:
        print(f"❌ Git operation failed: {e}")
        return False


def scan_existing_keys(repo_root: Path) -> dict:
    """Scan and test all existing API keys"""
    print("\n🔍 Scanning existing API keys...")
    print("="*60)
    
    results = {
        "youtube": [],
        "gemini": []
    }
    
    # Scan YouTube keys
    yt_file = repo_root / "secrets" / "api_keys.txt"
    if yt_file.exists():
        print("\n📺 YouTube Data API Keys:")
        print("-" * 60)
        content = yt_file.read_text(encoding="utf-8")
        keys = [line.strip() for line in content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        for idx, key in enumerate(keys, 1):
            print(f"\n🔑 Key #{idx}: {key[:10]}...{key[-4:]}")
            result = test_youtube_api(key)
            results["youtube"].append({
                "key": key,
                "index": idx,
                "result": result
            })
            print(f"   Status: {result['status']}")
            if result.get("quota"):
                print(f"   Quota: {result['quota']}")
            if result.get("error"):
                print(f"   Error: {result['error']}")
    else:
        print("\n📺 No YouTube API keys found")
    
    # Scan Gemini keys
    gemini_file = repo_root / "secrets" / "api_key.txt"
    if gemini_file.exists():
        print("\n\n🤖 Gemini AI API Keys:")
        print("-" * 60)
        content = gemini_file.read_text(encoding="utf-8").strip()
        keys = [line.strip() for line in content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        for idx, key in enumerate(keys, 1):
            print(f"\n🔑 Key #{idx}: {key[:10]}...{key[-4:]}")
            result = test_gemini_api(key)
            results["gemini"].append({
                "key": key,
                "index": idx,
                "result": result
            })
            print(f"   Status: {result['status']}")
            if result.get("model"):
                print(f"   Model: {result['model']}")
            if result.get("error"):
                print(f"   Error: {result['error']}")
    else:
        print("\n\n🤖 No Gemini API keys found")
    
    return results


def check_duplicate(api_key: str, existing_results: dict) -> dict:
    """Check if key already exists"""
    for service in ["youtube", "gemini"]:
        for item in existing_results[service]:
            if item["key"] == api_key:
                return {
                    "is_duplicate": True,
                    "service": service,
                    "index": item["index"],
                    "status": item["result"]["status"]
                }
    
    return {"is_duplicate": False}


def print_summary(existing_results: dict):
    """Print summary of all keys"""
    print("\n" + "="*60)
    print("📊 SUMMARY OF ALL KEYS")
    print("="*60)
    
    # YouTube summary
    yt_keys = existing_results["youtube"]
    if yt_keys:
        print(f"\n📺 YouTube Data API ({len(yt_keys)} keys):")
        working = sum(1 for k in yt_keys if k["result"]["valid"])
        quota_exceeded = sum(1 for k in yt_keys if "quota exceeded" in k["result"]["status"].lower())
        failed = len(yt_keys) - working - quota_exceeded
        
        print(f"   ✅ Working: {working}")
        print(f"   ⚠️  Quota Exceeded: {quota_exceeded}")
        print(f"   ❌ Failed/Blocked: {failed}")
    
    # Gemini summary
    gemini_keys = existing_results["gemini"]
    if gemini_keys:
        print(f"\n🤖 Gemini AI API ({len(gemini_keys)} keys):")
        working = sum(1 for k in gemini_keys if k["result"]["valid"])
        quota_exceeded = sum(1 for k in gemini_keys if "quota exceeded" in k["result"]["status"].lower())
        failed = len(gemini_keys) - working - quota_exceeded
        
        print(f"   ✅ Working: {working}")
        print(f"   ⚠️  Quota Exceeded: {quota_exceeded}")
        print(f"   ❌ Failed/Invalid: {failed}")


def main():
    """Main function"""
    print("="*60)
    print("🔑 Smart API Key Manager - YouTubeTB")
    print("="*60)
    
    # Get repo root
    repo_root = Path(__file__).parent
    
    # Scan existing keys first
    existing_results = scan_existing_keys(repo_root)
    
    # Print summary
    print_summary(existing_results)
    
    # Get API key from user
    print("\n" + "="*60)
    print("📝 Enter NEW API key to test and add:")
    print("   (or press Enter to exit)")
    print("="*60)
    api_key = input("\nAPI Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided - Exiting")
        return
    
    # Check for duplicates
    dup_check = check_duplicate(api_key, existing_results)
    if dup_check["is_duplicate"]:
        print(f"\n⚠️  DUPLICATE DETECTED!")
        print(f"   Service: {dup_check['service'].upper()}")
        print(f"   Position: Key #{dup_check['index']}")
        print(f"   Status: {dup_check['status']}")
        print("\n❌ Key already exists - Not adding")
        return
    
    # Detect key type
    detection = detect_api_type(api_key)
    
    if not detection["is_valid"]:
        print("\n❌ API key is not valid for any supported service")
        print("\nSupported services:")
        print("  • YouTube Data API v3")
        print("  • Gemini AI API")
        return
    
    key_type = detection["detected_type"]
    
    # Add to appropriate file
    print(f"\n📂 Adding key to {key_type} file...")
    if not add_key_to_file(api_key, key_type, repo_root):
        print("❌ Failed to add key to file")
        return
    
    # Auto-encrypt
    if not auto_encrypt_secrets(repo_root):
        print("❌ Failed to encrypt secrets")
        return
    
    # Auto-push
    if not auto_git_push(repo_root):
        print("⚠️  Failed to push to GitHub (manual push required)")
    
    print("\n" + "="*60)
    print("✅ ALL DONE!")
    print("="*60)
    print(f"\n📊 Summary:")
    
    if key_type == "both":
        print(f"  • API Type: BOTH (YouTube + Gemini)")
        print(f"  • YouTube Status: {detection['youtube']['status']}")
        print(f"  • Gemini Status: {detection['gemini']['status']}")
        print(f"  • Files: api_keys.txt + api_key.txt")
    else:
        print(f"  • API Type: {key_type.upper()}")
        print(f"  • Status: {detection[key_type]['status']}")
        print(f"  • File: secrets/{'api_keys.txt' if key_type == 'youtube' else 'api_key.txt'}")
    
    print(f"  • Encrypted: ✅")
    print(f"  • Pushed: ✅")
    print("\n🎉 Key is ready to use!")


if __name__ == "__main__":
    main()
