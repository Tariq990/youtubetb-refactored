from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.prompt import Prompt
from rich.table import Table
from rich import box


console = Console()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


# Add repo root to sys.path if not already there (for direct script execution)
_repo = repo_root()
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))


def runs_dir() -> Path:
    return repo_root() / "runs"


def read_latest_run_path() -> Optional[Path]:
    p = runs_dir() / "latest" / "path.txt"
    try:
        if p.exists():
            content = p.read_text(encoding="utf-8").strip()
            if content:
                rp = Path(content)
                if rp.exists():
                    return rp
    except Exception:
        pass
    return None


def newest_run_dir() -> Optional[Path]:
    base = runs_dir()
    if not base.exists():
        return None
    dirs = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
    if not dirs:
        return None
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return dirs[0]


def default_transcript_path() -> Optional[Path]:
    # Try pointer
    latest = read_latest_run_path()
    if latest is not None:
        p = latest / "transcribe.txt"
        if p.exists():
            return p
    # Try direct latest folder
    direct = runs_dir() / "latest" / "transcribe.txt"
    if direct.exists():
        return direct
    # Try newest run
    newest = newest_run_dir()
    if newest is not None:
        p = newest / "transcribe.txt"
        if p.exists():
            return p
    return None


def default_tts_text_path() -> Optional[Path]:
    # Try pointer
    latest = read_latest_run_path()
    if latest is not None:
        for name in ("script.txt", "translate.txt"):
            p = latest / name
            if p.exists():
                return p
    # Try direct latest folder
    for name in ("script.txt", "translate.txt"):
        p = runs_dir() / "latest" / name
        if p.exists():
            return p
    # Try newest run
    newest = newest_run_dir()
    if newest is not None:
        for name in ("script.txt", "translate.txt"):
            p = newest / name
            if p.exists():
                return p
    return None


def default_titles_json_path() -> Optional[Path]:
    # Try pointer
    latest = read_latest_run_path()
    if latest is not None:
        p = latest / "output.titles.json"
        if p.exists():
            return p
    # Try direct latest folder
    direct = runs_dir() / "latest" / "output.titles.json"
    if direct.exists():
        return direct
    # Try newest run
    newest = newest_run_dir()
    if newest is not None:
        p = newest / "output.titles.json"
        if p.exists():
            return p
    return None


def py() -> str:
    return sys.executable


def header() -> None:
    title = Align.center("YouTube Book Video Pipeline", vertical="middle")
    console.print(Panel(title, style="bold cyan", expand=True))
    t = Table(box=box.SIMPLE_HEAVY, expand=True)
    t.add_column("Option", justify="center", style="bold yellow")
    t.add_column("Action", style="white")
    t.add_row("0", "🔍 Check APIs & Requirements (Comprehensive Test)")
    t.add_row("1", "Run FULL pipeline")
    t.add_row("2", "📚 Batch Process from books.txt (Auto-Continue Support)")
    t.add_row("3", "📺 Process Entire YouTube Channel (All Videos)")
    t.add_row("4", "Search only")
    t.add_row("5", "Transcribe only")
    t.add_row("6", "Process only")
    t.add_row("7", "TTS only")
    t.add_row("8", "Render only")
    t.add_row("9", "Merge Audio + Video (loop video to audio length)")
    t.add_row("10", "YouTube Metadata only (Title + Description)")
    t.add_row("11", "Generate Thumbnail only")
    t.add_row("12", "Upload to YouTube (requires secrets/client_secret.json)")
    t.add_row("13", "Resume pipeline from last successful stage")
    t.add_row("14", "🔄 Sync Database from YouTube Channel")
    t.add_row("15", "️ Clean Up (Delete runs, tmp, database, pexels)")
    t.add_row("16", "🍪 Cookies & API Helper (JSON→Netscape, Test APIs)")
    t.add_row("17", "🔓 Decrypt Secrets (For deployment on new machines)")
    t.add_row("18", "🔄 Force Pull from GitHub (Overwrite local changes)")
    t.add_row("19", "Exit")
    console.print(t)


def pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(f"\n{msg}")
    except KeyboardInterrupt:
        pass


