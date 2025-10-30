"""
Comprehensive API and Requirements Checker
Tests all APIs and dependencies before pipeline execution
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

console = Console()


def check_gemini_api() -> Tuple[bool, str]:
    """Test Gemini API with actual API call"""
    try:
        import google.generativeai as genai

        # Load API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            env_path = Path("secrets/.env")
            if env_path.exists():
                load_dotenv(env_path)
                api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return False, "❌ GEMINI_API_KEY not found in environment or secrets/.env"

        # Test actual API call
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Simple test prompt
        response = model.generate_content("Say 'OK' if you can read this.")

        if response and response.text:
            return True, f"✅ Gemini API working (model: gemini-2.5-flash)"
        else:
            return False, "❌ Gemini API responded but no text returned"

    except ImportError:
        return False, "❌ google-generativeai package not installed"
    except Exception as e:
        return False, f"❌ Gemini API test failed: {str(e)[:100]}"


def check_pexels_api() -> Tuple[bool, str]:
    """Test Pexels API with actual API call (with multi-file fallback)"""
    try:
        import requests

        # ===== PEXELS API KEY FALLBACK SYSTEM =====
        api_key = None
        
        # Priority 1: Environment variable
        api_key = os.getenv("PEXELS_API_KEY")
        
        if not api_key:
            # Priority 2-6: Check multiple locations
            repo_root = Path(__file__).resolve().parents[3]
            api_key_paths = [
                repo_root / "secrets" / ".env",           # Priority 2: Main .env
                repo_root / "secrets" / "pexels_key.txt", # Priority 3: Dedicated file
                repo_root / "secrets" / "api_keys.txt",   # Priority 4: Shared keys
                repo_root / "secrets" / "api_key.txt",    # Priority 5: Legacy
                repo_root / ".env"                        # Priority 6: Root .env
            ]
            
            for key_path in api_key_paths:
                if key_path.exists():
                    try:
                        content = key_path.read_text(encoding="utf-8").strip()
                        
                        # Handle .env format
                        if key_path.name.endswith('.env'):
                            for line in content.splitlines():
                                if line.strip().startswith("PEXELS_API_KEY="):
                                    api_key = line.split("=", 1)[1].strip()
                                    break
                        
                        # Handle plain text format
                        else:
                            for line in content.splitlines():
                                line = line.strip()
                                if line and not line.startswith("#") and len(line) > 20:
                                    api_key = line
                                    break
                        
                        if api_key:
                            break
                    except Exception:
                        continue

        if not api_key:
            return False, "❌ PEXELS_API_KEY not found (env or secrets/.env or secrets/pexels_key.txt)"

        # Test actual API call
        headers = {"Authorization": api_key}
        response = requests.get(
            "https://api.pexels.com/videos/search?query=nature&per_page=1",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "videos" in data:
                return True, f"✅ Pexels API working ({len(data.get('videos', []))} videos found)"
            else:
                return False, "❌ Pexels API responded but no videos data"
        elif response.status_code == 401:
            return False, "❌ Pexels API key invalid (401 Unauthorized)"
        else:
            return False, f"❌ Pexels API error: {response.status_code}"

    except ImportError:
        return False, "❌ requests package not installed"
    except Exception as e:
        return False, f"❌ Pexels API test failed: {str(e)[:100]}"


def check_youtube_api() -> Tuple[bool, str]:
    """Check YouTube Data API key"""
    try:
        # Load API key
        api_key = os.getenv("YT_API_KEY")
        if not api_key:
            env_path = Path("secrets/.env")
            if env_path.exists():
                load_dotenv(env_path)
                api_key = os.getenv("YT_API_KEY")

        if not api_key:
            return False, "❌ YT_API_KEY not found in environment or secrets/.env"

        # Test actual API call (search endpoint)
        import requests
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": api_key,
            "q": "test",
            "part": "snippet",
            "type": "video",
            "maxResults": 1
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                return True, "✅ YouTube Data API working"
            else:
                return False, "❌ YouTube API responded but no items"
        elif response.status_code == 403:
            return False, "❌ YouTube API key invalid or quota exceeded (403)"
        elif response.status_code == 400:
            return False, "❌ YouTube API key invalid (400)"
        else:
            return False, f"❌ YouTube API error: {response.status_code}"

    except Exception as e:
        return False, f"❌ YouTube API test failed: {str(e)[:100]}"


def check_youtube_oauth() -> Tuple[bool, str]:
    """Check YouTube OAuth credentials"""
    try:
        secrets_dir = Path("secrets")

        # Check client_secret.json
        client_secret = secrets_dir / "client_secret.json"
        if not client_secret.exists():
            return False, "❌ secrets/client_secret.json not found"

        # Check if token.json exists (optional, will be created on first upload)
        token_json = secrets_dir / "token.json"
        if token_json.exists():
            return True, "✅ YouTube OAuth configured (client_secret.json + token.json)"
        else:
            return True, "⚠️ YouTube OAuth partially configured (token.json will be created on first upload)"

    except Exception as e:
        return False, f"❌ OAuth check failed: {str(e)[:100]}"


def check_google_books_api() -> Tuple[bool, str]:
    """Check Google Books API key (optional)"""
    try:
        api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or os.getenv("GBOOKS_API_KEY")
        if not api_key:
            env_path = Path("secrets/.env")
            if env_path.exists():
                load_dotenv(env_path)
                api_key = os.getenv("GOOGLE_BOOKS_API_KEY") or os.getenv("GBOOKS_API_KEY")

        if not api_key:
            return True, "⚠️ Google Books API key not set (optional, uses free tier)"

        # Test actual API call
        import requests
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            "q": "test",
            "key": api_key,
            "maxResults": 1
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            return True, "✅ Google Books API working (higher quota)"
        elif response.status_code == 400:
            return False, "❌ Google Books API key invalid"
        else:
            return True, f"⚠️ Google Books API error: {response.status_code} (fallback to free tier)"

    except Exception as e:
        return True, f"⚠️ Google Books check failed (fallback available): {str(e)[:50]}"


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if FFmpeg is installed and accessible"""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Extract version
            version_line = result.stdout.split('\n')[0]
            return True, f"✅ {version_line[:50]}"
        else:
            return False, "❌ FFmpeg found but returned error"

    except FileNotFoundError:
        return False, "❌ FFmpeg not found in PATH"
    except Exception as e:
        return False, f"❌ FFmpeg check failed: {str(e)[:100]}"


