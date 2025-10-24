from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import io
import time
import typer
from rich.console import Console
import shutil
import requests
import os
from dotenv import load_dotenv
import sys
import re
import tempfile

# Add repo root to sys.path BEFORE imports
repo_root = Path(__file__).resolve().parents[3]  # Go up to project root (contains src/)
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Now import from src
from src.infrastructure.adapters.search import main as search_main
from src.infrastructure.adapters.transcribe import main as transcribe_main
from src.infrastructure.adapters.process import main as process_main
from src.infrastructure.adapters.tts import main as tts_main
from src.infrastructure.adapters.render import main as render_main
from src.infrastructure.adapters.youtube_metadata import main as youtube_metadata_main
from src.infrastructure.adapters.merge_av import main as merge_main
from src.infrastructure.adapters.thumbnail import main as thumbnail_main
from src.infrastructure.adapters.youtube_upload import main as upload_main
from src.infrastructure.adapters.shorts_generator import generate_short
from src.infrastructure.adapters.api_validator import validate_apis_before_run

app = typer.Typer(help="YouTube book video pipeline runner")
console = Console()

# CRITICAL FIX: Maximum retries per stage to prevent infinite loops
MAX_RETRIES_PER_STAGE = 10


def _ensure_database_synced() -> bool:
    """
    Ensure database.json is synced with YouTube channel.
    If database is empty, attempts to sync from YouTube automatically.
    
    Returns:
        True if database has data (local or synced), False otherwise
    """
    from src.infrastructure.adapters.database import (
        _load_database, 
        sync_database_from_youtube
    )
    
    db = _load_database()
    
    # If database has books, we're good
    if db.get("books"):
        console.print("[dim]✓ Using local database[/dim]")
        return True
    
    # Database is empty - attempt YouTube sync
    console.print("\n[yellow]⚠️  Local database is empty![/yellow]")
    console.print("[cyan]   Attempting to sync from YouTube channel...[/cyan]")
    
    try:
        synced = sync_database_from_youtube()
        
        if synced:
            console.print("[green]✅ Database synced from YouTube successfully![/green]")
            console.print("[dim]   Duplicate detection is now active.[/dim]\n")
            return True
        else:
            console.print("[yellow]⚠️  YouTube channel has no videos yet.[/yellow]")
            console.print("[dim]   This is normal for new channels.[/dim]")
            console.print("[dim]   Proceeding with empty database (duplicates won't be detected).[/dim]\n")
            return False
    except Exception as e:
        console.print(f"[yellow]⚠️  Sync error: {e}[/yellow]")
        console.print("[dim]   Proceeding with empty database.[/dim]\n")
        return False


def _save_summary(run_dir: Path, summary: dict) -> None:
    """
    Save summary.json to run directory.
    CRITICAL: Call this after EVERY stage completion to ensure resume works correctly.

    Args:
        run_dir: Path to run directory
        summary: Summary dictionary with stages list
    """
    try:
        summary_path = run_dir / "summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Log but don't fail pipeline if summary save fails
        print(f"[warning] Could not save summary.json: {e}")


def _verify_stage_artifact(run_dir: Path, stage_name: str) -> bool:
    """
    Verify that the expected artifact file exists for a given stage.
    This is a safety check to ensure stages marked as "completed" in summary.json
    actually produced their output files.

    Args:
        run_dir: Path to the run directory
        stage_name: Name of the stage to check

    Returns:
        True if the stage's artifact file exists
    """
    # Map stage names to their expected artifact files
    artifacts = {
        "search": "search.chosen.json",
        "transcribe": "transcribe.txt",
        "process": "script.txt",
        "tts": "narration.mp3",
        "youtube_metadata": "output.titles.json",
        "render": "video_snap.mp4",
        "merge": None,  # Merge has variable filename (youtube_title.mp4)
        "thumbnail": "thumbnail.jpg",
        "upload": None,  # Upload updates metadata (video_id in output.titles.json)
        "short": "short_final.mp4",
        "short_upload": None,  # Updates metadata (short_video_id)
    }

    artifact_file = artifacts.get(stage_name)

    # Special cases that don't have simple file checks
    if artifact_file is None:
        if stage_name == "merge":
            # Check for any .mp4 file except video_snap.mp4
            try:
                for f in run_dir.glob("*.mp4"):
                    if f.name != "video_snap.mp4":
                        return True
                return False
            except Exception:
                return False
        elif stage_name == "upload":
            # Check if video_id exists in output.titles.json
            try:
                titles_json = run_dir / "output.titles.json"
                if titles_json.exists():
                    with titles_json.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    return bool(data.get("youtube_video_id"))
                return False
            except Exception:
                return False
        elif stage_name == "short_upload":
            # Check if short_video_id exists in output.titles.json
            try:
                titles_json = run_dir / "output.titles.json"
                if titles_json.exists():
                    with titles_json.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    return bool(data.get("short_video_id"))
                return False
            except Exception:
                return False
        # Unknown special case - assume completed
        return True

    # Standard file check
    artifact_path = run_dir / artifact_file
    return artifact_path.exists()


def _is_stage_completed(run_dir: Path, stage_name: str) -> bool:
    """
    Check if a stage has already been completed in summary.json AND verify
    that the expected artifact file exists.

    This dual-check prevents bugs where summary.json shows "completed" but
    the actual output files are missing (e.g., from failed runs, manual deletions).

    Args:
        run_dir: Path to the run directory
        stage_name: Name of the stage to check

    Returns:
        True if stage is marked as completed ("ok") in summary.json AND artifact exists
    """
    summary_file = run_dir / "summary.json"
    if not summary_file.exists():
        return False

    try:
        with summary_file.open("r", encoding="utf-8") as f:
            summary = json.load(f)

        # Check if stage is marked as completed in summary.json
        for stage in summary.get("stages", []):
            if stage.get("name") == stage_name and stage.get("status") == "ok":
                # CRITICAL: Also verify the artifact exists!
                artifact_exists = _verify_stage_artifact(run_dir, stage_name)
                if not artifact_exists:
                    console.print(
                        f"[yellow]⚠️ Stage '{stage_name}' marked completed but artifact missing - will re-run[/yellow]"
                    )
                return artifact_exists

        return False
    except Exception:
        return False


def _get_last_failed_stage(run_dir: Path) -> Optional[str]:
    """
    Get the last failed stage from summary.json to enable resume from failure.
    
    When a stage fails after max retries, it's saved with status="failed".
    This function finds that stage so the pipeline can retry it on resume.
    
    Args:
        run_dir: Path to the run directory
    
    Returns:
        Name of the last failed stage, or None if no failures found
    """
    summary_file = run_dir / "summary.json"
    if not summary_file.exists():
        return None
    
    try:
        with summary_file.open("r", encoding="utf-8") as f:
            summary = json.load(f)
        
        # Find last stage with status="failed"
        failed_stages = [
            stage.get("name") 
            for stage in summary.get("stages", []) 
            if stage.get("status") == "failed"
        ]
        
        if failed_stages:
            last_failed = failed_stages[-1]  # Get the most recent failure
            console.print(f"[yellow]♻️  Found failed stage: {last_failed}[/yellow]")
            return last_failed
        
        return None
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not read summary.json: {e}[/yellow]")
        return None


def _should_retry_stage(run_dir: Path, stage_name: str, failed_stage: Optional[str]) -> bool:
    """
    Determine if a stage should be retried based on previous run status.
    
    Logic:
    - If stage was completed successfully (status="ok") → Skip
    - If stage was the one that failed (status="failed") → Retry
    - If stage comes after failed stage → Run (need to continue pipeline)
    
    Args:
        run_dir: Path to the run directory
        stage_name: Current stage being checked
        failed_stage: Name of the last failed stage (if any)
    
    Returns:
        True if stage should be retried/run, False if it should be skipped
    """
    # If no failed stage, use normal completion check
    if not failed_stage:
        return not _is_stage_completed(run_dir, stage_name)
    
    # If this is the failed stage, always retry
    if stage_name == failed_stage:
        console.print(f"[cyan]♻️  Retrying failed stage: {stage_name}[/cyan]")
        return True
    
    # If stage was completed successfully, skip it
    if _is_stage_completed(run_dir, stage_name):
        return False
    
    # For stages after the failed one, run them
    return True


