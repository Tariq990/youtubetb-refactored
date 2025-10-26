#!/usr/bin/env python3
"""
Comprehensive Test - Force token expiry and test auto-refresh
"""

from pathlib import Path
import json
from datetime import datetime, timedelta
import sys

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.youtube_upload import _get_service

def force_expire_token():
    """Make token expired (set expiry to past date)"""
    token_file = repo_root / "secrets" / "token.json"
    
    if not token_file.exists():
        print("❌ token.json does not exist")
        return False
    
    print("🔧 Modifying token expiry to past date...")
    
    # Read token
    with open(token_file, 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    
    # Backup original expiry
    original_expiry = token_data.get('expiry')
    print(f"   📅 Original expiry: {original_expiry}")
    
    # Set expiry to 1 hour ago
    past_time = datetime.now() - timedelta(hours=1)
    token_data['expiry'] = past_time.isoformat() + 'Z'
    
    print(f"   📅 New expiry (expired): {token_data['expiry']}")
    
    # Save modified token
    with open(token_file, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, indent=2)
    
    print("✅ Token modified to be expired")
    return original_expiry


def test_refresh_after_expiry():
    """Test that expired token gets refreshed automatically"""
    
    print("\n" + "="*70)
    print("🧪 Testing Auto-Refresh of Expired Token")
    print("="*70)
    
    client_secret = repo_root / "secrets" / "client_secret.json"
    token_file = repo_root / "secrets" / "token.json"
    
    # Step 1: Force expiry
    print("\n[1/3] Forcing token expiry...")
    original_expiry = force_expire_token()
    if not original_expiry:
        return False
    
    # Step 2: Try to get service (should auto-refresh)
    print("\n[2/3] Attempting connection to YouTube...")
    print("      (Should auto-refresh token)")
    print()
    
    try:
        service, _ = _get_service(client_secret, token_file, debug=True)
        
        print("\n" + "="*70)
        print("✅✅✅ Auto-Refresh Successful! ✅✅✅")
        print("="*70)
        
        # Step 3: Verify new token was saved
        print("\n[3/3] Verifying new token was saved...")
        with open(token_file, 'r', encoding='utf-8') as f:
            new_token = json.load(f)
        
        new_expiry = new_token.get('expiry')
        print(f"   📅 New expiry: {new_expiry}")
        
        # Parse and compare
        try:
            new_exp_dt = datetime.fromisoformat(new_expiry.replace('Z', '+00:00'))
            now = datetime.now(new_exp_dt.tzinfo)
            remaining = new_exp_dt - now
            
            if remaining.total_seconds() > 0:
                print(f"   ✅ Token valid for {int(remaining.total_seconds() / 60)} minutes")
                print("\n📊 Summary:")
                print("   ✅ Auto-refresh works correctly")
                print("   ✅ New token saved to file")
                print("   ✅ You won't be asked for authorization URL in the future")
                return True
            else:
                print("   ⚠️  New token is still expired!")
                return False
        except Exception as e:
            print(f"   ⚠️  Failed to parse date: {e}")
            return False
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ Auto-refresh failed")
        print("="*70)
        print(f"\n⚠️  Error: {e}")
        return False


if __name__ == "__main__":
    try:
        print("="*70)
        print("🔬 Comprehensive Auto-Refresh Test")
        print("="*70)
        print("\nThis test will:")
        print("  1. Make token expired")
        print("  2. Attempt connection to YouTube API")
        print("  3. Verify auto-refresh and save")
        
        input("\n⏸️  Press Enter to continue...")
        
        success = test_refresh_after_expiry()
        
        print("\n" + "="*70)
        if success:
            print("🎉 Test successful - Auto-refresh works perfectly!")
            print("   Now when uploading videos you won't be asked to authenticate")
        else:
            print("⚠️  Test failed - check messages above")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