def run_api_check():
    """Run comprehensive API and requirements check"""
    console.clear()
    console.rule("[bold cyan]🔍 System Environment & API Validation")
    console.print("[dim]Testing system dependencies and API keys...[/dim]\n")

    # Step 1: Run check_system.py first
    console.print("[bold cyan]Step 1: System Environment Check[/bold cyan]")
    console.print("="*60)
    
    check_system_script = repo_root() / "check_system.py"
    
    if check_system_script.exists():
        try:
            result = subprocess.run(
                [py(), str(check_system_script)],
                cwd=repo_root(),
                capture_output=False  # Show output directly
            )
            
            if result.returncode != 0:
                console.print("\n[yellow]⚠️  System check found some issues.[/yellow]")
            else:
                console.print("\n[green]✅ System environment check passed![/green]")
                
        except Exception as e:
            console.print(f"[red]❌ Error running system check: {e}[/red]")
    else:
        console.print(f"[yellow]⚠️  check_system.py not found at {check_system_script}[/yellow]")
        console.print("[dim]Skipping system environment check...[/dim]")
    
    console.print("\n" + "="*60 + "\n")
    
    # Step 2: Run API validation
    console.print("[bold cyan]Step 2: API Keys Validation[/bold cyan]")
    console.print("="*60 + "\n")

    try:
        from src.infrastructure.adapters.api_validator import APIValidator

        # Run validation in VERBOSE mode (not quiet)
        validator = APIValidator(quiet=False)
        all_ok = validator.validate_all()

        if all_ok:
            console.print("\n[bold green]✅ All API checks passed! Pipeline is ready to run.[/bold green]")
        else:
            console.print("\n[bold red]❌ Some API checks failed. Fix the issues above before running pipeline.[/bold red]")

    except ImportError as e:
        console.print(f"[red]❌ Error: Could not load API checker module[/red]")
        console.print(f"[yellow]Details: {e}[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error running API checks: {e}[/red]")

    pause()


def run_cleanup():
    """Clean up runs, tmp, database, and pexels data"""
    console.clear()
    console.rule("[bold red]🗑️ Clean Up System Files")
    
    console.print("[yellow]⚠️  WARNING: This will delete:[/yellow]")
    console.print("   • [red]runs/[/red] - All processed videos and outputs")
    console.print("   • [red]tmp/[/red] - Temporary files")
    console.print("   • [red]database.json[/red] - Local database (can resync from YouTube)")
    console.print("   • [red]used_pexels_videos.json[/red] - Pexels video tracking")
    console.print("\n[dim]Note: This will NOT delete secrets/ or config/[/dim]\n")
    
    confirm = Prompt.ask(
        "Are you sure you want to delete all these files?",
        choices=["yes", "no"],
        default="no"
    )
    
    if confirm.lower() != "yes":
        console.print("[yellow]Cleanup canceled.[/yellow]")
        return
    
    import shutil
    import os
    
    deleted = []
    errors = []
    
    # List of items to delete
    items_to_delete = [
        ("runs/", "directory"),
        ("tmp/", "directory"),
        ("database.json", "file"),  # Fixed: database.json is in root, not src/
        ("used_pexels_videos.json", "file")
    ]
    
    console.print("\n[cyan]Starting cleanup...[/cyan]\n")
    
    for item_path, item_type in items_to_delete:
        full_path = repo_root() / item_path
        
        try:
            if item_type == "directory" and full_path.exists():
                # Delete directory
                shutil.rmtree(full_path)
                size = "directory"
                console.print(f"[green]✓[/green] Deleted {item_path}")
                deleted.append(item_path)
                
            elif item_type == "file" and full_path.exists():
                # Delete file
                file_size = full_path.stat().st_size
                full_path.unlink()
                size_kb = file_size / 1024
                console.print(f"[green]✓[/green] Deleted {item_path} ({size_kb:.1f} KB)")
                deleted.append(item_path)
                
            else:
                console.print(f"[dim]○[/dim] {item_path} (not found)")
                
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to delete {item_path}: {e}")
            errors.append((item_path, str(e)))
    
    # Summary
    console.print("\n" + "="*60)
    if deleted:
        console.print(f"[green]✅ Successfully deleted {len(deleted)} items:[/green]")
        for item in deleted:
            console.print(f"   • {item}")
    
    if errors:
        console.print(f"\n[red]❌ Failed to delete {len(errors)} items:[/red]")
        for item, error in errors:
            console.print(f"   • {item}: {error}")
    
    if not deleted and not errors:
        console.print("[yellow]No files found to delete.[/yellow]")
    
    console.print("="*60)
    
    if deleted:
        console.print("\n[cyan]💡 Tip: Database can be restored by running:[/cyan]")
        console.print("   [dim]Option 14: Sync Database from YouTube Channel[/dim]")
    
    pause()


