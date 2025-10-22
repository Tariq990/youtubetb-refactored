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
    t.add_row("2", "📚 Batch Process from books.txt (Multiple Books)")
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
    t.add_row("14", "Exit")
    console.print(t)


def pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(f"\n{msg}")
    except KeyboardInterrupt:
        pass


def run_api_check():
    """Run comprehensive API and requirements check"""
    console.clear()
    console.rule("[bold cyan]� API Keys Validation")
    console.print("[dim]Testing all required API keys for the pipeline...[/dim]\n")

    try:
        from src.infrastructure.adapters.api_validator import validate_apis_before_run

        # Run validation
        all_ok = validate_apis_before_run()

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

        # Run batch processing
        batch_script = repo_root() / "src" / "presentation" / "cli" / "run_batch.py"
        subprocess.run([py(), str(batch_script)], cwd=repo_root())

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

        model = _configure_model(config_dir)
        if model:
            console.print(f"[cyan]Getting official book name for: {query}[/cyan]")
            book_name, author_name = _get_official_book_name(model, query, prompts)

            if book_name:
                console.print(f"[green]✅ Book: {book_name}[/green]")
                console.print(f"[green]✅ Author: {author_name or 'Unknown'}[/green]")

                # Get playlist category
                console.print(f"[cyan]Classifying book into playlist...[/cyan]")
                playlist = _get_book_playlist(model, book_name, author_name, prompts)
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
        subprocess.run([py(), "2_transcribe_youtube.py", url], cwd=repo_root())
    else:
        subprocess.run([py(), "2_transcribe_youtube.py"], cwd=repo_root())


def run_process():
    p = Prompt.ask("Transcript path (blank = auto-detect)", default="")
    path: Optional[Path] = Path(p) if p.strip() else default_transcript_path()
    if not path or not path.exists():
        console.print("[red]Transcript not found. Provide a valid path.[/red]")
        return
    subprocess.run([py(), "3_process_script.py", str(path)], cwd=repo_root())


def run_tts():
    p = Prompt.ask("Text path for TTS (blank = auto-detect script/translate)", default="")
    path: Optional[Path] = Path(p) if p.strip() else default_tts_text_path()
    if not path or not path.exists():
        console.print("[red]Text file not found. Provide a valid path.[/red]")
        return
    subprocess.run([py(), "4_tts.py", str(path)], cwd=repo_root())


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
            "5render_video.py",
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
    subprocess.run([py(), "6_merge_audio_video.py", "--run", str(sel)], cwd=repo_root())


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    while True:
        console.clear()
        header()
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"], default="1")
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
                console.print("[bold yellow]Goodbye![/bold yellow]")
                return 0
        except KeyboardInterrupt:
            console.print("\n[red]Canceled by user.[/red]")
        pause()


if __name__ == "__main__":
    raise SystemExit(main())