def _cleanup_temp_files(run_dir: Path, debug: bool = False):
    """
    Clean up temporary files after pipeline failure or completion.

    CRITICAL FIX: Prevents disk space waste from failed runs.
    """
    cleanup_paths = [
        run_dir / "tmp" / "tts_segments",
        Path("tmp") / "subs",
        Path("tmp") / "tts_segments",
    ]

    for path in cleanup_paths:
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    if debug:
                        print(f"🗑️ Cleaned up: {path}")
                else:
                    path.unlink()
                    if debug:
                        print(f"🗑️ Deleted: {path}")
            except Exception as e:
                if debug:
                    print(f"⚠️ Failed to cleanup {path}: {e}")

    # Clean up Pexels clips in run directory
    try:
        for clip in run_dir.glob("pexels_clip_*.mp4"):
            clip.unlink()
            if debug:
                print(f"🗑️ Deleted Pexels clip: {clip.name}")
    except Exception as e:
        if debug:
            print(f"⚠️ Failed to cleanup Pexels clips: {e}")


def _cleanup_successful_run(run_dir: Path, debug: bool = False):
    """
    Clean up completed run folder after successful upload to YouTube.

    POLICY:
    - If book is successfully uploaded (status="done" in database.json)
      → Delete entire run folder + temp files
    - If book failed at any stage (status="processing" or not in DB)
      → Keep run folder for debugging

    Args:
        run_dir: Path to the run directory
        debug: Print debug messages
    """
    from src.infrastructure.adapters.database import check_book_exists

    try:
        # Load book metadata to check status
        titles_json = run_dir / "output.titles.json"
        if not titles_json.exists():
            if debug:
                print(f"⚠️ No metadata found, keeping run folder: {run_dir.name}")
            return

        with titles_json.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        book_name = metadata.get("main_title")
        author_name = metadata.get("author_name")

        if not book_name:
            if debug:
                print(f"⚠️ No book name found, keeping run folder: {run_dir.name}")
            return

        # Check database status
        book_entry = check_book_exists(book_name, author_name)

        if book_entry and book_entry.get("status") == "done":
            # Success! Delete the run folder
            print(f"\n🗑️ Book '{book_name}' successfully completed → Cleaning up run folder...")

            # Delete temp files first (TTS segments, etc.)
            _cleanup_temp_files(run_dir, debug=debug)

            # Delete the entire run directory
            try:
                import shutil
                shutil.rmtree(run_dir)
                print(f"✅ Deleted run folder: {run_dir.name}")
                print(f"💾 Disk space freed! Book metadata saved in database.json")
            except Exception as e:
                print(f"⚠️ Failed to delete run folder {run_dir.name}: {e}")

        else:
            # Failed or still processing → Keep folder
            if debug:
                status = book_entry.get("status") if book_entry else "not in database"
                print(f"📦 Keeping run folder for debugging (status: {status}): {run_dir.name}")

    except Exception as e:
        if debug:
            print(f"⚠️ Cleanup check failed: {e}")
            print(f"📦 Keeping run folder by default: {run_dir.name}")


def make_run_dirs(base: Path) -> dict:
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    root = base / run_id
    # Create only the root run directory (flat structure)
    root.mkdir(parents=True, exist_ok=True)
    # Temporary segments folder (outside the run directory)
    tmp_segments = Path("tmp") / "tts_segments" / run_id
    tmp_segments.mkdir(parents=True, exist_ok=True)
    paths = {"root": root, "tmp_segments": tmp_segments}
    # Maintain runs/latest/ pointer directory
    try:
        latest_dir = base / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        with (latest_dir / "path.txt").open("w", encoding="utf-8") as f:
            f.write(str(root.resolve()))
    except Exception:
        pass
    return paths


class TeeWriter(io.TextIOBase):
    def __init__(self, *streams):
        # accept any file-like with write/flush
        self._streams = [s for s in streams if s is not None]
    def write(self, s: str):
        for st in self._streams:
            try:
                st.write(s)
            except Exception:
                pass
        return len(s)
    def flush(self):
        for st in self._streams:
            try:
                st.flush()
            except Exception:
                pass