def run_youtube_sync():
    """Manually sync database from YouTube channel"""
    console.clear()
    console.rule("[bold cyan]🔄 Sync Database from YouTube")
    
    console.print("[dim]This will sync your local database with videos from your YouTube channel.[/dim]")
    console.print("[dim]Use this to detect duplicates after uploading from another device.[/dim]\n")
    
    try:
        from src.infrastructure.adapters.database import sync_database_from_youtube, _load_database
        
        # Show current database status
        db = _load_database()
        current_count = len(db.get("books", []))
        console.print(f"[cyan]Current database:[/cyan] {current_count} books\n")
        
        # Confirm sync
        if current_count > 0:
            confirm = Prompt.ask(
                "Database already has data. Sync will add missing books from YouTube. Continue?",
                choices=["y", "n"],
                default="y"
            )
            if confirm.lower() != "y":
                console.print("[yellow]Sync canceled.[/yellow]")
                return
        
        console.print("\n[cyan]Syncing from YouTube channel...[/cyan]")
        
        success = sync_database_from_youtube()
        
        if success:
            # Show new count
            db_after = _load_database()
            new_count = len(db_after.get("books", []))
            added = new_count - current_count
            
            console.print(f"\n[bold green]✅ Sync completed successfully![/bold green]")
            console.print(f"[cyan]Total books in database:[/cyan] {new_count}")
            if added > 0:
                console.print(f"[green]Books added from YouTube:[/green] {added}")
            else:
                console.print(f"[dim]No new books found (database was up to date)[/dim]")
        else:
            console.print(f"\n[yellow]⚠️  YouTube channel has no videos yet[/yellow]")
            console.print(f"[dim]This is normal for new channels.[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error during sync: {e}[/red]")
    
    pause()


def run_cookies_helper():
    """Launch cookies & API helper tool"""
    console.clear()
    console.rule("[bold cyan]🍪 Cookies & API Helper")
    
    console.print("[dim]Professional tool for managing cookies and API keys[/dim]")
    console.print("[dim]Features: JSON→Netscape conversion, API testing, multi-file fallback[/dim]\n")
    
    cookies_helper_script = repo_root() / "cookies_helper.py"
    
    if not cookies_helper_script.exists():
        console.print(f"[red]❌ cookies_helper.py not found at: {cookies_helper_script}[/red]")
        pause()
        return
    
    try:
        # Run the script with python
        subprocess.run([py(), str(cookies_helper_script)], cwd=repo_root())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cookies helper closed.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error running cookies helper: {e}[/red]")
    
    pause()


def run_decrypt_secrets():
    """Launch decrypt secrets script for deployment"""
    console.clear()
    console.rule("[bold cyan]🔓 Decrypt Secrets")
    
    console.print("[dim]Decrypt encrypted secrets from GitHub for deployment on new machines[/dim]")
    console.print("[dim]Required files: secrets_encrypted/*.enc + ENCRYPTION_KEY in environment[/dim]\n")
    
    decrypt_script = repo_root() / "scripts" / "decrypt_secrets.py"
    
    if not decrypt_script.exists():
        console.print(f"[red]❌ decrypt_secrets.py not found at: {decrypt_script}[/red]")
        pause()
        return
    
    # Check if encrypted files exist
    encrypted_dir = repo_root() / "secrets_encrypted"
    if not encrypted_dir.exists() or not any(encrypted_dir.glob("*.enc")):
        console.print(f"[yellow]⚠️  No encrypted files found in secrets_encrypted/[/yellow]")
        console.print("[dim]This is normal if secrets are not encrypted yet.[/dim]")
        pause()
        return
    
    console.print(f"[cyan]Found encrypted files in: {encrypted_dir}[/cyan]\n")
    
    try:
        # Run the decryption script
        result = subprocess.run([py(), str(decrypt_script)], cwd=repo_root())
        
        if result.returncode == 0:
            console.print("\n[green]✅ Secrets decrypted successfully![/green]")
        else:
            console.print("\n[yellow]⚠️  Decryption completed with warnings.[/yellow]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Decryption canceled.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error running decryption: {e}[/red]")
    
    pause()


