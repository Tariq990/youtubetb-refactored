#!/usr/bin/env python3
"""
فحص صلاحية التوكن - YouTube OAuth Token Validator
اختبار فوري لصلاحية التوكن وقدرته على التجديد
"""

import json
from pathlib import Path
from datetime import datetime

def test_token():
    """Comprehensive token validation"""
    print("="*70)
    print("🔍 YouTube OAuth Token Validator")
    print("="*70)
    
    # File paths
    repo_root = Path(__file__).resolve().parent.parent
    token_file = repo_root / "secrets" / "token.json"
    client_secret_file = repo_root / "secrets" / "client_secret.json"
    
    # 1. Check file exists
    print("\n[1/5] Checking token file existence...")
    if not token_file.exists():
        print("❌ token.json not found in secrets/")
        print(f"   Expected path: {token_file}")
        return False
    print("✅ File exists")
    
    # 2. Read token
    print("\n[2/5] Reading token data...")
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        print("✅ File read successfully")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return False
    
    # 3. Check token contents
    print("\n[3/5] Checking token contents...")
    required_fields = ['token', 'refresh_token', 'client_id', 'client_secret', 'expiry']
    missing_fields = [field for field in required_fields if field not in token_data]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    
    print("✅ All required fields present")
    print(f"   • Client ID: {token_data['client_id'][:20]}...")
    print(f"   • Refresh Token: {'Present ✅' if token_data['refresh_token'] else 'Missing ❌'}")
    
    # 4. Check expiry date
    print("\n[4/5] Checking expiry date...")
    try:
        expiry_str = token_data['expiry']
        # Parse ISO format: "2025-10-19T18:08:58Z"
        expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        now = datetime.now(expiry_date.tzinfo)
        
        print(f"   Expiry date: {expiry_str}")
        print(f"   Current time: {now.isoformat()}")
        
        if expiry_date < now:
            days_expired = (now - expiry_date).days
            hours_expired = (now - expiry_date).seconds // 3600
            print(f"❌ Token expired {days_expired} days and {hours_expired} hours ago")
            is_expired = True
        else:
            remaining = expiry_date - now
            print(f"✅ Token valid for {remaining.days} days and {remaining.seconds // 3600} hours")
            is_expired = False
    except Exception as e:
        print(f"⚠️  Failed to parse expiry date: {e}")
        is_expired = True
    
    # 5. Attempt actual refresh
    print("\n[5/5] Attempting actual token refresh...")
    print("      (This is the real test!)")
    
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        
        # Create credentials from file
        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data.get('scopes', [])
        )
        
        print("   📡 Connecting to Google servers...")
        print("   🔄 Attempting token refresh...")
        
        # Actual refresh attempt
        creds.refresh(Request())
        
        print("\n" + "="*70)
        print("✅✅✅ SUCCESS! Token refreshed successfully ✅✅✅")
        print("="*70)
        print("\n📊 Result:")
        print("   • Token is valid and can be auto-refreshed")
        print("   • refresh_token works correctly")
        print("   • No re-authentication needed")
        
        # Save updated token
        print("\n💾 Saving updated token...")
        updated_token = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }
        
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump(updated_token, f, indent=2)
        
        print("✅ New token saved to secrets/token.json")
        print(f"   Valid until: {creds.expiry.isoformat() if creds.expiry else 'Unknown'}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print("\n" + "="*70)
        print("❌❌❌ Token Refresh Failed ❌❌❌")
        print("="*70)
        print(f"\n⚠️  Failure reason: {error_msg}")
        
        # Error diagnosis
        print("\n🔍 Problem Diagnosis:")
        
        if 'invalid_grant' in error_msg.lower():
            print("   ❌ Problem: refresh_token has been revoked or expired")
            print("   📋 Solution:")
            print("      1. Delete secrets/token.json")
            print("      2. Run the program again")
            print("      3. You'll get an authorization URL")
            print("      4. Open URL, approve, and copy the code")
            
        elif 'invalid_client' in error_msg.lower():
            print("   ❌ Problem: client_id or client_secret is incorrect")
            print("   📋 Solution:")
            print("      1. Check secrets/client_secret.json")
            print("      2. Verify client_id and client_secret match Google Console")
            
        elif 'connection' in error_msg.lower() or 'network' in error_msg.lower():
            print("   ❌ Problem: Internet connection issue")
            print("   📋 Solution: Check your internet connection and try again")
            
        else:
            print("   ❌ Unexpected error")
            print("   📋 Suggested solution:")
            print("      1. Delete secrets/token.json")
            print("      2. Re-authenticate from scratch")
        
        return False


if __name__ == "__main__":
    try:
        success = test_token()
        
        print("\n" + "="*70)
        if success:
            print("🎉 Summary: Token works correctly!")
            print("   You can upload videos without issues now")
        else:
            print("⚠️  Summary: Re-authentication required")
            print("   Run the program and follow authentication steps")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