def _discover_yt_api_key(repo_root: Path) -> str | None:
    key = os.environ.get("YT_API_KEY")
    if key:
        return key.strip()
    for f in (repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"):
        try:
            if f.exists():
                t = f.read_text(encoding="utf-8").strip()
                if t:
                    return t
        except Exception:
            pass
    return None


def _discover_gemini_key(repo_root: Path) -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    for f in (repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"):
        try:
            if f.exists():
                t = f.read_text(encoding="utf-8").strip()
                if t:
                    return t
        except Exception:
            pass
    return None


def _preflight_check(run_root: Path, config_dir: Path, combined_log: Path | None = None) -> None:
    repo_root = Path(__file__).resolve().parents[3]  # Fixed: go up to project root
    log_path = combined_log or (run_root / "preflight.log")
    _stdout = sys.stdout
    attempt = 0
    while True:
        attempt += 1
        ok = True
        with log_path.open("a", encoding="utf-8") as lf:
            sys.stdout = TeeWriter(_stdout, lf)
            print("\n\n==============================================")
            print(f"[Preflight] attempt {attempt} @ {datetime.now().isoformat(timespec='seconds')}")
            print("==============================================")
            print(f"\n[preflight] attempt {attempt}...")
            # Internet check
            try:
                resp = requests.get("https://www.google.com/generate_204", timeout=5)
                if resp.status_code not in (204, 200):
                    print("Internet check returned status:", resp.status_code)
                    ok = False
            except Exception as e:
                print("Internet not reachable:", e)
                ok = False

            # ffmpeg
            if shutil.which("ffmpeg") is None:
                print("ffmpeg not found in PATH")
                ok = False

            # yt-dlp
            try:
                import yt_dlp  # type: ignore
                _ = yt_dlp
            except Exception:
                if shutil.which("yt-dlp") is None:
                    print("yt-dlp not installed (module and CLI not found)")
                    ok = False

            # Playwright launch test
            try:
                from playwright.sync_api import sync_playwright  # type: ignore
                with sync_playwright() as p:
                    br = p.chromium.launch(headless=True)
                    br.close()
            except Exception as e:
                print("Playwright browsers not ready:", e)
                ok = False

            # Cookies check (optional by default; required if configured)
            require_cookies = False
            try:
                # from config settings.json flag
                cfg_path = Path(config_dir) / "settings.json"
                if cfg_path.exists():
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    rc = cfg.get("require_cookies")
                    if isinstance(rc, bool):
                        require_cookies = rc
                # env override
                env_rc = os.environ.get("REQUIRE_COOKIES")
                if isinstance(env_rc, str) and env_rc.strip().lower() in ("1", "true", "yes"):
                    require_cookies = True
            except Exception:
                pass

            cookie_candidates = [repo_root / "secrets" / "cookies.txt", repo_root / "cookies.txt"]
            cookie_found = None
            for cpath in cookie_candidates:
                try:
                    if cpath.exists() and cpath.stat().st_size > 0:
                        cookie_found = cpath
                        break
                except Exception:
                    pass
            if cookie_found:
                print("cookies.txt found:", cookie_found)
            else:
                if require_cookies:
                    print("cookies.txt is required but was not found in 'secrets/cookies.txt' or repo root.")
                    ok = False
                else:
                    print("cookies.txt not found; proceeding without cookies.")

            # YouTube API key test (with multi-key fallback)
            yt_keys = []
            
            # 1. Try environment variable first
            env_key = os.environ.get("YT_API_KEY")
            if env_key:
                yt_keys.append(env_key.strip())
            
            # 2. Load from api_keys.txt (multiple keys)
            api_keys_path = repo_root / "secrets" / "api_keys.txt"
            if api_keys_path.exists():
                try:
                    content = api_keys_path.read_text(encoding="utf-8")
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            yt_keys.append(line)
                except Exception:
                    pass
            
            # 3. Fallback to single api_key.txt
            if not yt_keys:
                single_key = _discover_yt_api_key(repo_root)
                if single_key:
                    yt_keys.append(single_key)
            
            if not yt_keys:
                print("YouTube API key not found (env YT_API_KEY, secrets/api_keys.txt, or secrets/api_key.txt)")
                ok = False
            else:
                yt_key_working = False
                for i, yt_key in enumerate(yt_keys, start=1):
                    try:
                        test_url = "https://www.googleapis.com/youtube/v3/search"
                        params = {"part": "snippet", "q": "test", "type": "video", "maxResults": 1, "key": yt_key}
                        r = requests.get(test_url, params=params, timeout=10)
                        if r.status_code == 200:
                            print(f"✅ YouTube API key {i}/{len(yt_keys)} working!")
                            yt_key_working = True
                            break
                        elif r.status_code == 403 and "quota" in r.text.lower():
                            print(f"⚠️  YouTube API key {i}/{len(yt_keys)}: Quota exceeded, trying next...")
                            continue
                        else:
                            print(f"⚠️  YouTube API key {i}/{len(yt_keys)} failed: {r.status_code}")
                            continue
                    except Exception as e:
                        print(f"⚠️  YouTube API key {i}/{len(yt_keys)} error: {str(e)[:100]}")
                        continue
                
                if not yt_key_working:
                    print(f"❌ All {len(yt_keys)} YouTube API key(s) failed!")
                    ok = False

            # Gemini API key test (with multi-key fallback)
            gm_keys = []
            
            # Load all API keys from api_keys.txt (fallback system)
            api_keys_path = repo_root / "secrets" / "api_keys.txt"
            if api_keys_path.exists():
                try:
                    content = api_keys_path.read_text(encoding="utf-8")
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            gm_keys.append(line)
                    if gm_keys:
                        print(f"📋 Loaded {len(gm_keys)} API key(s) for fallback")
                except Exception as e:
                    print(f"⚠️  Failed to read api_keys.txt: {e}")
            
            # Fallback to single key if api_keys.txt not found or empty
            if not gm_keys:
                single_key = _discover_gemini_key(repo_root)
                if single_key:
                    gm_keys.append(single_key)
            
            if not gm_keys:
                print("❌ GEMINI_API_KEY not found (env, secrets/api_keys.txt, or secrets/api_key.txt)")
                ok = False
            else:
                # Try each API key until one works
                gemini_working = False
                for idx, gm_key in enumerate(gm_keys, 1):
                    try:
                        print(f"🔑 Trying API key {idx}/{len(gm_keys)}: {gm_key[:20]}...")
                        import importlib as _il
                        genai = _il.import_module("google.generativeai")
                        getattr(genai, "configure")(api_key=gm_key)
                        Model = getattr(genai, "GenerativeModel")
                        model = Model("gemini-2.5-flash")
                        resp = model.generate_content("ping")
                        _ = getattr(resp, "text", None)
                        print(f"✅ API key {idx} working!")
                        gemini_working = True
                        break  # Success! Stop trying other keys
                    except Exception as e:
                        error_str = str(e)
                        # Check if quota exceeded (429 error)
                        if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                            print(f"⚠️  API key {idx} quota exceeded, trying next key...")
                            continue
                        else:
                            print(f"❌ API key {idx} failed: {e}")
                            # For non-quota errors, still try next key
                            continue
                
                if not gemini_working:
                    print("❌ All Gemini API keys failed or quota exceeded")
                    ok = False

            # Thumbnail font check (warning only, not critical)
            try:
                from src.infrastructure.adapters.thumbnail import _bebas_neue_candidates
                font_cands = _bebas_neue_candidates("bold")
                if font_cands:
                    print(f"✓ Thumbnail font found: {font_cands[0].name}")
                else:
                    print("⚠️  Thumbnail font 'Bebas Neue' not found in assets/fonts/ or system")
                    print("   Thumbnail generation (Stage 9) will fail and use bookcover.jpg fallback")
                    print("   Download: https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf")
                    print("   Save to: assets/fonts/BebasNeue-Regular.ttf")
                    # Don't fail preflight - thumbnail is non-critical
            except Exception as e:
                print(f"⚠️  Thumbnail font check skipped: {e}")

        sys.stdout = _stdout
        if ok:
            console.print("[green]Preflight passed. Starting pipeline...[/green]")
            return
        sleep_s = min(60, 5 * attempt)
        console.print(f"[yellow]Preflight failed (attempt {attempt}). Retrying in {sleep_s}s...[/yellow]")
        time.sleep(sleep_s)


@app.command()
def run(
    query: str = typer.Argument(..., help="Book title or topic for YouTube search"),
    runs_dir: Path = typer.Option(Path("runs"), help="Base directory for run outputs"),
    config_dir: Path = typer.Option(Path("config"), help="Config directory (settings.json/template.html)"),
    secrets_dir: Path = typer.Option(Path("secrets"), help="Secrets directory containing .env"),
    direct_url: Optional[str] = typer.Option(None, help="Process specific YouTube video URL directly (skips search)"),
    skip_api_check: bool = typer.Option(False, help="Skip API validation (NOT RECOMMENDED)"),
    auto_continue: bool = typer.Option(False, "--auto-continue", help="Auto-continue on errors without user input (for batch mode)")
):
    """
    🚨 CRITICAL ERROR HANDLING:
    Any RuntimeError raised by stage failures will propagate up and cause
    the pipeline to exit with code 1, ensuring batch processing stops immediately.
    """
    try:
        _run_internal(query, runs_dir, config_dir, secrets_dir, direct_url, skip_api_check, auto_continue)
    except RuntimeError as e:
        # ❌ CRITICAL: Stage failed after max retries
        console.print(f"\n[bold red]🛑 PIPELINE FAILED: {e}[/bold red]")
        console.print("[yellow]Pipeline stopped after max retry attempts.[/yellow]")
        console.print("[dim]Check pipeline.log for details.[/dim]\n")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠️ Pipeline interrupted by user.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        # ❌ Unexpected error
        console.print(f"\n[bold red]🛑 UNEXPECTED ERROR: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


def _run_internal(
    query: str,
    runs_dir: Path,
    config_dir: Path,
    secrets_dir: Path,
    direct_url: Optional[str],
    skip_api_check: bool,
    auto_continue: bool = False
):
    """Internal run function with all pipeline logic (wrapped by error handler)."""
    load_dotenv(secrets_dir / ".env")

    # 🔒 CRITICAL: Validate all APIs before starting pipeline
    if not skip_api_check:
        console.print("\n", end="")  # Just a newline
        if not validate_apis_before_run():
            console.print("\n[bold red]❌ System validation failed![/bold red]")
            console.print("[yellow]Fix the issues and try again.[/yellow]")
            console.print("[dim]Hint: Run Option 0 for detailed diagnostics[/dim]\n")
            raise typer.Exit(code=1)
    else:
        console.print("[yellow]⚠️ Skipping validation (--skip-api-check)[/yellow]\n")
    
    # 📊 CRITICAL: Ensure database is synced (auto-sync from YouTube if empty)
    _ensure_database_synced()

    # Cleanup orphaned/empty run folders before starting new pipeline
    try:
        for run_folder in runs_dir.iterdir():
            if not run_folder.is_dir() or run_folder.name == "latest":
                continue

            # Check if folder is empty or has only empty pipeline.log
            files = list(run_folder.iterdir())
            if len(files) == 0:
                # Completely empty folder
                shutil.rmtree(run_folder)
                console.print(f"[dim]🗑️ Deleted empty run folder: {run_folder.name}[/dim]")
            elif len(files) == 1 and files[0].name == "pipeline.log":
                # Only has pipeline.log - check if it's empty
                if files[0].stat().st_size == 0:
                    shutil.rmtree(run_folder)
                    console.print(f"[dim]🗑️ Deleted incomplete run folder: {run_folder.name}[/dim]")
    except Exception as e:
        # Silently ignore cleanup errors - not critical
        pass

    d = make_run_dirs(runs_dir)
    summary: dict = {"run_id": d["root"].name, "stages": []}

    # Create a single combined log file for this run and run preflight into it
    combined_log = d["root"] / "pipeline.log"
    # Preflight: internet, dependencies, keys. Retry until everything is ready, logging into combined log.
    _preflight_check(d["root"], config_dir, combined_log=combined_log)

    # 🍪 COOKIES CHECK: CRITICAL - Required for transcribe and process stages
    console.print("\n[bold cyan]🍪 Cookies Check (Required)[/bold cyan]")
    try:
        from src.infrastructure.adapters.cookie_manager import check_cookies_status, interactive_cookie_setup
        
        cookies_valid, cookies_msg = check_cookies_status(verbose=False)
        
        if cookies_valid:
            console.print(f"[green]✓[/green] {cookies_msg}")
        else:
            # Cookies are REQUIRED - transcribe.py and process.py depend on them
            console.print(f"[bold red]❌ CRITICAL: {cookies_msg}[/bold red]")
            console.print("[yellow]⚠️  Cookies are REQUIRED for pipeline to work correctly:[/yellow]")
            console.print("[dim]   - Transcribe stage: Downloads video/audio with yt-dlp[/dim]")
            console.print("[dim]   - Process stage: Fetches book cover from Amazon[/dim]")
            console.print("[dim]   Without valid cookies, these stages will fail![/dim]")
            
            # Force user to set up cookies now
            console.print("\n[bold cyan]You must set up YouTube + Amazon cookies to continue.[/bold cyan]")
            console.print("[dim]📖 Full guide: docs/COOKIES_SETUP.md[/dim]")
            
            if auto_continue:
                # Auto mode: skip cookie setup and exit
                console.print("\n[bold red]❌ Auto-continue mode: Cannot set up cookies automatically[/bold red]")
                console.print("[yellow]Pipeline cannot continue without valid cookies.[/yellow]")
                sys.exit(1)
            
            try:
                setup_now = input("Set up cookies now? (y/n): ").strip().lower()
                if setup_now == 'y':
                    success = interactive_cookie_setup()
                    if not success:
                        console.print("\n[bold red]❌ Cookie setup failed![/bold red]")
                        console.print("[yellow]Pipeline cannot continue without valid cookies.[/yellow]")
                        console.print("[dim]Read guide: docs/COOKIES_SETUP.md[/dim]")
                        sys.exit(1)
                    # Re-check after setup
                    cookies_valid, cookies_msg = check_cookies_status(verbose=False)
                    if not cookies_valid:
                        console.print(f"\n[bold red]❌ Cookies still invalid: {cookies_msg}[/bold red]")
                        console.print("[yellow]Pipeline cannot continue.[/yellow]")
                        sys.exit(1)
                    console.print(f"[green]✓[/green] Cookies validated successfully!")
                else:
                    console.print("\n[bold red]❌ Pipeline cancelled by user[/bold red]")
                    console.print("[yellow]Cookies are required to continue.[/yellow]")
                    sys.exit(1)
            except KeyboardInterrupt:
                console.print("\n\n[bold red]❌ Pipeline cancelled[/bold red]")
                sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Cookie check error: {e}[/bold red]")
        console.print("[yellow]Cannot verify cookies - pipeline may fail.[/yellow]")
        
        if auto_continue:
            # Auto mode: continue without asking
            console.print("[dim]🤖 Auto-continue mode: Proceeding despite cookie error...[/dim]")
        else:
            try:
                cont = input("Continue anyway? (yes/no): ").strip().lower()
                if cont != 'yes':
                    sys.exit(1)
            except KeyboardInterrupt:
                sys.exit(1)
    
    # 🔄 YOUTUBE SYNC: Ensure database.json is up-to-date (syncs from YouTube if empty)
    console.print("\n[bold cyan]🔄 Database Sync Check[/bold cyan]")
    try:
        from src.infrastructure.adapters.database import ensure_database_synced
        ensure_database_synced()
    except Exception as e:
        console.print(f"[yellow]⚠️  Database sync failed: {e}[/yellow]")
        console.print("[dim]   Continuing with local database (duplicate detection may not work)[/dim]")

    # EARLY RENAME: Get official book name from user query and rename folder before any heavy processing
    console.rule("[bold]0) Get Book Metadata & Rename")
    try:
        # Import the helper function from process.py
        from src.infrastructure.adapters.process import _configure_model, _get_official_book_name, _get_book_playlist
        from src.infrastructure.adapters.database import check_book_exists, add_book
        import json as _json

        # Load prompts
        prompts = {}
        try:
            prompts_json = config_dir / "prompts.json"
            if prompts_json.exists():
                prompts = _json.loads(prompts_json.read_text(encoding="utf-8"))
        except Exception:
            pass

        # Configure Gemini model
        model = _configure_model(config_dir)
        if model:
            print(f"[early_meta] Getting official book name from query: {query}")

            # Get book name and author
            book_name, author_name = _get_official_book_name(model, query, prompts)

            if book_name:
                print(f"[early_meta] ✅ Book: {book_name}")
                print(f"[early_meta] ✅ Author: {author_name or 'Unknown'}")

                # Get playlist category
                print(f"[early_meta] Classifying book into playlist...")
                playlist = _get_book_playlist(model, book_name, author_name, prompts)
                print(f"[early_meta] ✅ Playlist: {playlist}")

                # CRITICAL: Check if book already exists BEFORE adding to database
                existing = check_book_exists(book_name, author_name)
                status = existing.get('status') if existing else None
                reused_old_folder = False  # Track if we reused an existing folder

                if existing and status in ['done', 'uploaded']:
                    # Book completely done - STOP
                    console.print(f"\n[bold red]⛔ Book already processed![/bold red]")
                    console.print(f"[yellow]Title:[/yellow] {existing.get('main_title')}")
                    console.print(f"[yellow]Author:[/yellow] {existing.get('author_name', 'Unknown')}")
                    console.print(f"[yellow]Playlist:[/yellow] {existing.get('playlist', 'Unknown')}")
                    console.print(f"[yellow]Date:[/yellow] {existing.get('date_added', 'Unknown')}")
                    console.print(f"[yellow]Status:[/yellow] {status}")
                    if existing.get('youtube_url'):
                        console.print(f"[yellow]YouTube:[/yellow] {existing['youtube_url']}")
                    if existing.get('youtube_short_url'):
                        console.print(f"[yellow]Short:[/yellow] {existing['youtube_short_url']}")
                    
                    # CRITICAL FIX: Delete empty run folder to avoid clutter
                    console.print(f"\n[dim]🗑️  Cleaning up empty run folder: {d['root'].name}[/dim]")
                    try:
                        shutil.rmtree(d["root"])
                        console.print(f"[dim]✅ Deleted empty folder[/dim]")
                    except Exception as e:
                        console.print(f"[dim yellow]⚠️  Could not delete folder: {e}[/dim yellow]")
                    
                    console.print(f"\n[red]Pipeline stopped to prevent duplicate processing.[/red]")
                    return

                elif existing and status == 'processing':
                    # Book incomplete - try to reuse old folder
                    console.print(f"\n[bold yellow]♻️ Book exists but is INCOMPLETE (status: processing)[/bold yellow]")
                    console.print(f"[cyan]Title:[/cyan] {existing.get('main_title')}")
                    console.print(f"[cyan]Author:[/cyan] {existing.get('author_name', 'Unknown')}")
                    console.print(f"[cyan]Run Folder:[/cyan] {existing.get('run_folder', 'Unknown')}")
                    console.print(f"\n[cyan]Searching for existing run folder to resume...[/cyan]")

                    # Search for old folder by matching book name + author in output.titles.json
                    old_run_folder = None
                    runs_dir = d["root"].parent
                    for run_folder in runs_dir.iterdir():
                        if not run_folder.is_dir() or run_folder.name == "latest":
                            continue

                        old_titles_json = run_folder / "output.titles.json"
                        if old_titles_json.exists():
                            try:
                                old_data = _json.loads(old_titles_json.read_text(encoding="utf-8"))
                                if (old_data.get("main_title") == book_name and
                                    old_data.get("author_name") == author_name):
                                    old_run_folder = run_folder
                                    console.print(f"[green]✅ Found existing run folder: {run_folder.name}[/green]")
                                    break
                            except Exception:
                                continue

                    if old_run_folder:
                        # Delete new temporary folder and use old one
                        console.print(f"[yellow]Deleting temporary new folder: {d['root'].name}[/yellow]")
                        shutil.rmtree(d["root"])

                        # Use old folder
                        d["root"] = old_run_folder
                        combined_log = old_run_folder / "pipeline.log"

                        # Update latest pointer
                        latest = old_run_folder.parent / "latest"
                        latest.mkdir(exist_ok=True)
                        (latest / "path.txt").write_text(str(old_run_folder.resolve()), encoding="utf-8")

                        console.print(f"[bold green]✅ Resuming in folder: {old_run_folder.name}[/bold green]")
                        
                        # 🔍 CRITICAL: Check for failed stages to enable resume from failure
                        failed_stage = _get_last_failed_stage(old_run_folder)
                        if failed_stage:
                            console.print(f"[bold yellow]♻️  RESUMING FROM FAILED STAGE: {failed_stage}[/bold yellow]")
                            console.print(f"[yellow]   This stage will be retried with {MAX_RETRIES_PER_STAGE} attempts[/yellow]")
                            console.print(f"[dim]   All completed stages will be skipped[/dim]\n")
                            # Store failed_stage for later use in stage checks
                            summary["last_failed_stage"] = failed_stage
                        else:
                            console.print(f"[cyan]Pipeline will resume from last successful stage...[/cyan]\n")

                        reused_old_folder = True  # Mark that we reused old folder
                        
                        # 📖 CRITICAL: Load existing summary.json to preserve stage history
                        summary_file = old_run_folder / "summary.json"
                        if summary_file.exists():
                            try:
                                summary = _json.loads(summary_file.read_text(encoding="utf-8"))
                                console.print(f"[dim]✓ Loaded existing summary with {len(summary.get('stages', []))} completed stages[/dim]")
                            except Exception as e:
                                console.print(f"[yellow]⚠️  Could not load summary.json: {e}[/yellow]")
                                summary = {"run_id": old_run_folder.name, "stages": []}
                        
                        # Skip renaming and database update since folder already exists
                        # Continue to pipeline stages below
                    else:
                        console.print(f"[yellow]⚠️ Could not find old run folder. Starting fresh...[/yellow]\n")
                        # Continue with new folder (rename it below)

                elif existing:
                    # Unknown status - warn but continue
                    console.print(f"\n[yellow]⚠️ Book exists with unknown status: {status}[/yellow]")
                    console.print(f"[yellow]Continuing anyway...[/yellow]\n")
                
                # Add to database if this is a NEW book (not existing)
                if not existing:
                    add_book(book_name, author_name, d["root"].name, status="processing", playlist=playlist)
                    print(f"[early_meta] ✅ Added NEW book to database: {book_name}")

                # Save to output.titles.json (not early_metadata.json)
                if not reused_old_folder:
                    # Only save if we didn't reuse an old folder (it already has this file)
                    titles_data = {
                        "main_title": book_name,
                        "author_name": author_name,
                        "playlist": playlist,
                    }
                    (d["root"] / "output.titles.json").write_text(_json.dumps(titles_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"[early_meta] ✅ Saved to output.titles.json")

                # Rename folder (only if new folder, not reused)
                if not reused_old_folder:
                    def slugify(s: str) -> str:
                        s = s.encode("ascii", "ignore").decode("ascii")
                        s = re.sub(r"[^A-Za-z0-9\-\_ ]+", "", s)
                        s = re.sub(r"\s+", "-", s).strip("-_")
                        return re.sub(r"-+", "-", s)[:60]

                    slug = slugify(book_name)
                    if slug:
                        new_root = d["root"].parent / f"{d['root'].name}_{slug}"
                        if new_root.exists():
                            for i in range(1, 100):
                                candidate = d["root"].parent / f"{d['root'].name}_{slug}-{i}"
                                if not candidate.exists():
                                    new_root = candidate
                                    break

                        old_name = d["root"].name
                        d["root"].rename(new_root)
                        print(f"[early_meta] ✅ Renamed: {old_name} → {new_root.name}")

                        # Update paths
                        d["root"] = new_root
                        combined_log = new_root / "pipeline.log"

                        # Update latest pointer
                        latest = d["root"].parent / "latest"
                        latest.mkdir(exist_ok=True)
                        (latest / "path.txt").write_text(str(new_root.resolve()), encoding="utf-8")

                        # Update run_folder in database after rename
                        from src.infrastructure.adapters.database import update_book_run_folder
                        update_book_run_folder(book_name, author_name, new_root.name)
                        print(f"[early_meta] ✅ Updated database with new folder name")
            else:
                print(f"[early_meta] ⚠️ Could not extract book name")
        else:
            print(f"[early_meta] ⚠️ Gemini not configured, skipping")
    except Exception as e:
        print(f"[early_meta] ⚠️ Error: {e}")

    console.rule("[bold]1) Search YouTube")

    # 🔍 Get last failed stage (if any) for intelligent resume
    failed_stage = summary.get("last_failed_stage")
    
    # Check if direct URL provided (skip search)
    if direct_url:
        console.print(f"[cyan]🔗 Using direct video URL (skipping search): {direct_url}[/cyan]")
        search_result = {"url": direct_url, "title": "Direct Video", "duration_min": 0}

        # Save to search.chosen.json for consistency
        search_chosen = d["root"] / "search.chosen.json"
        with search_chosen.open("w", encoding="utf-8") as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)

        summary["stages"].append({
            "name": "search",
            "status": "ok",
            "duration_sec": 0,
            "artifact": str(search_chosen.resolve()),
        })
        _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
    # Check if stage already completed (or needs retry)
    elif not _should_retry_stage(d["root"], "search", failed_stage):
        console.print("[green]✓ Search stage already completed (skipping)[/green]")
        # Load search result from file
        search_chosen = d["root"] / "search.chosen.json"
        if search_chosen.exists():
            with search_chosen.open("r", encoding="utf-8") as f:
                search_result = json.load(f)
        else:
            search_result = None
    else:
        _stdout = sys.stdout
        attempt = 0
        search_result = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] SEARCH attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[search] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    search_result = search_main(query=query, output_dir=d["root"])  # best candidate URL or info dict
                except Exception as e:
                    print("Search error:", e)
                    search_result = None
                t1 = time.time()
            sys.stdout = _stdout
            if search_result is not None:
                summary["stages"].append({
                    "name": "search",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str((d["root"] / "input_name.txt").resolve()),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break

            if attempt >= MAX_RETRIES_PER_STAGE:
                error_msg = f"❌ CRITICAL: Search stage failed after {MAX_RETRIES_PER_STAGE} attempts"
                console.print(f"[red]{error_msg}[/red]")
                summary["stages"].append({
                    "name": "search",
                    "status": "failed",
                    "duration_sec": round(t1 - t0, 3),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save even on failure
                raise RuntimeError(error_msg)

            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Search failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    console.rule("[bold]2) Transcribe")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "transcribe", failed_stage):
        console.print("[green]✓ Transcribe stage already completed (skipping)[/green]")
        transcript_path = d["root"] / "transcribe.txt"
    else:
        _stdout = sys.stdout
        transcript_path = None
        # Build candidate list from search result
        candidates = []
        if isinstance(search_result, dict) and search_result.get("candidates"):
            candidates = search_result["candidates"]
        else:
            # fallback to just the best
            candidates = [search_result]

        # Get book name for validation (to prevent choosing videos about different books)
        book_name_for_validation = None
        try:
            titles_json_path = d["root"] / "output.titles.json"
            if titles_json_path.exists():
                titles_data = json.loads(titles_json_path.read_text(encoding="utf-8"))
                book_name_for_validation = titles_data.get("main_title")
                if book_name_for_validation:
                    console.print(f"[cyan]Book name for validation: {book_name_for_validation}[/cyan]")
        except Exception:
            pass

        # Try each candidate until transcription succeeds
        for idx, cand in enumerate(candidates, start=1):
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] TRANSCRIBE candidate {idx}/{len(candidates)} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[transcribe] trying candidate {idx}...")
                t0 = time.time()
                try:
                    transcript_path = transcribe_main(search_result=cand if cand else "", output_dir=d["root"])  # returns transcribe.txt path
                except Exception as e:
                    print("Transcribe error:", e)
                    transcript_path = None
                t1 = time.time()
            sys.stdout = _stdout
            if transcript_path:
                summary["stages"].append({
                    "name": "transcribe",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(transcript_path),
                    "candidate_index": idx,
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                # Save chosen candidate for traceability
                try:
                    chosen_path = d["root"] / "search.chosen.json"
                    with chosen_path.open("w", encoding="utf-8") as f:
                        json.dump(cand, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                break
            else:
                console.print(f"[yellow]Candidate {idx} transcription failed. Moving to next candidate...[/yellow]")

        if not transcript_path:
            console.print("[red]All candidates failed transcription. Exiting.[/red]")
            raise typer.Exit(code=2)

    console.rule("[bold]3) Process Script")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "process", failed_stage):
        console.print("[green]✓ Process stage already completed (skipping)[/green]")
        processed_single = d["root"] / "script.txt"
    else:
        _stdout = sys.stdout
        attempt = 0
        processed_single = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] PROCESS attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[process] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    processed_single = process_main(
                        transcript_path=transcript_path,
                        config_dir=config_dir,
                        output_text=d["root"] / "translate.txt",
                        output_titles=d["root"] / "output.titles.json",
                    )
                except Exception as e:
                    print("Process error:", e)
                    processed_single = None
                t1 = time.time()
            sys.stdout = _stdout
            # processed_single may be a string path; normalize to Path
            if isinstance(processed_single, str):
                processed_single = Path(processed_single)
            if processed_single and Path(processed_single).exists():
                summary["stages"].append({
                    "name": "process",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(Path(processed_single).resolve()),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break

            if attempt >= MAX_RETRIES_PER_STAGE:
                error_msg = f"❌ CRITICAL: Process stage failed after {MAX_RETRIES_PER_STAGE} attempts"
                console.print(f"[red]{error_msg}[/red]")
                summary["stages"].append({
                    "name": "process",
                    "status": "failed",
                    "duration_sec": round(t1 - t0, 3),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save even on failure
                raise RuntimeError(error_msg)

            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Process failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    # 4) TTS (must run BEFORE YouTube Metadata to generate timestamps.json)
    console.rule("[bold]4) TTS")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "tts", failed_stage):
        console.print("[green]✓ TTS stage already completed (skipping)[/green]")
        narration_mp3 = d["root"] / "narration.mp3"
    else:
        _stdout = sys.stdout
        attempt = 0
        narration_mp3 = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] TTS attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[tts] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    narration_mp3 = tts_main(
                        text_path=Path(processed_single) if processed_single else Path(""),
                        segments_dir=d["tmp_segments"],
                        output_mp3=d["root"] / "narration.mp3",
                        run_dir=d["root"],
                    )
                except Exception as e:
                    print("TTS error:", e)
                    narration_mp3 = None
                t1 = time.time()
            sys.stdout = _stdout
            if narration_mp3:
                summary["stages"].append({
                    "name": "tts",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(narration_mp3),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break

            if attempt >= MAX_RETRIES_PER_STAGE:
                error_msg = f"❌ CRITICAL: TTS stage failed after {MAX_RETRIES_PER_STAGE} attempts"
                console.print(f"[red]{error_msg}[/red]")
                summary["stages"].append({
                    "name": "tts",
                    "status": "failed",
                    "duration_sec": round(t1 - t0, 3),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save even on failure
                raise RuntimeError(error_msg)

            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]TTS failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    # 5) YouTube Metadata (Title + Description with Timestamps)
    # NOTE: Must run AFTER TTS to read timestamps.json
    console.rule("[bold]5) YouTube Metadata")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "youtube_metadata", failed_stage):
        console.print("[green]✓ YouTube Metadata stage already completed (skipping)[/green]")
        ym_path = d["root"] / "output.titles.json"
    else:
        _stdout = sys.stdout
        ym_attempts = 0
        ym_path = None
        while ym_attempts < MAX_RETRIES_PER_STAGE:
            ym_attempts += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] YT_METADATA attempt {ym_attempts}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[yt_metadata] attempt {ym_attempts}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    ym_path = youtube_metadata_main(
                        titles_json=d["root"] / "output.titles.json",
                        config_dir=config_dir,
                    )
                except Exception as e:
                    print("YouTube Metadata error:", e)
                    ym_path = None
                t1 = time.time()
            sys.stdout = _stdout
            if ym_path:
                summary["stages"].append({
                    "name": "youtube_metadata",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(ym_path),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break
            if ym_attempts >= MAX_RETRIES_PER_STAGE:
                raise RuntimeError(f"YouTube Metadata stage failed after {MAX_RETRIES_PER_STAGE} attempts")
            sleep_s = min(60, 5 * ym_attempts)
            console.print(f"[yellow]YouTube Metadata failed (attempt {ym_attempts}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    console.rule("[bold]7) Render Video")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "render", failed_stage):
        console.print("[green]✓ Render stage already completed (skipping)[/green]")
        final_video = d["root"] / "video_snap.mp4"
    else:
        _stdout = sys.stdout
        attempt = 0
        final_video = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] RENDER attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[render] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    # Merge run metadata (titles + cover) into a temp settings file for consistent rendering
                    base_settings = {}
                    try:
                        base_settings = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
                    except Exception:
                        base_settings = {}
                    try:
                        tj = json.loads((d["root"] / "output.titles.json").read_text(encoding="utf-8"))
                        for key in ("main_title", "subtitle", "footer", "top_title"):
                            if key in tj and isinstance(tj[key], str) and tj[key].strip():
                                base_settings[key] = tj[key]
                    except Exception:
                        pass
                    try:
                        cover_jpg = d["root"] / "bookcover.jpg"
                        if cover_jpg.exists():
                            base_settings["cover_image"] = str(cover_jpg.resolve())
                    except Exception:
                        pass
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
                    tf.close()
                    merged_settings_path = Path(tf.name)
                    merged_settings_path.write_text(json.dumps(base_settings, ensure_ascii=False, indent=2), encoding="utf-8")

                    final_video = render_main(
                        titles_json=d["root"] / "output.titles.json",
                        settings_json=merged_settings_path,
                        template_html=config_dir / "template.html",
                        narration_mp3=narration_mp3 if narration_mp3 else Path(""),
                        output_mp4=d["root"] / "video_snap.mp4",
                    )
                except Exception as e:
                    print("Render error:", e)
                    final_video = None
                t1 = time.time()
            sys.stdout = _stdout
            if final_video:
                summary["stages"].append({
                    "name": "render",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(final_video),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break
            if attempt >= MAX_RETRIES_PER_STAGE:
                raise RuntimeError(f"Render stage failed after {MAX_RETRIES_PER_STAGE} attempts")
            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Render failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    console.rule("[green]Done")
    # NOTE: summary.json is now saved after EVERY stage (not centralized here)
    # Each stage calls _save_summary() after appending to summary["stages"]

    # After success, try to rename run folder to include English book name
    try:
        # Prefer metadata titles JSON, fallback to config settings
        title_en: str | None = None
        try:
            tj = json.loads((d["root"] / "output.titles.json").read_text(encoding="utf-8"))
            title_en = tj.get("main_title") or tj.get("title") or None
        except Exception:
            pass
        if not title_en:
            try:
                sj = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
                title_en = sj.get("main_title") or sj.get("title") or None
            except Exception:
                pass

        def slugify_english(s: str) -> str:
            s_ascii = s.encode("ascii", "ignore").decode("ascii")
            s_ascii = re.sub(r"[^A-Za-z0-9\-\_ ]+", "", s_ascii)
            s_ascii = re.sub(r"\s+", "-", s_ascii).strip("-_")
            s_ascii = re.sub(r"-+", "-", s_ascii)
            return s_ascii[:60]

        if title_en:
            slug = slugify_english(str(title_en))
            if slug:
                base_dir = d["root"].parent
                # Check if folder already contains the book name (to avoid duplicate naming)
                if slug not in d["root"].name:
                    new_root = base_dir / f"{d['root'].name}_{slug}"
                    if new_root.exists():
                        for i in range(1, 100):
                            candidate = base_dir / f"{d['root'].name}_{slug}-{i}"
                            if not candidate.exists():
                                new_root = candidate
                                break
                    d["root"].rename(new_root)
                else:
                    # Folder already has book name, skip rename
                    new_root = d["root"]
                try:
                    latest_dir = base_dir / "latest"
                    latest_dir.mkdir(parents=True, exist_ok=True)
                    with (latest_dir / "path.txt").open("w", encoding="utf-8") as f:
                        f.write(str(new_root.resolve()))
                except Exception:
                    pass
                final_video = new_root / "video_snap.mp4"
                # Update run root and artifact paths after rename so subsequent stages use correct locations
                try:
                    d["root"] = new_root
                except Exception:
                    pass
                try:
                    if narration_mp3:
                        narration_mp3 = new_root / "narration.mp3"
                except Exception:
                    pass
                # Also update combined_log to point to the new run directory
                try:
                    combined_log = d["root"] / "pipeline.log"  # type: ignore[assignment]
                    combined_log.parent.mkdir(parents=True, exist_ok=True)
                    # Touch/append a note to ensure the file exists after rename
                    with combined_log.open("a", encoding="utf-8") as lf:
                        lf.write(f"\n[info] run renamed to {new_root.name}\n")
                except Exception:
                    pass
    except Exception:
        pass

    console.print(f"Video: {final_video}")

    # 7) Merge Narration + Video (loop video to audio length)
    console.rule("[bold]8) Merge Audio + Video")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "merge", failed_stage):
        console.print("[green]✓ Merge stage already completed (skipping)[/green]")
        # Find merged video file by looking for .mp4 files with youtube_title
        merged_output = None
        try:
            titles_json = d["root"] / "output.titles.json"
            if titles_json.exists():
                tj = json.loads(titles_json.read_text(encoding="utf-8"))
                yt_title = tj.get("youtube_title", "")
                if yt_title:
                    # Sanitize title to match merge output filename
                    sanitized = re.sub(r'[<>:"/\\|?*]', '-', yt_title)[:120]
                    merged_output = d["root"] / f"{sanitized}.mp4"
                    if not merged_output.exists():
                        # Fallback: find any .mp4 file that's not video_snap.mp4
                        for mp4_file in d["root"].glob("*.mp4"):
                            if mp4_file.name != "video_snap.mp4":
                                merged_output = mp4_file
                                break
        except Exception:
            pass
    else:
        _stdout = sys.stdout
        attempt = 0
        merged_output = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] MERGE attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[merge] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    merged_output = merge_main(
                        titles_json=d["root"] / "output.titles.json",
                        video_mp4=final_video if final_video else Path(""),
                        audio_mp3=narration_mp3 if narration_mp3 else Path(""),
                        output_dir=d["root"],
                    )
                except Exception as e:
                    print("Merge error:", e)
                    merged_output = None
                t1 = time.time()
            sys.stdout = _stdout
            if merged_output:
                summary["stages"].append({
                    "name": "merge",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(merged_output),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break
            if attempt >= MAX_RETRIES_PER_STAGE:
                raise RuntimeError(f"Merge stage failed after {MAX_RETRIES_PER_STAGE} attempts")
            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Merge failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    console.print(f"Merged: {merged_output}")

    # 9) Generate Thumbnail (optional but recommended)
    console.rule("[bold]9) Generate Thumbnail")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "thumbnail", failed_stage):
        console.print("[green]✓ Thumbnail stage already completed (skipping)[/green]")
        thumbnail_path = d["root"] / "thumbnail.jpg"
    else:
        _stdout = sys.stdout
        attempt = 0
        thumbnail_path = None

        # Load thumbnail font preferences from settings.json
        thumbnail_title_font = "Bebas Neue"  # Default
        thumbnail_subtitle_font = "Bebas Neue"  # Default
        thumbnail_title_font_size = 150  # Default
        thumbnail_subtitle_font_size = 60  # Default
        try:
            settings_path = config_dir / "settings.json"
            if settings_path.exists():
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                thumbnail_title_font = settings.get("thumbnail_title_font", thumbnail_title_font)
                thumbnail_subtitle_font = settings.get("thumbnail_subtitle_font", thumbnail_subtitle_font)
                thumbnail_title_font_size = settings.get("thumbnail_title_font_size", thumbnail_title_font_size)
                thumbnail_subtitle_font_size = settings.get("thumbnail_subtitle_font_size", thumbnail_subtitle_font_size)
        except Exception:
            pass

        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] THUMBNAIL attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[thumbnail] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    thumbnail_path = thumbnail_main(
                        titles_json=d["root"] / "output.titles.json",
                        run_dir=d["root"],
                        output_path=d["root"] / "thumbnail.jpg",
                        title_font_name=thumbnail_title_font,
                        sub_font_name=thumbnail_subtitle_font,
                        title_font_size=thumbnail_title_font_size,
                        subtitle_font_size=thumbnail_subtitle_font_size,
                    )
                except Exception as e:
                    print("Thumbnail generation error:", e)
                    thumbnail_path = None
                t1 = time.time()
            sys.stdout = _stdout
            if thumbnail_path and Path(thumbnail_path).exists():
                summary["stages"].append({
                    "name": "thumbnail",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": str(Path(thumbnail_path).resolve()),
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break
            # Thumbnail is not critical; log and continue after max retries
            if attempt >= MAX_RETRIES_PER_STAGE:
                console.print(f"[yellow]Thumbnail generation failed after {MAX_RETRIES_PER_STAGE} attempts. Proceeding without custom thumbnail.[/yellow]")
                break
            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Thumbnail failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    # 10) Upload to YouTube (optional; requires OAuth client_secret.json in secrets/)
    console.rule("[bold]10) Upload to YouTube")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "upload", failed_stage):
        console.print("[green]✓ Upload stage already completed (skipping)[/green]")
        # Try to get video_id from database or output.titles.json
        video_id = None
        try:
            titles_json = d["root"] / "output.titles.json"
            if titles_json.exists():
                tj = json.loads(titles_json.read_text(encoding="utf-8"))
                video_id = tj.get("youtube_video_id") or tj.get("video_id")
        except Exception:
            pass
    else:
        _stdout = sys.stdout
        attempt = 0
        video_id = None
        while attempt < MAX_RETRIES_PER_STAGE:
            attempt += 1
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] UPLOAD attempt {attempt}/{MAX_RETRIES_PER_STAGE} @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                print(f"\n[upload] attempt {attempt}/{MAX_RETRIES_PER_STAGE}...")
                t0 = time.time()
                try:
                    video_id = upload_main(
                        run_dir=d["root"],
                        titles_json=d["root"] / "output.titles.json",
                        secrets_dir=Path("secrets"),
                        privacy_status="public",  # Always public for main video
                        upload_thumbnail=True,
                    )
                except Exception as e:
                    print("Upload error:", e)
                    video_id = None
                t1 = time.time()
            sys.stdout = _stdout
            if video_id:
                summary["stages"].append({
                    "name": "upload",
                    "status": "ok",
                    "duration_sec": round(t1 - t0, 3),
                    "artifact": f"https://youtube.com/watch?v={video_id}",
                })
                _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                break
            if attempt >= MAX_RETRIES_PER_STAGE:
                raise RuntimeError(f"Upload stage failed after {MAX_RETRIES_PER_STAGE} attempts")
            sleep_s = min(60, 5 * attempt)
            console.print(f"[yellow]Upload failed (attempt {attempt}/{MAX_RETRIES_PER_STAGE}). Retrying in {sleep_s}s...[/yellow]")
            time.sleep(sleep_s)

    # 11) Generate YouTube Short
    console.rule("[bold]11) Generate YouTube Short")

    # Check if stage already completed (or needs retry)
    if not _should_retry_stage(d["root"], "short", failed_stage):
        console.print("[green]✓ Short generation stage already completed (skipping)[/green]")
        short_path = d["root"] / "short_final.mp4"
    else:
        _stdout = sys.stdout
        short_path = None
        with combined_log.open("a", encoding="utf-8") as lf:
            sys.stdout = TeeWriter(_stdout, lf)
            print("\n\n==============================================")
            print(f"[Stage] SHORT GENERATION @ {datetime.now().isoformat(timespec='seconds')}")
            print("==============================================")
            print(f"\n[short] Generating 60s vertical video...")
            t0 = time.time()
            try:
                short_path = generate_short(run_dir=d["root"])
            except Exception as e:
                print("Short generation error:", e)
                import traceback
                traceback.print_exc()
                short_path = None
            t1 = time.time()
        sys.stdout = _stdout

        if short_path:
            summary["stages"].append({
                "name": "short_generation",
                "status": "ok",
                "duration_sec": round(t1 - t0, 3),
                "artifact": str(short_path),
            })
            _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
            console.print(f"[green]✅ Short generated: {short_path}[/green]")
        else:
            summary["stages"].append({
                "name": "short_generation",
                "status": "failed",
                "duration_sec": round(t1 - t0, 3),
            })
            _save_summary(d["root"], summary)  # ← CRITICAL: Save even on failure
            console.print("[yellow]⚠️ Short generation failed (non-critical, continuing)[/yellow]")

    # 12) Upload Short to YouTube (if generated successfully)
    short_video_id = None  # Initialize to prevent unbound variable error
    if short_path and short_path.exists():
        console.rule("[bold]12) Upload YouTube Short")

        # Check if stage already completed (or needs retry)
        if not _should_retry_stage(d["root"], "short_upload", failed_stage):
            console.print("[green]✓ Short upload stage already completed (skipping)[/green]")
            # Try to get short_video_id from database or output.titles.json
            try:
                titles_json = d["root"] / "output.titles.json"
                if titles_json.exists():
                    tj = json.loads(titles_json.read_text(encoding="utf-8"))
                    short_video_id = tj.get("short_youtube_video_id") or tj.get("short_video_id")
            except Exception:
                pass
        else:
            _stdout = sys.stdout

            # Prepare short metadata with main video link
            try:
                with (d["root"] / "output.titles.json").open("r", encoding="utf-8") as f:
                    metadata = json.load(f)

                book_name = metadata.get("main_title", "Unknown Book")

                # Get main video URL
                main_video_url = f"https://youtube.com/watch?v={video_id}" if video_id else None

                # Read short script for description
                short_script_path = d["root"] / "short_script.txt"
                short_script = ""
                if short_script_path.exists():
                    with short_script_path.open("r", encoding="utf-8") as f:
                        short_script = f.read().strip()

                # Build short description with main video link
                short_description = f"{short_script}\n\n"
                if main_video_url:
                    short_description += f"📖 Watch Full Summary:\n{main_video_url}\n\n"
                else:
                    short_description += f"📖 Watch Full Summary on our channel\n\n"

                short_description += f"#shorts #books #booksummary #{book_name.replace(' ', '')}"

                # Create hook from first sentence
                hook = short_script.split('.')[0] if '.' in short_script else short_script[:50]
                short_title = f"{hook[:50]}... - {book_name}"

                # Create temporary titles JSON for short
                short_titles_json = d["root"] / "short_titles.json"
                short_metadata = {
                    "youtube_title": short_title,
                    "youtube_description": short_description,
                    "TAGS": metadata.get("TAGS", []) + ["shorts"],
                    "main_title": book_name,
                    "author_name": metadata.get("author_name"),
                    "is_short": True,  # Flag for upload logic
                    "video_filename": "short_final.mp4"  # Explicit filename for shorts
                }

                with short_titles_json.open("w", encoding="utf-8") as f:
                    json.dump(short_metadata, f, ensure_ascii=False, indent=2)

                console.print(f"[cyan]Short Title: {short_title}[/cyan]")
                console.print(f"[cyan]Short Description: {short_description[:100]}...[/cyan]")

            except Exception as e:
                console.print(f"[yellow]Failed to prepare short metadata: {e}[/yellow]")
                short_titles_json = None

            # Upload short
            if short_titles_json:
                attempt = 0
                while True:
                    attempt += 1
                    with combined_log.open("a", encoding="utf-8") as lf:
                        sys.stdout = TeeWriter(_stdout, lf)
                        print("\n\n==============================================")
                        print(f"[Stage] SHORT UPLOAD attempt {attempt} @ {datetime.now().isoformat(timespec='seconds')}")
                        print("==============================================")
                        print(f"\n[short upload] attempt {attempt}...")
                        t0 = time.time()
                        try:
                            short_video_id = upload_main(
                                run_dir=d["root"],
                                titles_json=short_titles_json,
                                secrets_dir=Path("secrets"),
                                privacy_status="public",  # Always public for shorts
                                is_short=True,  # Mark as short to use correct database field
                            )
                        except Exception as e:
                            print("Short upload error:", e)
                            import traceback
                            traceback.print_exc()
                            short_video_id = None
                        t1 = time.time()
                    sys.stdout = _stdout

                    if short_video_id:
                        summary["stages"].append({
                            "name": "short_upload",
                            "status": "ok",
                            "duration_sec": round(t1 - t0, 3),
                            "artifact": f"https://youtube.com/watch?v={short_video_id}",
                        })
                        _save_summary(d["root"], summary)  # ← CRITICAL: Save after stage completion
                        console.print(f"[green]✅ Short uploaded: https://youtube.com/watch?v={short_video_id}[/green]")

                        # Save short video ID to metadata
                        try:
                            with (d["root"] / "output.titles.json").open("r", encoding="utf-8") as f:
                                metadata_update = json.load(f)
                            metadata_update["short_video_id"] = short_video_id
                            metadata_update["short_video_url"] = f"https://youtube.com/watch?v={short_video_id}"
                            with (d["root"] / "output.titles.json").open("w", encoding="utf-8") as f:
                                json.dump(metadata_update, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass

                        break

                    if attempt >= 3:  # Max 3 attempts for shorts upload
                        console.print("[red]❌ Short upload failed after 3 attempts - CRITICAL STAGE FAILED[/red]")
                        summary["stages"].append({
                            "name": "short_upload",
                            "status": "failed",
                            "duration_sec": round(t1 - t0, 3),
                        })
                        _save_summary(d["root"], summary)  # ← CRITICAL: Save even on failure
                        # CRITICAL: Raise error to prevent marking book as "done"
                        raise RuntimeError(f"Short upload failed after 3 attempts. Book incomplete - short not uploaded.")

                    sleep_s = min(30, 5 * attempt)
                    console.print(f"[yellow]Short upload failed (attempt {attempt}). Retrying in {sleep_s}s...[/yellow]")
                    time.sleep(sleep_s)

    # Final: Update database status to "done" with YouTube URLs
    # CRITICAL: Only reached if ALL stages succeeded (including short upload)
    try:
        from src.infrastructure.adapters.database import update_book_status

        # Get book metadata
        meta = {}
        try:
            with (d["root"] / "output.titles.json").open("r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            pass

        book_name = meta.get("main_title")
        author_name = meta.get("author_name")
        main_video_url = f"https://youtube.com/watch?v={video_id}" if video_id else None
        short_video_url = f"https://youtube.com/watch?v={short_video_id}" if short_video_id else None

        if book_name:
            # CRITICAL: Only update to "done" if we have BOTH main video AND short
            if video_id and short_video_id:
                update_book_status(
                    book_name=book_name,
                    author_name=author_name,
                    status="done",
                    youtube_url=main_video_url,
                    short_url=short_video_url
                )
                console.print(f"[green]✅ Book complete: Main video + Short uploaded successfully[/green]")
            else:
                # Incomplete - keep status as "processing"
                missing = []
                if not video_id:
                    missing.append("main video")
                if not short_video_id:
                    missing.append("short")
                console.print(f"[yellow]⚠️ Book incomplete - missing: {', '.join(missing)}[/yellow]")
                console.print(f"[yellow]Status remains 'processing' - folder NOT deleted[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠️ Failed to update database status: {e}[/yellow]")

    # CRITICAL FIX: Smart cleanup based on database status
    console.rule("[bold]🗑️ Cleanup")
    print("\n🧹 Checking cleanup policy...")
    try:
        _cleanup_successful_run(d["root"], debug=True)
    except Exception as e:
        console.print(f"[yellow]⚠️ Cleanup check failed (keeping folder by default): {e}[/yellow]")


if __name__ == "__main__":
    app()