def run_force_pull():
    """Force pull from GitHub (overwrites local changes)"""
    console.clear()
    console.rule("[bold red]🔄 Force Pull from GitHub")
    
    console.print("[bold red]⚠️  WARNING: This will OVERWRITE all local changes![/bold red]")
    console.print("[yellow]This operation will:[/yellow]")
    console.print("   1. Fetch latest code from GitHub (origin/master)")
    console.print("   2. Reset all local files to match GitHub")
    console.print("   3. Delete any uncommitted changes")
    console.print("\n[dim]Use this when you want to sync with the latest code and don't care about local edits.[/dim]\n")
    
    confirm = Prompt.ask(
        "Are you SURE you want to overwrite all local changes?",
        choices=["yes", "no"],
        default="no"
    )
    
    if confirm.lower() != "yes":
        console.print("[yellow]Force pull canceled.[/yellow]")
        pause()
        return
    
    try:
        console.print("\n[cyan]Step 1: Fetching from GitHub...[/cyan]")
        result1 = subprocess.run(
            ["git", "fetch", "origin", "master"],
            cwd=repo_root(),
            capture_output=True,
            text=True
        )
        
        if result1.returncode == 0:
            console.print("[green]✓ Fetch completed[/green]")
        else:
            console.print(f"[red]✗ Fetch failed: {result1.stderr}[/red]")
            pause()
            return
        
        console.print("\n[cyan]Step 2: Resetting local files to match GitHub...[/cyan]")
        result2 = subprocess.run(
            ["git", "reset", "--hard", "origin/master"],
            cwd=repo_root(),
            capture_output=True,
            text=True
        )
        
        if result2.returncode == 0:
            console.print("[green]✓ Reset completed[/green]")
            console.print(result2.stdout.strip())
        else:
            console.print(f"[red]✗ Reset failed: {result2.stderr}[/red]")
            pause()
            return
        
        console.print("\n[cyan]Step 3: Cleaning untracked files...[/cyan]")
        result3 = subprocess.run(
            ["git", "clean", "-fd"],
            cwd=repo_root(),
            capture_output=True,
            text=True
        )
        
        if result3.returncode == 0:
            console.print("[green]✓ Clean completed[/green]")
            if result3.stdout.strip():
                console.print(result3.stdout.strip())
        else:
            console.print(f"[yellow]⚠️  Clean warning: {result3.stderr}[/yellow]")
        
        console.print("\n" + "="*60)
        console.print("[bold green]✅ Force pull completed successfully![/bold green]")
        console.print("[green]Your local code now matches GitHub master branch.[/green]")
        console.print("="*60)
        
    except FileNotFoundError:
        console.print("[red]❌ Git not found. Make sure Git is installed and in PATH.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error during force pull: {e}[/red]")
    
    pause()


def run_full():
    book = Prompt.ask("Enter book title", default="").strip()
    if not book:
        console.print("[red]Book title is required for full run.[/red]")
        return
    # Only use the book title now (author removed by user request)
    query = book
    pipeline_script = repo_root() / "src" / "presentation" / "cli" / "run_pipeline.py"
    subprocess.run([py(), str(pipeline_script), query], cwd=repo_root())


def run_batch():
    """Run batch processing from books.txt"""
    console.clear()
    console.rule("[bold cyan]📚 Batch Processing")

    books_file = repo_root() / "books.txt"

    if not books_file.exists():
        console.print(f"[red]❌ File not found: {books_file}[/red]")
        console.print("[yellow]Create books.txt in the root directory with book names (one per line)[/yellow]")
        console.print("\nExample content:")
        console.print("  الأمير")
        console.print("  فن الحرب")
        console.print("  التفكير السريع والبطيء")
        pause()
        return

    # Show file preview
    try:
        lines = books_file.read_text(encoding='utf-8').splitlines()
        books = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]

        console.print(f"\n[cyan]📂 Found {len(books)} books in books.txt:[/cyan]")
        for idx, book in enumerate(books[:10], start=1):  # Show first 10
            console.print(f"  {idx}. {book}")
        if len(books) > 10:
            console.print(f"  ... and {len(books) - 10} more")

        console.print(f"\n[yellow]⚠️ This will process {len(books)} books sequentially.[/yellow]")
        console.print("[yellow]   This may take several hours![/yellow]")

        confirm = Prompt.ask("\nContinue?", choices=["yes", "no"], default="no")
        if confirm != "yes":
            console.print("[red]Cancelled[/red]")
            return

        # Ask about auto-continue mode
        console.print("\n[cyan]📌 Auto-Continue Mode:[/cyan]")
        console.print("[dim]   • ON: Skip failed books automatically (no prompts)[/dim]")
        console.print("[dim]   • OFF: Ask what to do when a book fails[/dim]")
        auto_mode = Prompt.ask("\nEnable Auto-Continue mode?", choices=["yes", "no"], default="yes")

        # Run batch processing
        batch_script = repo_root() / "src" / "presentation" / "cli" / "run_batch.py"
        cmd = [py(), str(batch_script)]
        if auto_mode == "yes":
            cmd.append("--auto-continue")
        subprocess.run(cmd, cwd=repo_root())

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

    pause()


def run_channel():
    """Run channel processing"""
    console.clear()
    console.rule("[bold cyan]📺 YouTube Channel Processor")

    channel_url = Prompt.ask(
        "\nEnter YouTube channel URL",
        default="https://youtube.com/@"
    ).strip()

    if not channel_url or channel_url == "https://youtube.com/@":
        console.print("[red]❌ Channel URL is required[/red]")
        pause()
        return

    # Run channel processor
    channel_script = repo_root() / "src" / "presentation" / "cli" / "process_channel.py"
    subprocess.run([py(), str(channel_script), channel_url], cwd=repo_root())

    pause()


