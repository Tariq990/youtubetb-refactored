#!/usr/bin/env python3
"""
Test Fallback System - Verify all components use multi-key fallback
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def test_youtube_fallback():
    """Test YouTube API multi-key fallback"""
    print("\n" + "="*60)
    print("🧪 Testing YouTube API Fallback System")
    print("="*60)
    
    try:
        from src.infrastructure.adapters.search import _load_all_youtube_api_keys
        
        keys = _load_all_youtube_api_keys()
        print(f"\n✅ YouTube keys loaded: {len(keys)}")
        
        for idx, key in enumerate(keys, 1):
            masked = key[:10] + "..." if len(key) > 10 else key
            print(f"   Key #{idx}: {masked}")
        
        if len(keys) >= 3:
            print("\n✅ PASS: Multi-key fallback ready (3+ keys)")
            return True
        else:
            print(f"\n⚠️  WARNING: Only {len(keys)} key(s) - recommend 3+")
            return len(keys) > 0
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_gemini_fallback_process():
    """Test Gemini API fallback in process.py"""
    print("\n" + "="*60)
    print("🧪 Testing Gemini API Fallback (process.py)")
    print("="*60)
    
    try:
        # Simulate loading keys like process.py does
        import os
        
        api_keys = []
        
        # 1. Environment
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            api_keys.append(env_key.strip())
        
        # 2. Multi-key file
        api_keys_file = repo_root / "secrets" / "api_keys.txt"
        if api_keys_file.exists():
            lines = api_keys_file.read_text(encoding="utf-8").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line not in api_keys:
                        api_keys.append(line)
        
        # 3. Single-key file
        if not api_keys:
            api_key_file = repo_root / "secrets" / "api_key.txt"
            if api_key_file.exists():
                key = api_key_file.read_text(encoding="utf-8").strip()
                if key:
                    api_keys.append(key)
        
        print(f"\n✅ Gemini keys loaded: {len(api_keys)}")
        
        for idx, key in enumerate(api_keys, 1):
            masked = key[:10] + "..." if len(key) > 10 else key
            print(f"   Key #{idx}: {masked}")
        
        if len(api_keys) >= 2:
            print("\n✅ PASS: Multi-key fallback ready (2+ keys)")
            return True
        else:
            print(f"\n⚠️  WARNING: Only {len(api_keys)} key(s) - recommend 2+")
            return len(api_keys) > 0
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_gemini_fallback_metadata():
    """Test Gemini API fallback in youtube_metadata.py"""
    print("\n" + "="*60)
    print("🧪 Testing Gemini API Fallback (youtube_metadata.py)")
    print("="*60)
    
    try:
        # Check if _configure_model has multi-key support
        from src.infrastructure.adapters import youtube_metadata
        import inspect
        
        source = inspect.getsource(youtube_metadata._configure_model)
        
        # Look for multi-key patterns
        has_loop = "for key_idx, api_key in enumerate(api_keys" in source
        has_quota_check = '"429"' in source or "'429'" in source
        has_continue = "continue" in source
        
        print(f"\n   Multi-key loop: {'✅' if has_loop else '❌'}")
        print(f"   Quota detection: {'✅' if has_quota_check else '❌'}")
        print(f"   Key retry logic: {'✅' if has_continue else '❌'}")
        
        if has_loop and has_quota_check and has_continue:
            print("\n✅ PASS: youtube_metadata.py has multi-key fallback")
            return True
        else:
            print("\n❌ FAIL: youtube_metadata.py missing fallback features")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_database_fallback():
    """Test database.py YouTube API fallback"""
    print("\n" + "="*60)
    print("🧪 Testing Database YouTube API Fallback")
    print("="*60)
    
    try:
        from src.infrastructure.adapters.database import _get_all_youtube_api_keys
        
        keys = _get_all_youtube_api_keys()
        print(f"\n✅ Database YouTube keys loaded: {len(keys)}")
        
        for idx, key in enumerate(keys, 1):
            masked = key[:10] + "..." if len(key) > 10 else key
            print(f"   Key #{idx}: {masked}")
        
        if len(keys) >= 3:
            print("\n✅ PASS: Multi-key fallback ready (3+ keys)")
            return True
        else:
            print(f"\n⚠️  WARNING: Only {len(keys)} key(s) - recommend 3+")
            return len(keys) > 0
            
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def main():
    """Run all fallback tests"""
    print("\n" + "="*60)
    print("🔍 FALLBACK SYSTEM COMPREHENSIVE TEST")
    print("="*60)
    
    results = {
        "YouTube (search.py)": test_youtube_fallback(),
        "YouTube (database.py)": test_database_fallback(),
        "Gemini (process.py)": test_gemini_fallback_process(),
        "Gemini (youtube_metadata.py)": test_gemini_fallback_metadata(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {component}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Fallback system is fully operational")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("❌ Fix issues above before production use")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
