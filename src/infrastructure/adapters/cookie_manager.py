"""
Cookie Manager - Test and manage YouTube cookies
Provides interactive guidance for obtaining fresh cookies
"""

import time
from pathlib import Path
from typing import Optional, Tuple

# Get repository root
REPO_ROOT = Path(__file__).parent.parent.parent.parent


def find_cookies_file() -> Optional[Path]:
    """
    Find cookies.txt file in expected locations.
    
    Returns:
        Path to cookies.txt if found, None otherwise
    """
    candidates = [
        REPO_ROOT / "secrets" / "cookies.txt",
        REPO_ROOT / "cookies.txt"
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None


def validate_cookies_content(cookies_path: Path) -> Tuple[bool, str]:
    """
    Validate cookies file content.
    
    Args:
        cookies_path: Path to cookies.txt file
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        content = cookies_path.read_text(encoding='utf-8').strip()
        
        # Check if file is empty
        if not content:
            return False, "File is empty"
        
        # Check minimum size (valid cookies file should be > 1KB)
        if len(content) < 1024:
            return False, f"File too small ({len(content)} bytes, expected > 1KB)"
        
        # Check for Netscape format header
        if not content.startswith('# Netscape HTTP Cookie File') and \
           not content.startswith('# HTTP Cookie File'):
            return False, "Not in Netscape cookie format"
        
        # Count cookie lines (lines not starting with #)
        cookie_lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        if len(cookie_lines) < 5:
            return False, f"Too few cookies ({len(cookie_lines)} found, expected > 5)"
        
        # Check for YouTube domains
        youtube_cookies = [line for line in cookie_lines if 'youtube.com' in line or 'google.com' in line]
        
        if len(youtube_cookies) < 3:
            return False, f"No YouTube/Google cookies found ({len(youtube_cookies)} found)"
        
        return True, f"Valid cookies file with {len(cookie_lines)} cookies"
        
    except Exception as e:
        return False, f"Error reading file: {e}"


def test_cookies_with_ytdlp(cookies_path: Path, test_video_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ") -> Tuple[bool, str]:
    """
    Test cookies by attempting to extract video info with yt-dlp.
    
    Args:
        cookies_path: Path to cookies.txt file
        test_video_url: YouTube video URL to test with
        
    Returns:
        Tuple of (success, message)
    """
    try:
        from yt_dlp import YoutubeDL
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': str(cookies_path),
            'extract_flat': True,  # Don't download, just extract info
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_video_url, download=False)
            
            if info and 'title' in info:
                return True, f"Cookies work! Successfully accessed: {info['title']}"
            else:
                return False, "Could not extract video info"
                
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for common error patterns
        if 'sign in' in error_msg or 'login' in error_msg:
            return False, "Cookies expired or invalid - YouTube requires login"
        elif 'age' in error_msg or 'restricted' in error_msg:
            return False, "Age-restricted video - cookies may not have proper permissions"
        elif 'private' in error_msg:
            return False, "Private video - normal behavior (cookies are OK)"
        else:
            return False, f"Error testing cookies: {e}"


def print_cookie_instructions():
    """Print detailed instructions for obtaining fresh cookies."""
    
    print("\n" + "="*70)
    print(" HOW TO GET FRESH COOKIES.TXT FROM YOUR BROWSER")
    print("="*70)
    
    print("\n[STEP 1] Install Browser Extension")
    print("-" * 70)
    print("Chrome/Edge:")
    print("  https://chrome.google.com/webstore/detail/get-cookiestxt/")
    print("  bgaddhkoddajcdgocldbbfleckgcbcid")
    print("\nFirefox:")
    print("  https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/")
    
    print("\n[STEP 2] Login to YouTube")
    print("-" * 70)
    print("1. Open YouTube in your browser")
    print("2. Make sure you're logged in")
    print("3. Watch a video or two (to activate cookies)")
    
    print("\n[STEP 3] Export Cookies")
    print("-" * 70)
    print("1. While on YouTube.com, click the extension icon")
    print("2. Click 'Export' or 'Download'")
    print("3. Save the file as 'cookies.txt'")
    
    print("\n[STEP 4] Place Cookie File")
    print("-" * 70)
    print(f"Place cookies.txt in ONE of these locations:")
    print(f"  Option 1 (recommended): {REPO_ROOT / 'secrets' / 'cookies.txt'}")
    print(f"  Option 2: {REPO_ROOT / 'cookies.txt'}")
    
    print("\n[IMPORTANT NOTES]")
    print("-" * 70)
    print("[!] Cookies are machine-specific - export fresh on each computer")
    print("[!] Cookies expire after ~30 days - re-export monthly")
    print("[!] Must be in Netscape format (extension handles this)")
    print("[!] File should be > 1KB in size")
    
    print("\n" + "="*70 + "\n")


def interactive_cookie_setup() -> bool:
    """
    Interactive cookie setup guide.
    Walks user through obtaining and placing cookies.
    
    Returns:
        True if cookies are now valid, False otherwise
    """
    print("\n" + "="*70)
    print(" COOKIES.TXT SETUP WIZARD")
    print("="*70)
    
    # Check if cookies already exist
    existing_cookies = find_cookies_file()
    
    if existing_cookies:
        print(f"\n[FOUND] Cookies file exists at: {existing_cookies}")
        
        # Validate content
        is_valid, message = validate_cookies_content(existing_cookies)
        print(f"[VALIDATION] {message}")
        
        if is_valid:
            # Test with YouTube
            print("\n[TESTING] Testing cookies with YouTube...")
            success, test_message = test_cookies_with_ytdlp(existing_cookies)
            print(f"[RESULT] {test_message}")
            
            if success:
                print("\n[SUCCESS] Cookies are working perfectly!")
                return True
            else:
                print("\n[ISSUE] Cookies file exists but doesn't work with YouTube")
                print("        This usually means cookies have expired or are invalid")
        else:
            print("\n[ISSUE] Cookies file is invalid or corrupted")
    else:
        print("\n[NOT FOUND] No cookies.txt file found")
    
    # Cookies don't exist or don't work - show instructions
    print("\nYou need to obtain fresh cookies from your browser.")
    print_cookie_instructions()
    
    # Wait for user to get cookies
    print("\n" + "="*70)
    print("Please follow the steps above to get cookies.txt")
    print("="*70)
    
    try:
        input("\nPress ENTER after you've placed cookies.txt in the correct location...")
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Setup cancelled by user")
        return False
    
    # Check again after user claims to have added cookies
    print("\n[CHECKING] Verifying cookies.txt...")
    new_cookies = find_cookies_file()
    
    if not new_cookies:
        print("[FAILED] Still no cookies.txt found")
        print(f"         Please place it in: {REPO_ROOT / 'secrets' / 'cookies.txt'}")
        return False
    
    # Validate new cookies
    is_valid, message = validate_cookies_content(new_cookies)
    print(f"[VALIDATION] {message}")
    
    if not is_valid:
        print("[FAILED] Cookies file is invalid")
        return False
    
    # Test new cookies
    print("\n[TESTING] Testing new cookies with YouTube...")
    success, test_message = test_cookies_with_ytdlp(new_cookies)
    print(f"[RESULT] {test_message}")
    
    if success:
        print("\n[SUCCESS] Cookies setup complete and working!")
        return True
    else:
        print("\n[FAILED] Cookies still don't work")
        print("         Try exporting fresh cookies again")
        print("         Make sure you're logged into YouTube first")
        return False


def check_cookies_status(verbose: bool = True) -> Tuple[bool, str]:
    """
    Quick check of cookies status.
    
    Args:
        verbose: Print detailed status
        
    Returns:
        Tuple of (cookies_valid, status_message)
    """
    cookies_path = find_cookies_file()
    
    if not cookies_path:
        msg = "No cookies.txt found"
        if verbose:
            print(f"[Cookies] {msg}")
        return False, msg
    
    is_valid, validation_msg = validate_cookies_content(cookies_path)
    
    if not is_valid:
        msg = f"Invalid cookies: {validation_msg}"
        if verbose:
            print(f"[Cookies] {msg}")
        return False, msg
    
    # Test with YouTube
    success, test_msg = test_cookies_with_ytdlp(cookies_path)
    
    if success:
        msg = f"Cookies OK: {cookies_path.name}"
        if verbose:
            print(f"[Cookies] {msg}")
        return True, msg
    else:
        msg = f"Cookies don't work: {test_msg}"
        if verbose:
            print(f"[Cookies] {msg}")
        return False, msg


def main():
    """Main function for testing cookie manager."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        # Interactive setup
        success = interactive_cookie_setup()
        sys.exit(0 if success else 1)
    else:
        # Quick status check
        valid, message = check_cookies_status(verbose=True)
        
        if not valid:
            print("\nRun with 'setup' argument for interactive guide:")
            print(f"  python -m {__name__.replace('.', '/')} setup")
        
        sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