def run_search():
    book = Prompt.ask("Enter book title", default="").strip()
    if not book:
        console.print("[red]Book title is required for search.[/red]")
        return
    query = book

    # Stage 0: Get early metadata and rename folder
    console.print("[yellow]Running early metadata extraction and folder rename...[/yellow]")
    import subprocess
    import json
    from pathlib import Path
    import time

    # Create a temporary run for early metadata
    run_id = time.strftime("%Y-%m-%d_%H-%M-%S")
    run_root = runs_dir() / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    # Save input query
    (run_root / "input_name.txt").write_text(query, encoding="utf-8")

    # Run early metadata stage using process.py helpers
    try:
        from src.infrastructure.adapters.process import _configure_model, _get_official_book_name, _get_book_playlist
        from src.infrastructure.adapters.database import check_book_exists, add_book
        import json as _json
        import re

        config_dir = repo_root() / "config"
        prompts = {}
        try:
            prompts_json = config_dir / "prompts.json"
            if prompts_json.exists():
                prompts = _json.loads(prompts_json.read_text(encoding="utf-8"))
        except Exception:
            pass

        model_result = _configure_model(config_dir)
        
        # Unpack tuple (model, api_keys)
        if isinstance(model_result, tuple):
            model, api_keys = model_result
        else:
            model = model_result
            api_keys = None
        
        if model:
            console.print(f"[cyan]Getting official book name for: {query}[/cyan]")
            book_name, author_name = _get_official_book_name(model, query, prompts, api_keys=api_keys)

            if book_name:
                console.print(f"[green]✅ Book: {book_name}[/green]")
                console.print(f"[green]✅ Author: {author_name or 'Unknown'}[/green]")

                # Get playlist category
                console.print(f"[cyan]Classifying book into playlist...[/cyan]")
                playlist = _get_book_playlist(model, book_name, author_name, prompts, api_keys=api_keys)
                console.print(f"[green]✅ Playlist: {playlist}[/green]")

                # Check if book already exists in database
                existing = check_book_exists(book_name, author_name)
                if existing:
                    status = existing.get('status', 'unknown')

                    # Display existing book info
                    console.print(f"\n[bold yellow]⚠️ Book found in database![/bold yellow]")
                    console.print(f"[yellow]Title:[/yellow] {existing.get('main_title')}")
                    console.print(f"[yellow]Author:[/yellow] {existing.get('author_name', 'Unknown')}")
                    console.print(f"[yellow]Playlist:[/yellow] {existing.get('playlist', 'Unknown')}")
                    console.print(f"[yellow]Date:[/yellow] {existing.get('date_added', 'Unknown')}")
                    console.print(f"[yellow]Status:[/yellow] [bold]{status}[/bold]")
                    if existing.get('youtube_url'):
                        console.print(f"[yellow]YouTube:[/yellow] {existing['youtube_url']}")
                    if existing.get('short_url'):
                        console.print(f"[yellow]Short:[/yellow] {existing['short_url']}")

                    # Decision based on status
                    if status == 'done':
                        # Book is complete → Stop and clean up
                        console.print(f"\n[bold red]❌ Book is already COMPLETE and uploaded![/bold red]")
                        console.print(f"[red]Search stopped to prevent duplicate processing.[/red]")

                        # Clean up: Delete the newly created run folder
                        console.print(f"[dim]Cleaning up temporary run folder...[/dim]")
                        try:
                            import shutil
                            shutil.rmtree(run_root)
                            console.print(f"[green]✅ Deleted run folder: {run_root.name}[/green]")
                        except Exception as e:
                            console.print(f"[yellow]⚠️ Could not delete run folder: {e}[/yellow]")

                        console.print(f"\n[cyan]💡 Tip: This book is already done. Use a different book title.[/cyan]")
                        console.print("[cyan]Press Enter to continue...[/cyan]")
                        input()
                        return

                    elif status == 'processing':
                        # Book is incomplete → Find old run folder and resume from there
                        console.print(f"\n[bold cyan]♻️ Book exists but is INCOMPLETE (status: processing).[/bold cyan]")
                        console.print(f"[cyan]This means a previous run failed or was interrupted.[/cyan]")

                        # Search for existing run folder with this book
                        console.print(f"\n[dim]Searching for existing run folder...[/dim]")
                        old_run_folder = None
                        runs_path = runs_dir()  # Call the function to get Path
                        for rf in runs_path.iterdir():
                            if not rf.is_dir() or rf.name == "latest":
                                continue

                            # Check if this folder has the same book
                            old_titles_json = rf / "output.titles.json"
                            if old_titles_json.exists():
                                try:
                                    import json as _json
                                    old_data = _json.loads(old_titles_json.read_text(encoding="utf-8"))
                                    if (old_data.get("main_title") == book_name and
                                        old_data.get("author_name") == author_name):
                                        old_run_folder = rf
                                        break
                                except Exception:
                                    continue

                        if old_run_folder:
                            # Found old folder → Delete new folder and use old one
                            console.print(f"[green]✅ Found existing run folder: {old_run_folder.name}[/green]")
                            console.print(f"[cyan]Resuming from last successful stage in existing folder...[/cyan]")

                            # Delete the newly created folder (we don't need it)
                            console.print(f"[dim]Deleting temporary new folder: {run_root.name}[/dim]")
                            try:
                                import shutil
                                shutil.rmtree(run_root)
                            except Exception:
                                pass

                            # Use old folder
                            run_root = old_run_folder

                            console.print(f"[green]✅ Resuming in folder: {old_run_folder.name}[/green]\n")
                        else:
                            # No old folder found → Continue with new folder
                            console.print(f"[yellow]⚠️ Could not find existing run folder.[/yellow]")
                            console.print(f"[cyan]Continuing with new folder: {run_root.name}[/cyan]\n")

                    else:
                        # Unknown status → Warn but continue
                        console.print(f"\n[bold yellow]⚠️ Book exists with unknown status: {status}[/bold yellow]")
                        console.print(f"[yellow]Continuing with search, but this may create a duplicate entry.[/yellow]\n")
                        # Continue with search
                    input()
                    return

                # Save to output.titles.json (same as pipeline Stage 0)
                titles_data = {
                    "main_title": book_name,
                    "author_name": author_name,
                    "playlist": playlist,
                }
                (run_root / "output.titles.json").write_text(_json.dumps(titles_data, ensure_ascii=False, indent=2), encoding="utf-8")
                console.print(f"[green]✅ Saved to output.titles.json[/green]")

                # Rename folder
                def slugify(s: str) -> str:
                    s = s.encode("ascii", "ignore").decode("ascii")
                    s = re.sub(r"[^A-Za-z0-9\-\_ ]+", "", s)
                    s = re.sub(r"\s+", "-", s).strip("-_")
                    return re.sub(r"-+", "-", s)[:60]

                slug = slugify(book_name)
                if slug:
                    new_root = runs_dir() / f"{run_id}_{slug}"
                    if new_root.exists():
                        for i in range(1, 100):
                            candidate = runs_dir() / f"{run_id}_{slug}-{i}"
                            if not candidate.exists():
                                new_root = candidate
                                break
                    run_root.rename(new_root)
                    run_root = new_root
                    console.print(f"[green]✅ Renamed: {run_id} → {new_root.name}[/green]")

                    # Update latest
                    latest = runs_dir() / "latest"
                    latest.mkdir(exist_ok=True)
                    (latest / "path.txt").write_text(str(new_root.resolve()), encoding="utf-8")

                    # Add to database with playlist
                    add_book(book_name, author_name, new_root.name, status="processing", playlist=playlist)
            else:
                console.print("[yellow]⚠️ Could not extract book name, folder not renamed[/yellow]")
        else:
            console.print("[yellow]⚠️ Gemini not configured[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in early metadata: {e}[/red]")
        import traceback
        traceback.print_exc()

    # Now run the actual search in the SAME folder
    console.print("[cyan]Running YouTube search...[/cyan]")
    # Import search_main directly to use the same run_root
    from src.infrastructure.adapters.search import main as search_main
    search_main(query=query, output_dir=run_root)