def check_playwright() -> Tuple[bool, str]:
    """Check if Playwright is installed"""
    try:
        from playwright.sync_api import sync_playwright

        # Try to launch browser (quick test)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()

        return True, "✅ Playwright installed and browser ready"

    except ImportError:
        return False, "❌ playwright package not installed"
    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg:
            return False, "❌ Playwright browsers not installed (run: python -m playwright install)"
        else:
            return False, f"❌ Playwright test failed: {error_msg[:100]}"


def check_python_packages() -> Tuple[bool, str]:
    """Check if all required Python packages are installed"""
    package_imports = {
        "google-generativeai": "google.generativeai",
        "requests": "requests",
        "playwright": "playwright",
        "pillow": "PIL",
        "edge-tts": "edge_tts",
        "yt-dlp": "yt_dlp",
        "rich": "rich",
        "typer": "typer",
        "python-dotenv": "dotenv",
        "mutagen": "mutagen"
    }

    missing = []
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        return False, f"❌ Missing packages: {', '.join(missing)}"
    else:
        return True, f"✅ All {len(package_imports)} required packages installed"


def check_fonts() -> Tuple[bool, str]:
    """Check if required fonts are installed"""
    try:
        from PIL import ImageFont

        # Try to load Bebas Neue (critical font)
        try:
            font = ImageFont.truetype("Bebas Neue", 50)
            return True, "✅ Bebas Neue font installed"
        except OSError:
            # Try alternative path
            font_path = Path("assets/fonts/BebasNeue-Regular.ttf")
            if font_path.exists():
                return True, "✅ Bebas Neue font found in assets/fonts/"
            else:
                return False, "❌ Bebas Neue font not found (required for thumbnails)"

    except ImportError:
        return False, "❌ PIL/Pillow not installed"
    except Exception as e:
        return False, f"❌ Font check failed: {str(e)[:100]}"


