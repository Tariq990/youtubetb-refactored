#!/usr/bin/env python3
"""
Script to generate and save YouTube OAuth token.
Run this once to authenticate and save credentials.
"""

from pathlib import Path
import os

# Add project root to path
import sys
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

def generate_token():
    """Generate YouTube OAuth token and save to secrets/token.json"""
    
    print("🔐 YouTube OAuth Token Generator")
    print("="*70)
    
    # Import required modules
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("❌ Missing required packages!")
        print("   Run: pip install google-auth-oauthlib google-auth google-api-python-client")
        return False
    
    # Define scopes
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
    ]
    
    # Locate client_secret.json
    secrets_dir = repo_root / "secrets"
    client_secret_file = secrets_dir / "client_secret.json"
    
    if not client_secret_file.exists():
        print(f"❌ Client secret file not found: {client_secret_file}")
        print("   Make sure secrets/client_secret.json exists")
        return False
    
    print(f"✓ Found client secret: {client_secret_file}")
    
    # Token output path
    token_file = secrets_dir / "token.json"
    
    # Check for environment variables (alternative method)
    client_id = os.environ.get("YT_CLIENT_ID") or os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret_env = os.environ.get("YT_CLIENT_SECRET") or os.environ.get("YOUTUBE_CLIENT_SECRET")
    
    try:
        if client_id and client_secret_env:
            print("✓ Using client credentials from environment variables")
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret_env,
                    "redirect_uris": ["http://localhost", "http://127.0.0.1"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "project_id": "yt-upload-client",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        else:
            print("✓ Using client_secret.json file")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
        
        # Set manual redirect URI (console-based flow)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print("\n" + "="*70)
        print("🔗 Please visit this URL to authorize the application:")
        print()
        print(auth_url)
        print()
        print("="*70)
        print()
        print("📌 Steps:")
        print("   1. Click the link above (or copy-paste to browser)")
        print("   2. Login to your Google/YouTube account")
        print("   3. Grant permissions when asked")
        print("   4. Copy the authorization code from the browser")
        print("   5. Paste it below")
        print()
        
        # Get authorization code from user
        code = input("📝 Enter the authorization code: ").strip()
        
        if not code:
            print("❌ No code entered!")
            return False
        
        print("\n⏳ Exchanging code for token...")
        
        # Exchange code for credentials
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save token to file
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")
        
        print()
        print("="*70)
        print("✅ SUCCESS! Token saved to:", token_file)
        print("="*70)
        print()
        print("📊 Token Details:")
        print(f"   - Expiry: {creds.expiry}")
        print(f"   - Has Refresh Token: {bool(creds.refresh_token)}")
        print(f"   - Scopes: {', '.join(creds.scopes)}")
        print()
        print("💡 This token will be automatically refreshed when it expires.")
        print("   You won't need to re-authenticate unless you revoke access.")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = generate_token()
        if success:
            print("✅ Token generation complete!")
            print("   You can now run the pipeline without re-authentication.")
        else:
            print("❌ Token generation failed!")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        exit(1)
