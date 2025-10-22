"""
Comprehensive Validation Module - Verify all requirements before processing
Checks: APIs, System Tools, Python Packages, Cookies, Secrets
"""
import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.table import Table
import requests

# Suppress Google API warnings (STDERR noise from absl and grpc)
import warnings
warnings.filterwarnings('ignore')

# Redirect STDERR temporarily during import to suppress Google warnings
_original_stderr = sys.stderr
try:
    sys.stderr = open(os.devnull, 'w')
    import google.generativeai as genai  # type: ignore
finally:
    sys.stderr.close()
    sys.stderr = _original_stderr

console = Console()


class APIValidator:
    """Comprehensive validation of all pipeline requirements"""

    def __init__(self, quiet: bool = False):
        self.results: Dict[str, Tuple[bool, str]] = {}
        self.quiet = quiet  # Quiet mode for minimal output
        self._load_env()

    def _load_env(self):
        """Load environment variables from secrets/.env"""
        env_file = Path("secrets/.env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

    # ==================== SYSTEM TOOLS VALIDATION ====================

    def validate_ffmpeg(self) -> Tuple[bool, str]:
        """Check if FFmpeg is installed and accessible"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split('\n')[0]
                version = version_line.split('version')[1].split()[0] if 'version' in version_line else 'unknown'
                return True, f"✅ Installed (v{version})"
            else:
                return False, "❌ FFmpeg found but not working"
        except FileNotFoundError:
            return False, "❌ Not found - Install FFmpeg and add to PATH"
        except subprocess.TimeoutExpired:
            return False, "⚠️ Timeout - FFmpeg may be hanging"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def validate_playwright(self) -> Tuple[bool, str]:
        """Check if Playwright is installed with Chromium browser"""
        try:
            # Check if playwright package is installed
            import playwright

            # Check if chromium is installed
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                    return True, "✅ Installed with Chromium browser"
                except Exception as e:
                    if 'Executable doesn\'t exist' in str(e):
                        return False, "❌ Chromium not installed - Run: playwright install chromium"
                    else:
                        return False, f"⚠️ Issue: {str(e)[:50]}"
        except ImportError:
            return False, "❌ Playwright not installed - Run: pip install playwright"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"

    def validate_yt_dlp(self) -> Tuple[bool, str]:
        """Check if yt-dlp is installed"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"✅ Installed (v{version})"
            else:
                return False, "❌ yt-dlp found but not working"
        except FileNotFoundError:
            return False, "❌ Not found - Run: pip install yt-dlp"
        except subprocess.TimeoutExpired:
            return False, "⚠️ Timeout checking yt-dlp"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    # ==================== PYTHON PACKAGES VALIDATION ====================

    def validate_required_packages(self) -> Tuple[bool, str]:
        """Check if all required Python packages are installed"""
        required_packages = [
            'requests',
            'google.generativeai',
            'rich',
            'typer',
            'playwright',
            'PIL',  # Pillow imports as PIL
            'edge_tts',
            'mutagen',
            'pydub',
        ]

        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
            except ImportError:
                missing.append(package)

        if missing:
            return False, f"❌ Missing: {', '.join(missing)}"
        else:
            return True, f"✅ All {len(required_packages)} packages installed"

    # ==================== FILES & SECRETS VALIDATION ====================

    def validate_cookies_file(self) -> Tuple[bool, str]:
        """Check if cookies.txt exists for age/geo-restricted videos"""
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            size = cookies_path.stat().st_size
            if size > 0:
                return True, f"✅ Found ({size} bytes)"
            else:
                return False, "⚠️ File exists but is empty"
        else:
            return False, "⚠️ Not found (optional but recommended for restricted videos)"

    def validate_secrets_folder(self) -> Tuple[bool, str]:
        """Check if secrets folder and required files exist"""
        secrets_path = Path("secrets")
        if not secrets_path.exists():
            return False, "❌ secrets/ folder not found"

        required_files = {
            '.env': 'Environment variables',
            'client_secret.json': 'YouTube OAuth config',
        }

        missing = []
        found = []
        for file, desc in required_files.items():
            file_path = secrets_path / file
            if file_path.exists():
                found.append(file)
            else:
                missing.append(f"{file} ({desc})")

        if missing:
            return False, f"⚠️ Missing: {', '.join(missing)}"
        else:
            return True, f"✅ All required files present ({', '.join(found)})"

    def validate_template_html(self) -> Tuple[bool, str]:
        """Check if template.html exists with required IDs"""
        template_path = Path("config/template.html")
        if not template_path.exists():
            return False, "❌ config/template.html not found"

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            required_ids = [
                'video-preview-container',
                'top-title-input',
                'main-title-input',
                'subtitle-input',
                'footer-input'
            ]

            missing = [id for id in required_ids if f'id="{id}"' not in content and f"id='{id}'" not in content]

            if missing:
                return False, f"❌ Missing IDs: {', '.join(missing)}"
            else:
                return True, f"✅ Valid with all {len(required_ids)} required IDs"
        except Exception as e:
            return False, f"❌ Error reading: {str(e)}"

    # ==================== API KEYS VALIDATION ====================

    def validate_youtube_api(self) -> Tuple[bool, str]:
        """Validate YouTube Data API v3"""
        api_key = os.getenv('YT_API_KEY')

        if not api_key:
            return False, "❌ API key not found in environment"

        try:
            # Test with a simple search query
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': 'test',
                'maxResults': 1,
                'key': api_key
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return True, "✅ Valid - Working"
            elif response.status_code == 403:
                error_data = response.json()
                reason = error_data.get('error', {}).get('errors', [{}])[0].get('reason', 'Unknown')
                if reason == 'quotaExceeded':
                    return False, "⚠️ Quota exceeded - Wait or use another key"
                else:
                    return False, f"❌ Access denied: {reason}"
            else:
                return False, f"❌ HTTP {response.status_code}"

        except Exception as e:
            return False, f"❌ Connection error: {str(e)[:50]}"

    def validate_gemini_api(self) -> Tuple[bool, str]:
        """Validate Google Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            return False, "❌ API key not found in environment"

        try:
            genai.configure(api_key=api_key)  # type: ignore
            # Use latest stable Gemini model (gemini-2.0-flash)
            model = genai.GenerativeModel('gemini-2.0-flash')  # type: ignore

            # Test with a simple prompt
            response = model.generate_content("Say 'OK' if you receive this.")

            if response.text:
                return True, "✅ Valid - Working"
            else:
                return False, "❌ No response from API"

        except Exception as e:
            error_msg = str(e).lower()
            if 'api key' in error_msg or 'invalid' in error_msg:
                return False, "❌ Invalid API key"
            elif 'quota' in error_msg:
                return False, "⚠️ Quota exceeded"
            elif 'not found' in error_msg or '404' in error_msg:
                return False, "❌ Model not available - Check API access"
            else:
                return False, f"❌ Error: {str(e)[:50]}"

    def validate_google_books_api(self) -> Tuple[bool, str]:
        """Validate Google Books API (optional but recommended)"""
        api_key = os.getenv('GOOGLE_BOOKS_API_KEY') or os.getenv('GBOOKS_API_KEY')

        if not api_key:
            return True, "⚠️ Optional - Not configured (will use lower quota)"

        try:
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                'q': 'test',
                'maxResults': 1,
                'key': api_key
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return True, "✅ Valid - Higher quota enabled"
            else:
                return True, f"⚠️ Key invalid but optional (HTTP {response.status_code})"

        except Exception as e:
            return True, f"⚠️ Error but optional: {str(e)[:40]}"

    def validate_pexels_api(self) -> Tuple[bool, str]:
        """Validate Pexels API for Shorts"""
        api_key = os.getenv('PEXELS_API_KEY')

        if not api_key:
            return False, "❌ API key not found (required for Shorts)"

        try:
            url = "https://api.pexels.com/videos/search"
            headers = {'Authorization': api_key}
            params = {'query': 'nature', 'per_page': 1}

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                return True, "✅ Valid - Working"
            elif response.status_code == 401:
                return False, "❌ Invalid API key"
            else:
                return False, f"❌ HTTP {response.status_code}"

        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"

    def validate_youtube_oauth(self) -> Tuple[bool, str]:
        """Validate YouTube OAuth credentials"""
        client_id = os.getenv('YT_CLIENT_ID')
        client_secret = os.getenv('YT_CLIENT_SECRET')

        if not client_id or not client_secret:
            return False, "❌ OAuth credentials not found"

        # Check if token.json exists
        token_file = Path("secrets/token.json")
        if token_file.exists():
            return True, "✅ OAuth configured with saved token"
        else:
            return True, "⚠️ Credentials OK but needs first-time auth"

    def validate_all(self) -> bool:
        """
        Comprehensive validation of ALL pipeline requirements

        Validates:
        - System tools (FFmpeg, Playwright, yt-dlp)
        - Python packages (all requirements.txt)
        - Required files (cookies.txt, secrets/, template.html)
        - API keys (YouTube, Gemini, Pexels, OAuth, Google Books)

        Returns:
            bool: True if all critical checks pass
        """
        # Only show headers if not in quiet mode
        if not self.quiet:
            console.print("\n[bold cyan]🔍 Comprehensive Pipeline Validation[/bold cyan]")
            console.print("[dim]Checking system tools, packages, files, and API keys...[/dim]\n")

        # ========== SECTION 1: SYSTEM TOOLS ==========
        if not self.quiet:
            console.print("[bold yellow]📦 System Tools[/bold yellow]")
        system_tools = {
            'FFmpeg': self.validate_ffmpeg,
            'Playwright': self.validate_playwright,
            'yt-dlp': self.validate_yt_dlp,
        }

        for tool_name, validator in system_tools.items():
            success, message = validator()
            self.results[tool_name] = (success, message)

        # ========== SECTION 2: PYTHON PACKAGES ==========
        if not self.quiet:
            console.print("\n[bold yellow]🐍 Python Packages[/bold yellow]")
        success, message = self.validate_required_packages()
        self.results['Required Packages'] = (success, message)

        # ========== SECTION 3: FILES & SECRETS ==========
        if not self.quiet:
            console.print("\n[bold yellow]📁 Files & Configuration[/bold yellow]")
        file_checks = {
            'Secrets Folder': self.validate_secrets_folder,
            'Cookies File': self.validate_cookies_file,
            'Template HTML': self.validate_template_html,
        }

        for check_name, validator in file_checks.items():
            success, message = validator()
            self.results[check_name] = (success, message)

        # ========== SECTION 4: API KEYS ==========
        if not self.quiet:
            console.print("\n[bold yellow]🔐 API Keys[/bold yellow]")

        # Critical APIs (must pass)
        critical_apis = {
            'YouTube Data API': self.validate_youtube_api,
            'Gemini AI API': self.validate_gemini_api,
            'Pexels API': self.validate_pexels_api,
            'YouTube OAuth': self.validate_youtube_oauth,
        }

        # Optional APIs
        optional_apis = {
            'Google Books API': self.validate_google_books_api,
        }

        # Validate critical APIs
        critical_failed = []
        for api_name, validator in critical_apis.items():
            success, message = validator()
            self.results[api_name] = (success, message)

            if not success:
                critical_failed.append(api_name)

        # Validate optional APIs
        for api_name, validator in optional_apis.items():
            success, message = validator()
            self.results[api_name] = (success, message)

        # ========== DISPLAY RESULTS TABLE (only if not quiet) ==========
        if not self.quiet:
            self._display_results()

        # ========== DETERMINE OVERALL STATUS ==========
        # Critical items that MUST pass
        critical_items = [
            'FFmpeg',
            'Playwright',
            'yt-dlp',
            'Required Packages',
            'Secrets Folder',
            'Template HTML',
            'YouTube Data API',
            'Gemini AI API',
            'Pexels API',
            'YouTube OAuth',
        ]

        # Warning items (recommended but not critical)
        warning_items = [
            'Cookies File',
            'Google Books API',
        ]

        # Check critical failures
        failed_critical = []
        for item in critical_items:
            if item in self.results:
                success, _ = self.results[item]
                if not success:
                    failed_critical.append(item)

        # Check warnings
        warnings = []
        for item in warning_items:
            if item in self.results:
                success, msg = self.results[item]
                if not success and '⚠️' in msg:
                    warnings.append(item)

        # Display final verdict
        if failed_critical:
            if not self.quiet:
                console.print(f"\n[bold red]❌ VALIDATION FAILED - Critical issues found![/bold red]")
                console.print(f"[yellow]Failed critical checks: {', '.join(failed_critical)}[/yellow]")
                console.print("[dim]Fix these issues before running the pipeline.[/dim]\n")
            return False
        elif warnings:
            if not self.quiet:
                console.print(f"\n[bold yellow]⚠️ VALIDATION PASSED with warnings[/bold yellow]")
                console.print(f"[dim]Warnings: {', '.join(warnings)}[/dim]")
                console.print("[green]✅ All critical checks passed - Safe to proceed[/green]\n")
            return True
        else:
            if not self.quiet:
                console.print(f"\n[bold green]✅ PERFECT! All validations passed successfully![/bold green]")
                console.print("[dim]System is fully ready for pipeline execution.[/dim]\n")
            return True

    def _display_results(self):
        """Display validation results in a formatted table"""
        table = Table(title="🔍 Comprehensive Validation Results", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=25)
        table.add_column("Status", width=60)

        for component_name, (success, message) in self.results.items():
            status_style = "green" if success else ("yellow" if "⚠️" in message else "red")
            table.add_row(component_name, f"[{status_style}]{message}[/{status_style}]")

        console.print("\n")
        console.print(table)

    def get_missing_critical(self) -> List[str]:
        """Get list of failed critical components"""
        critical_items = [
            'FFmpeg', 'Playwright', 'yt-dlp', 'Required Packages',
            'Secrets Folder', 'Template HTML',
            'YouTube Data API', 'Gemini AI API', 'Pexels API', 'YouTube OAuth'
        ]

        missing = []
        for item in critical_items:
            if item in self.results:
                success, _ = self.results[item]
                if not success:
                    missing.append(item)
        return missing


def validate_apis_before_run() -> bool:
    """
    Comprehensive validation function to call before any pipeline run

    Validates ALL requirements:
    - System tools (FFmpeg, Playwright, yt-dlp)
    - Python packages (all dependencies)
    - Configuration files (cookies, secrets, templates)
    - API keys (YouTube, Gemini, Pexels, OAuth)

    Returns:
        bool: True if all critical validations passed, False otherwise
    """
    # Quiet mode - minimal output
    console.print("[dim]Checking system...[/dim]", end=" ")
    
    validator = APIValidator(quiet=True)  # Pass quiet=True
    result = validator.validate_all()
    
    if result:
        console.print("[green]✓ Ready[/green]")
    else:
        console.print("[red]✗ Failed[/red]")
        console.print("[yellow]→ Run Option 0 for detailed diagnostics[/yellow]\n")
    
    return result


if __name__ == "__main__":
    """Standalone comprehensive validation tool"""
    console.print("\n[bold]� Comprehensive Pipeline Validation Tool[/bold]")
    console.print("[dim]Checking system tools, packages, files, and API keys...[/dim]\n")

    if validate_apis_before_run():
        console.print("[bold green]✅ System fully validated! Ready to process books.[/bold green]")
        sys.exit(0)
    else:
        console.print("[bold red]❌ Validation failed! Fix the issues above.[/bold red]")
        console.print("\n[yellow]💡 Quick Fixes:[/yellow]")
        console.print("  • Missing FFmpeg? Download from: https://ffmpeg.org/download.html")
        console.print("  • Missing packages? Run: pip install -r requirements.txt")
        console.print("  • Missing Chromium? Run: playwright install chromium")
        console.print("  • Invalid API keys? Check secrets/.env and API consoles")
        console.print("  • Missing cookies.txt? Export from browser for geo-restricted videos")
        sys.exit(1)
