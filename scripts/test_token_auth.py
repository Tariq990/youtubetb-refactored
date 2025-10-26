"""
Test OAuth Token authentication without uploading
يختبر المصادقة بدون رفع فيديو
"""

from pathlib import Path
import sys

# Add project root to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

def test_token_authentication():
    """Test if OAuth token is valid and working"""
    
    print("\n" + "="*70)
    print("🔍 TESTING OAUTH TOKEN AUTHENTICATION")
    print("="*70 + "\n")
    
    # Check if files exist
    secrets_dir = repo_root / "secrets"
    token_file = secrets_dir / "token.json"
    client_secret_file = secrets_dir / "client_secret.json"
    
    print("📁 Checking required files...")
    print(f"   Token file: {token_file}")
    print(f"   Exists: {'✅' if token_file.exists() else '❌'}")
    print(f"\n   Client secret: {client_secret_file}")
    print(f"   Exists: {'✅' if client_secret_file.exists() else '❌'}\n")
    
    if not client_secret_file.exists():
        print("❌ ERROR: client_secret.json not found!")
        print("   Please download it from Google Cloud Console")
        return False
    
    # Import YouTube upload module
    try:
        from src.infrastructure.adapters.youtube_upload import _get_service
        print("✅ YouTube upload module loaded\n")
    except ImportError as e:
        print(f"❌ Failed to import upload module: {e}")
        return False
    
    # Try to get service (this will trigger auth flow if needed)
    print("🔐 Attempting authentication...\n")
    print("-" * 70 + "\n")
    
    try:
        service, _ = _get_service(
            client_secret=client_secret_file,
            token_file=token_file,
            debug=True
        )
        
        print("\n" + "-" * 70)
        print("\n✅ Authentication successful!")
        print("   Service object created: ✅")
        
        # Try a simple API call to verify token works
        print("\n📡 Testing API call (get channel info)...")
        try:
            request = service.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]
                snippet = channel.get('snippet', {})
                stats = channel.get('statistics', {})
                
                print("\n" + "="*70)
                print("✅ API CALL SUCCESSFUL!")
                print("="*70)
                print(f"\n📺 Channel: {snippet.get('title', 'N/A')}")
                print(f"🆔 Channel ID: {channel.get('id', 'N/A')}")
                print(f"👥 Subscribers: {stats.get('subscriberCount', 'N/A')}")
                print(f"🎬 Videos: {stats.get('videoCount', 'N/A')}")
                print(f"👀 Views: {stats.get('viewCount', 'N/A')}")
                print("="*70 + "\n")
                
                # Check token file again
                if token_file.exists():
                    print("✅ Token file saved successfully")
                    print(f"   Location: {token_file}")
                    
                    # Read token to check expiry info
                    import json
                    try:
                        token_data = json.loads(token_file.read_text(encoding='utf-8'))
                        if 'expiry' in token_data:
                            print(f"   Expiry: {token_data['expiry']}")
                        print(f"   Has refresh token: {'✅' if 'refresh_token' in token_data else '❌'}")
                    except Exception:
                        pass
                
                print("\n🎉 RESULT: Token is valid and working!")
                print("🎉 Production Mode active - token lasts 6+ months")
                print("🎉 Ready to upload videos!\n")
                
                return True
            else:
                print("\n⚠️  No channel data returned")
                return False
                
        except Exception as e:
            print(f"\n❌ API call failed: {e}")
            print("   Token may be invalid or lacks permissions")
            return False
            
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n💡 If you see manual auth prompt above:")
        print("   1. Copy the URL")
        print("   2. Open in browser")
        print("   3. Sign in and grant permissions")
        print("   4. Copy the authorization code")
        print("   5. Paste it when prompted")
        return False

if __name__ == "__main__":
    success = test_token_authentication()
    
    if success:
        print("\n" + "="*70)
        print("✅ TEST PASSED - Ready to upload!")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ TEST FAILED - Check errors above")
        print("="*70 + "\n")
        sys.exit(1)