def run_transcribe():
    url = Prompt.ask("Enter YouTube URL (leave blank to be prompted)", default="")
    if url.strip():
        subprocess.run([py(), "-m", "src.infrastructure.adapters.transcribe", url], cwd=repo_root())
    else:
        subprocess.run([py(), "-m", "src.infrastructure.adapters.transcribe"], cwd=repo_root())


def run_process():
    p = Prompt.ask("Transcript path (blank = auto-detect)", default="")
    path: Optional[Path] = Path(p) if p.strip() else default_transcript_path()
    if not path or not path.exists():
        console.print("[red]Transcript not found. Provide a valid path.[/red]")
        return
    subprocess.run([py(), "-m", "src.infrastructure.adapters.process", str(path)], cwd=repo_root())


def run_tts():
    p = Prompt.ask("Text path for TTS (blank = auto-detect script/translate)", default="")
    path: Optional[Path] = Path(p) if p.strip() else default_tts_text_path()
    if not path or not path.exists():
        console.print("[red]Text file not found. Provide a valid path.[/red]")
        return
    subprocess.run([py(), "-m", "src.infrastructure.adapters.tts", str(path)], cwd=repo_root())


def run_render():
    # Build selectable list of runs
    base = runs_dir()
    if not base.exists():
        console.print("[red]No runs directory found.[/red]")
        return

    latest_ptr = read_latest_run_path()
    # Gather run folders (excluding 'latest') sorted by mtime desc
    items = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
    items.sort(key=lambda d: d.stat().st_mtime, reverse=True)

    # If latest pointer is valid, put it at top if not already first
    options: list[Path] = []
    labels: list[str] = []
    if latest_ptr and latest_ptr.exists():
        options.append(latest_ptr)
        labels.append(f"latest → {latest_ptr.name}")
        # remove duplicate if present in items
        items = [d for d in items if d.resolve() != latest_ptr.resolve()]

    options.extend(items)
    labels.extend([d.name for d in items])

    if not options:
        console.print("[red]No run folders to render.[/red]")
        return

    # Show table
    t = Table(title="Select run for Render", box=box.SIMPLE_HEAVY, expand=True)
    t.add_column("#", justify="right", style="bold yellow")
    t.add_column("Run folder", style="white")
    for idx, label in enumerate(labels, start=1):
        t.add_row(str(idx), label)
    console.print(t)

    default_choice = "1"
    valid_choices = [str(i) for i in range(1, len(options) + 1)]
    ch = Prompt.ask("Choose run", choices=valid_choices, default=default_choice)
    sel = options[int(ch) - 1]

    out_path = sel / "video_snap.mp4"
    console.print(f"[cyan]Rendering from[/cyan] [bold]{sel.name}[/bold] → [green]{out_path.name}[/green]")
    # Ensure we overwrite any existing preview file
    try:
        if out_path.exists():
            out_path.unlink()
    except Exception:
        pass
    subprocess.run(
        [
            py(),
            "-m",
            "src.infrastructure.adapters.render",
            "--run",
            str(sel),
            "--html",
            "config/template.html",
            "--settings",
            "config/settings.json",
            "--out",
            str(out_path),
        ],
        cwd=repo_root(),
    )


