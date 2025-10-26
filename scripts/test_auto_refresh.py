#!/usr/bin/env python3
"""
اختبار التجديد التلقائي للتوكن
Test automatic token refresh in youtube_upload.py
"""

from pathlib import Path
import sys

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.youtube_upload import _get_service

def test_auto_refresh():
    """Test that _get_service auto-refreshes token"""
    
    print("="*70)
    print("🧪 Testing Automatic Token Refresh")
    print("="*70)
    
    client_secret = repo_root / "secrets" / "client_secret.json"
    token_file = repo_root / "secrets" / "token.json"
    
    print("\n[1/2] Checking files...")
    if not client_secret.exists():
        print(f"❌ client_secret.json not found: {client_secret}")
        return False
    if not token_file.exists():
        print(f"❌ token.json not found: {token_file}")
        return False
    
    print("✅ Files exist")
    
    print("\n[2/2] Attempting connection to YouTube API...")
    print("      (Will auto-refresh if token is expired)")
    print()
    
    try:
        # This will auto-refresh if token is expired
        service, MediaFileUpload = _get_service(client_secret, token_file, debug=True)
        
        print("\n" + "="*70)
        print("✅✅✅ SUCCESS! Connected successfully ✅✅✅")
        print("="*70)
        print("\n📊 Result:")
        print("   • Service is ready to use")
        print("   • Token is valid (auto-refreshed if expired)")
        print("   • You can upload videos now without issues")
        
        # Quick API test
        print("\n🔍 Quick API test...")
        try:
            request = service.channels().list(part="snippet", mine=True)
            response = request.execute()
            channel_title = response.get("items", [{}])[0].get("snippet", {}).get("title", "Unknown")
            print(f"✅ Your channel: {channel_title}")
        except Exception as e:
            print(f"⚠️  Quick test failed: {e}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print("\n" + "="*70)
        print("❌ Connection failed")
        print("="*70)
        print(f"\n⚠️  Error: {error_msg}")
        
        if "No such file" in error_msg or "does not exist" in error_msg:
            print("\n💡 Problem: Missing file")
            print("   Make sure secrets/client_secret.json and secrets/token.json exist")
        elif "invalid_grant" in error_msg.lower():
            print("\n💡 Problem: refresh_token is invalid")
            print("   Solution: Delete secrets/token.json and re-authenticate")
        
        return False


if __name__ == "__main__":
    try:
        success = test_auto_refresh()
        
        print("\n" + "="*70)
        if success:
            print("🎉 Auto-refresh works correctly!")
        else:
            print("⚠️  Test failed - check messages above")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