def check_config_files() -> Tuple[bool, str]:
    """Check if all required config files exist"""
    required_files = [
        "config/settings.json",
        "config/prompts.json",
        "config/template.html"
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        return False, f"❌ Missing config files: {', '.join(missing)}"
    else:
        return True, f"✅ All {len(required_files)} config files found"


def check_secrets_env() -> Tuple[bool, str]:
    """Check if secrets/.env exists and has basic keys"""
    env_path = Path("secrets/.env")

    if not env_path.exists():
        return False, "❌ secrets/.env not found"

    # Load and check for required keys
    load_dotenv(env_path)

    required_keys = ["GEMINI_API_KEY", "PEXELS_API_KEY", "YT_API_KEY"]
    missing_keys = []

    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        return False, f"❌ Missing keys in .env: {', '.join(missing_keys)}"
    else:
        return True, f"✅ secrets/.env exists with {len(required_keys)} required keys"


def run_all_checks(verbose: bool = True) -> Dict[str, Tuple[bool, str]]:
    """Run all checks and return results"""

    if verbose:
        console.print("\n" + "="*70)
        console.print(Panel.fit(
            "[bold cyan]🔍 API & Requirements Checker[/bold cyan]\n"
            "[dim]Testing all APIs and dependencies before pipeline execution[/dim]",
            border_style="cyan"
        ))
        console.print("="*70 + "\n")

    checks = {
        "Secrets File": check_secrets_env,
        "Python Packages": check_python_packages,
        "Config Files": check_config_files,
        "FFmpeg": check_ffmpeg,
        "Playwright": check_playwright,
        "Fonts": check_fonts,
        "Gemini API": check_gemini_api,
        "Pexels API": check_pexels_api,
        "YouTube Data API": check_youtube_api,
        "YouTube OAuth": check_youtube_oauth,
        "Google Books API": check_google_books_api,
    }

    results = {}

    for check_name, check_func in checks.items():
        if verbose:
            console.print(f"[cyan]Testing {check_name}...[/cyan]", end=" ")

        success, message = check_func()
        results[check_name] = (success, message)

        if verbose:
            console.print(message)

    return results


def print_summary(results: Dict[str, Tuple[bool, str]]) -> bool:
    """Print summary table and return overall status"""

    console.print("\n" + "="*70)

    table = Table(title="📊 Check Summary", box=None, show_header=True, header_style="bold cyan")
    table.add_column("Check", style="cyan", width=25)
    table.add_column("Status", width=45)

    critical_failed = []
    warnings = []
    passed = []

    for check_name, (success, message) in results.items():
        # Determine if critical
        is_critical = check_name in [
            "Secrets File", "Python Packages", "Config Files",
            "FFmpeg", "Gemini API", "Pexels API", "YouTube Data API"
        ]

        if success:
            if "⚠️" in message:
                warnings.append(check_name)
                table.add_row(check_name, f"[yellow]{message}[/yellow]")
            else:
                passed.append(check_name)
                table.add_row(check_name, f"[green]{message}[/green]")
        else:
            if is_critical:
                critical_failed.append(check_name)
                table.add_row(check_name, f"[red]{message}[/red]")
            else:
                warnings.append(check_name)
                table.add_row(check_name, f"[yellow]{message}[/yellow]")

    console.print(table)
    console.print("\n" + "="*70)

    # Print final verdict
    if critical_failed:
        console.print(Panel(
            f"[bold red]❌ CRITICAL FAILURES ({len(critical_failed)})[/bold red]\n\n"
            f"Failed checks: {', '.join(critical_failed)}\n\n"
            f"[dim]Pipeline cannot run until these are fixed.[/dim]",
            border_style="red",
            title="Status"
        ))
        return False
    elif warnings:
        console.print(Panel(
            f"[bold yellow]⚠️ WARNINGS ({len(warnings)})[/bold yellow]\n\n"
            f"[green]✅ Passed: {len(passed)}[/green]\n"
            f"[yellow]⚠️ Warnings: {len(warnings)}[/yellow]\n\n"
            f"[dim]Pipeline can run, but some features may be limited.[/dim]",
            border_style="yellow",
            title="Status"
        ))
        return True
    else:
        console.print(Panel(
            f"[bold green]🎉 ALL CHECKS PASSED ({len(passed)}/{len(results)})[/bold green]\n\n"
            f"[dim]All APIs and dependencies are ready!\n"
            f"Pipeline is fully operational.[/dim]",
            border_style="green",
            title="Status"
        ))
        return True


def main():
    """Main entry point for standalone execution"""
    results = run_all_checks(verbose=True)
    all_ok = print_summary(results)

    if not all_ok:
        sys.exit(1)
    else:
        console.print("\n✅ [green]Ready to run pipeline![/green]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