def run_merge():
    # Build selectable list of runs (same as render)
    base = runs_dir()
    if not base.exists():
        console.print("[red]No runs directory found.[/red]")
        return

    latest_ptr = read_latest_run_path()
    items = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
    items.sort(key=lambda d: d.stat().st_mtime, reverse=True)

    options: list[Path] = []
    labels: list[str] = []
    if latest_ptr and latest_ptr.exists():
        options.append(latest_ptr)
        labels.append(f"latest → {latest_ptr.name}")
        items = [d for d in items if d.resolve() != latest_ptr.resolve()]

    options.extend(items)
    labels.extend([d.name for d in items])

    if not options:
        console.print("[red]No run folders to merge.[/red]")
        return

    t = Table(title="Select run for Merge", box=box.SIMPLE_HEAVY, expand=True)
    t.add_column("#", justify="right", style="bold yellow")
    t.add_column("Run folder", style="white")
    for idx, label in enumerate(labels, start=1):
        t.add_row(str(idx), label)
    console.print(t)

    default_choice = "1"
    valid_choices = [str(i) for i in range(1, len(options) + 1)]
    ch = Prompt.ask("Choose run", choices=valid_choices, default=default_choice)
    sel = options[int(ch) - 1]

    console.print(f"[cyan]Merging[/cyan] [bold]{sel.name}[/bold] → uses youtube_title for output filename")
    subprocess.run([py(), "-m", "src.infrastructure.adapters.merge", "--run", str(sel)], cwd=repo_root())


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    while True:
        console.clear()
        header()
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"], default="1")
        console.rule(style="dim")
        try:
            if choice == "0":
                run_api_check()
            elif choice == "1":
                run_full()
            elif choice == "2":
                run_batch()
            elif choice == "3":
                run_channel()
            elif choice == "4":
                run_search()
            elif choice == "5":
                run_transcribe()
            elif choice == "6":
                run_process()
            elif choice == "7":
                run_tts()
            elif choice == "8":
                run_render()
            elif choice == "9":
                run_merge()
            elif choice == "10":
                # YouTube Metadata only (Title + Description)
                p = Prompt.ask("Path to output.titles.json (blank = auto-detect)", default="")
                titles_path: Optional[Path] = Path(p) if p.strip() else default_titles_json_path()
                if not titles_path or not titles_path.exists():
                    console.print("[red]output.titles.json not found. Provide a valid path.[/red]")
                else:
                    metadata_script = repo_root() / "src" / "infrastructure" / "adapters" / "youtube_metadata.py"
                    subprocess.run([py(), str(metadata_script), str(titles_path)], cwd=repo_root())
            elif choice == "11":
                # Generate Thumbnail only
                base = runs_dir()
                if not base.exists():
                    console.print("[red]No runs directory found.[/red]")
                else:
                    latest_ptr = read_latest_run_path()
                    items = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
                    items.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                    options: list[Path] = []
                    labels: list[str] = []
                    if latest_ptr and latest_ptr.exists():
                        options.append(latest_ptr)
                        labels.append(f"latest → {latest_ptr.name}")
                        items = [d for d in items if d.resolve() != latest_ptr.resolve()]
                    options.extend(items)
                    labels.extend([d.name for d in items])
                    if not options:
                        console.print("[red]No run folders found.[/red]")
                    else:
                        t = Table(title="Select run for Thumbnail", box=box.SIMPLE_HEAVY, expand=True)
                        t.add_column("#", justify="right", style="bold yellow")
                        t.add_column("Run folder", style="white")
                        for idx, label in enumerate(labels, start=1):
                            t.add_row(str(idx), label)
                        console.print(t)
                        ch = Prompt.ask("Choose run", choices=[str(i) for i in range(1, len(options) + 1)], default="1")
                        sel = options[int(ch) - 1]
                        thumbnail_script = repo_root() / "src" / "infrastructure" / "adapters" / "thumbnail.py"
                        subprocess.run([py(), str(thumbnail_script), "--run", str(sel)], cwd=repo_root())
            elif choice == "12":
                # Upload to YouTube
                base = runs_dir()
                if not base.exists():
                    console.print("[red]No runs directory found.[/red]")
                else:
                    latest_ptr = read_latest_run_path()
                    items = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
                    items.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                    options: list[Path] = []
                    labels: list[str] = []
                    if latest_ptr and latest_ptr.exists():
                        options.append(latest_ptr)
                        labels.append(f"latest → {latest_ptr.name}")
                        items = [d for d in items if d.resolve() != latest_ptr.resolve()]
                    options.extend(items)
                    labels.extend([d.name for d in items])
                    if not options:
                        console.print("[red]No run folders to upload.[/red]")
                    else:
                        t = Table(title="Select run for Upload", box=box.SIMPLE_HEAVY, expand=True)
                        t.add_column("#", justify="right", style="bold yellow")
                        t.add_column("Run folder", style="white")
                        for idx, label in enumerate(labels, start=1):
                            t.add_row(str(idx), label)
                        console.print(t)
                        ch = Prompt.ask("Choose run", choices=[str(i) for i in range(1, len(options) + 1)], default="1")
                        sel = options[int(ch) - 1]
                        # Auto-set privacy to public (no prompt)
                        priv = "public"
                        # Ask about thumbnail
                        use_thumb = Prompt.ask("Upload with thumbnail?", choices=["y", "n"], default="y")
                        upload_script = repo_root() / "src" / "infrastructure" / "adapters" / "youtube_upload.py"
                        cmd = [py(), str(upload_script), "--run", str(sel), "--privacy", priv]
                        if use_thumb.lower() == "y":
                            cmd.append("--thumbnail")
                        subprocess.run(cmd, cwd=repo_root())
            elif choice == "13":
                # Resume from last successful stage
                base = runs_dir()
                if not base.exists():
                    console.print("[red]No runs directory found.[/red]")
                else:
                    latest_ptr = read_latest_run_path()
                    items = [d for d in base.iterdir() if d.is_dir() and d.name != "latest"]
                    items.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                    options: list[Path] = []
                    labels: list[str] = []
                    if latest_ptr and latest_ptr.exists():
                        options.append(latest_ptr)
                        labels.append(f"latest → {latest_ptr.name}")
                        items = [d for d in items if d.resolve() != latest_ptr.resolve()]
                    options.extend(items)
                    labels.extend([d.name for d in items])
                    if not options:
                        console.print("[red]No run folders to resume.[/red]")
                    else:
                        t = Table(title="Select run to Resume", box=box.SIMPLE_HEAVY, expand=True)
                        t.add_column("#", justify="right", style="bold yellow")
                        t.add_column("Run folder", style="white")
                        for idx, label in enumerate(labels, start=1):
                            t.add_row(str(idx), label)
                        console.print(t)
                        ch = Prompt.ask("Choose run", choices=[str(i) for i in range(1, len(options) + 1)], default="1")
                        sel = options[int(ch) - 1]
                        # Auto-set privacy to public (no prompt)
                        priv = "public"
                        resume_script = repo_root() / "src" / "presentation" / "cli" / "run_resume.py"
                        subprocess.run([py(), str(resume_script), "--run", str(sel), "--privacy", priv], cwd=repo_root())
            elif choice == "14":
                run_youtube_sync()
            elif choice == "15":
                run_cleanup()
            elif choice == "16":
                run_cookies_helper()
            elif choice == "17":
                run_decrypt_secrets()
            elif choice == "18":
                run_force_pull()
            elif choice == "19":
                console.print("[bold yellow]Goodbye![/bold yellow]")
                return 0
        except KeyboardInterrupt:
            console.print("\n[red]Canceled by user.[/red]")
        pause()


if __name__ == "__main__":
    raise SystemExit(main())
