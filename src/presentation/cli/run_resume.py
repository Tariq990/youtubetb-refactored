from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import re
import io
import time
from datetime import datetime
from typing import Optional, List
import argparse

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore

# Add repo root to sys.path BEFORE imports
repo_root = Path(__file__).resolve().parents[3]  # Go up to project root (contains src/)
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Load environment variables from .env and secrets/.env
if load_dotenv is not None:
    # Try loading from root .env first
    root_env = repo_root / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=str(root_env))
    
    # Then load from secrets/.env (will override if keys exist)
    secrets_env = repo_root / "secrets" / ".env"
    if secrets_env.exists():
        load_dotenv(dotenv_path=str(secrets_env))

# Now import from src
from src.infrastructure.adapters.youtube_metadata import main as youtube_metadata_main
from src.infrastructure.adapters.tts import main as tts_main
from src.infrastructure.adapters.render import main as render_main
from src.infrastructure.adapters.merge_av import main as merge_main
from src.infrastructure.adapters.youtube_upload import main as upload_main
from src.infrastructure.adapters.thumbnail import main as thumbnail_main
from src.infrastructure.adapters.short_thumbnail import main as short_thumbnail_main
from src.infrastructure.adapters.shorts_generator import generate_short


STAGE_ORDER: List[str] = [
    "search",
    "transcribe",
    "process",
    "youtube_metadata",
    "tts",
    "render",
    "merge",
    "thumbnail",       # إنشاء ثامبنيل الفيديو الرئيسي
    "upload",          # رفع الفيديو + الثامبنيل
    "short",           # إنشاء الفيديو القصير
    "short_thumbnail", # إنشاء ثامبنيل الفيديو القصير ← جديد!
    "short_upload",    # رفع الفيديو القصير + الثامبنيل
]


class TeeWriter(io.TextIOBase):
    """Write to multiple streams simultaneously (console + log file)."""
    def __init__(self, *streams):
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


def _slugify_english(s: str) -> str:
    s_ascii = s.encode("ascii", "ignore").decode("ascii")
    s_ascii = re.sub(r"[^A-Za-z0-9\-\_ ]+", "", s_ascii)
    s_ascii = re.sub(r"\s+", "-", s_ascii).strip("-_")
    s_ascii = re.sub(r"-+", "-", s_ascii)
    return s_ascii[:60]


def _read_titles(run_dir: Path) -> dict:
    try:
        return json.loads((run_dir / "output.titles.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _update_summary(run_dir: Path, stage_name: str, status: str = "ok", artifact: str = "") -> None:
    """Update summary.json with stage completion status."""
    summary_path = run_dir / "summary.json"
    try:
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        else:
            summary = {"run_id": run_dir.name.split("_")[0], "stages": []}

        # Check if stage already recorded
        existing = [s for s in summary.get("stages", []) if s.get("name") == stage_name]
        if existing:
            # Update existing entry
            for s in summary["stages"]:
                if s.get("name") == stage_name:
                    s["status"] = status
                    if artifact:
                        s["artifact"] = artifact
                    break
        else:
            # Add new entry
            summary["stages"].append({
                "name": stage_name,
                "status": status,
                "artifact": artifact,
            })

        # Save
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[warning] could not update summary.json: {e}")


def _sanitize_filename(name: str, max_len: int = 120) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    name = re.sub(r"[\x00-\x1F]", "", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s*-\s*", "-", name)
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "output"


def _validate_stage_requirements(run_dir: Path, stage_name: str) -> tuple[bool, list[str]]:
    """
    Validate that all required outputs for a given stage exist.
    Returns (is_valid, missing_files)
    """
    missing = []
    titles = _read_titles(run_dir)

    if stage_name == "search":
        if not (run_dir / "input_name.txt").exists():
            missing.append("input_name.txt")
        if not (run_dir / "search.results.json").exists():
            missing.append("search.results.json")

    elif stage_name == "transcribe":
        if not (run_dir / "transcribe.txt").exists():
            missing.append("transcribe.txt")

    elif stage_name == "process":
        if not (run_dir / "output.titles.json").exists():
            missing.append("output.titles.json")
        # Either script.txt OR translate.txt must exist
        if not (run_dir / "script.txt").exists() and not (run_dir / "translate.txt").exists():
            missing.append("script.txt or translate.txt")
        if not titles:
            missing.append("valid output.titles.json content")

    elif stage_name == "youtube_metadata":
        if not titles:
            missing.append("output.titles.json")
        else:
            if "youtube_title" not in titles:
                missing.append("youtube_title in titles.json")
            if "youtube_description" not in titles:
                missing.append("youtube_description in titles.json")
            if "TAGS" not in titles:
                missing.append("TAGS in titles.json")

    elif stage_name == "tts":
        if not (run_dir / "narration.mp3").exists():
            missing.append("narration.mp3")
        if not (run_dir / "timestamps.json").exists():
            missing.append("timestamps.json")

    elif stage_name == "render":
        # render creates video_snap.mp4 (but it gets deleted after merge)
        # If merge is done, we assume render was done too
        yt = titles.get("youtube_title") if titles else None
        merge_done = False
        if yt:
            target = run_dir / f"{_sanitize_filename(yt)}.mp4"
            if target.exists():
                merge_done = True

        if not (run_dir / "video_snap.mp4").exists() and not merge_done:
            missing.append("video_snap.mp4 (or merged video)")

    elif stage_name == "merge":
        yt = titles.get("youtube_title") if titles else None
        if not yt:
            missing.append("youtube_title in titles.json")
        else:
            target = run_dir / f"{_sanitize_filename(yt)}.mp4"
            if not target.exists():
                missing.append(f"{_sanitize_filename(yt)}.mp4")

    elif stage_name == "thumbnail":
        if not (run_dir / "thumbnail.jpg").exists() and not (run_dir / "thumbnail.png").exists():
            missing.append("thumbnail.jpg or thumbnail.png")

    elif stage_name == "upload":
        # Upload is verified via summary.json only (no file artifact)
        try:
            sj = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            found = False
            for st in sj.get("stages", []):
                if st.get("name") == "upload" and st.get("status") == "ok":
                    found = True
                    break
            if not found:
                missing.append("upload stage in summary.json")
        except Exception:
            missing.append("summary.json")

    elif stage_name == "short":
        if not (run_dir / "short_final.mp4").exists():
            missing.append("short_final.mp4")
        if not (run_dir / "short_titles.json").exists():
            missing.append("short_titles.json")

    elif stage_name == "short_thumbnail":
        if not (run_dir / "short_thumbnail.jpg").exists() and not (run_dir / "short_thumbnail.png").exists():
            missing.append("short_thumbnail.jpg or short_thumbnail.png")

    elif stage_name == "short_upload":
        # Short upload is verified via summary.json only
        try:
            sj = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            found = False
            for st in sj.get("stages", []):
                if st.get("name") == "short_upload" and st.get("status") == "ok":
                    found = True
                    break
            if not found:
                missing.append("short_upload stage in summary.json")
        except Exception:
            missing.append("summary.json")

    return (len(missing) == 0, missing)


def _detect_completed_stages(run_dir: Path) -> List[str]:
    done: List[str] = []
    # search
    if (run_dir / "input_name.txt").exists():
        done.append("search")
    # transcribe
    if (run_dir / "transcribe.txt").exists():
        done.append("transcribe")
    # process
    titles = _read_titles(run_dir)
    if titles and (run_dir / "output.titles.json").exists() and ((run_dir / "script.txt").exists() or (run_dir / "translate.txt").exists()):
        done.append("process")
    # youtube_metadata
    if titles and ("youtube_title" in titles or "youtube_description" in titles or "TAGS" in titles):
        done.append("youtube_metadata")
    # tts
    if (run_dir / "narration.mp3").exists():
        done.append("tts")

    # Check merge first (to determine if render is also done)
    yt = titles.get("youtube_title") if titles else None
    merge_completed = False
    if yt:
        target = run_dir / f"{_sanitize_filename(yt)}.mp4"
        if target.exists():
            merge_completed = True

    # render - if merge is done, render must be done too (video_snap.mp4 gets deleted after merge)
    if (run_dir / "video_snap.mp4").exists() or merge_completed:
        done.append("render")

    # merge - add after render
    if merge_completed:
        done.append("merge")
    # upload — detect via summary.json
    try:
        sj = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        for st in sj.get("stages", []):
            if st.get("name") == "upload" and st.get("status") == "ok":
                done.append("upload")
                break
    except Exception:
        pass
    # thumbnail
    if (run_dir / "thumbnail.jpg").exists() or (run_dir / "thumbnail.png").exists():
        done.append("thumbnail")
    # short
    if (run_dir / "short_final.mp4").exists():
        done.append("short")
    # short_thumbnail
    if (run_dir / "short_thumbnail.jpg").exists() or (run_dir / "short_thumbnail.png").exists():
        done.append("short_thumbnail")
    # short_upload — detect via summary.json
    try:
        sj = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        for st in sj.get("stages", []):
            if st.get("name") == "short_upload" and st.get("status") == "ok":
                done.append("short_upload")
                break
    except Exception:
        pass
    return done


def _next_stage_from_summary(run_dir: Path) -> Optional[str]:
    """
    Determine next stage by combining summary.json with artifact detection.
    Validates each completed stage's outputs before proceeding.
    If any stage is missing required outputs, resume from that stage.
    """
    completed_stages = set()

    # 1. Read from summary.json
    try:
        sj = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        ok = [s for s in sj.get("stages", []) if s.get("status") == "ok" and s.get("name") in STAGE_ORDER]
        for stage in ok:
            completed_stages.add(stage["name"])
    except Exception:
        pass

    # 2. Detect from artifacts (important for runs started with run_pipeline)
    detected = _detect_completed_stages(run_dir)
    for stage in detected:
        completed_stages.add(stage)

    # 3. VALIDATION LAYER: Verify each completed stage has required outputs
    # Go through STAGE_ORDER and validate each "completed" stage
    first_invalid_stage = None
    for stage_name in STAGE_ORDER:
        if stage_name in completed_stages:
            # Validate this stage's outputs
            is_valid, missing = _validate_stage_requirements(run_dir, stage_name)
            if not is_valid:
                print(f"\n⚠️  WARNING: Stage '{stage_name}' marked complete but missing outputs:")
                for item in missing:
                    print(f"   ❌ {item}")
                print(f"   ↻ Will resume from '{stage_name}' to regenerate missing outputs.\n")
                first_invalid_stage = stage_name
                break
        else:
            # This stage not completed yet
            if first_invalid_stage is None:
                first_invalid_stage = stage_name
            break

    # 4. Return the first stage that needs to run
    return first_invalid_stage


def main() -> int:
    p = argparse.ArgumentParser(description="Resume pipeline from last successful stage for a given run directory")
    p.add_argument("--run", dest="run_dir", required=True, help="Run directory to resume (e.g., runs/2025-..)")
    p.add_argument("--config", dest="config_dir", default="config", help="Config directory")
    p.add_argument("--secrets", dest="secrets_dir", default="secrets", help="Secrets directory")
    p.add_argument("--privacy", dest="privacy_status", default="public", choices=["private","unlisted","public"], help="Privacy for upload stage (default: public)")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    config_dir = Path(args.config_dir)
    secrets_dir = Path(args.secrets_dir)

    if not run_dir.exists():
        print("Run directory not found:", run_dir)
        return 2

    start = _next_stage_from_summary(run_dir)
    if not start:
        print("No remaining stages to run (pipeline appears complete).")
        return 0
    print("Resuming from stage:", start)

    # Execute remaining stages in order
    remaining = STAGE_ORDER[STAGE_ORDER.index(start):]

    # Setup pipeline.log for unified logging
    combined_log = run_dir / "pipeline.log"
    combined_log.parent.mkdir(parents=True, exist_ok=True)
    _stdout = sys.stdout

    # Pre-detect common artifacts
    titles_json = run_dir / "output.titles.json"
    narration_mp3 = run_dir / "narration.mp3"
    script_txt = run_dir / "script.txt"
    translate_txt = run_dir / "translate.txt"

    for stage in remaining:
        print(f"[resume] Running stage: {stage}")

        if stage == "youtube_metadata":
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] YOUTUBE_METADATA @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = youtube_metadata_main(titles_json=titles_json, config_dir=config_dir)
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ youtube_metadata failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ youtube_metadata completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "youtube_metadata", "ok", str(titles_json))
                finally:
                    sys.stdout = _stdout

        elif stage == "tts":
            text_path = script_txt if script_txt.exists() else translate_txt
            tmp_segments = Path("tmp") / "tts_segments" / run_dir.name
            tmp_segments.mkdir(parents=True, exist_ok=True)

            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] TTS @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = tts_main(text_path=text_path, segments_dir=tmp_segments, output_mp3=narration_mp3)
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ tts failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ tts completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "tts", "ok", str(narration_mp3))
                finally:
                    sys.stdout = _stdout

        elif stage == "render":
            # Merge settings similar to run_pipeline
            base_settings = {}
            try:
                base_settings = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
            except Exception:
                base_settings = {}
            try:
                tj = json.loads(titles_json.read_text(encoding="utf-8"))
                for key in ("main_title", "subtitle", "footer", "top_title"):
                    if key in tj and isinstance(tj[key], str) and tj[key].strip():
                        base_settings[key] = tj[key]
            except Exception:
                pass
            try:
                cover_jpg = run_dir / "bookcover.jpg"
                if cover_jpg.exists():
                    base_settings["cover_image"] = str(cover_jpg.resolve())
            except Exception:
                pass
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tf.close()
            merged_settings_path = Path(tf.name)
            merged_settings_path.write_text(json.dumps(base_settings, ensure_ascii=False, indent=2), encoding="utf-8")

            out_mp4 = run_dir / "video_snap.mp4"
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] RENDER @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = render_main(
                        titles_json=titles_json,
                        settings_json=merged_settings_path,
                        template_html=config_dir / "template.html",
                        narration_mp3=narration_mp3,
                        output_mp4=out_mp4,
                    )
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ render failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ render completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "render", "ok", str(out_mp4))
                finally:
                    sys.stdout = _stdout

        elif stage == "merge":
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] MERGE @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = merge_main(
                        titles_json=titles_json,
                        video_mp4=run_dir / "video_snap.mp4",
                        audio_mp3=narration_mp3,
                        output_dir=run_dir,
                    )
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ merge failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ merge completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "merge", "ok", str(res))
                finally:
                    sys.stdout = _stdout

        elif stage == "upload":
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] UPLOAD @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    # Check if thumbnail exists
                    thumb_exists = (run_dir / "thumbnail.jpg").exists() or (run_dir / "thumbnail.png").exists()

                    vid = upload_main(
                        run_dir=run_dir,
                        titles_json=titles_json,
                        secrets_dir=secrets_dir,
                        privacy_status=args.privacy_status,
                        upload_thumbnail=thumb_exists,  # Upload thumbnail if it exists
                    )
                    elapsed = time.time() - t0
                    if not vid:
                        print(f"❌ upload failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ upload completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "upload", "ok", vid)
                finally:
                    sys.stdout = _stdout

        elif stage == "thumbnail":
            thumb_out = run_dir / "thumbnail.jpg"
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] THUMBNAIL @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = thumbnail_main(
                        titles_json=titles_json,
                        run_dir=run_dir,
                        output_path=thumb_out,
                    )
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ thumbnail failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ thumbnail completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "thumbnail", "ok", str(thumb_out))
                finally:
                    sys.stdout = _stdout

        elif stage == "short":
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] SHORT @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = generate_short(run_dir=run_dir)
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ short generation failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ short generation completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "short", "ok", str(res))
                finally:
                    sys.stdout = _stdout

        elif stage == "short_thumbnail":
            short_thumb_out = run_dir / "short_thumbnail.jpg"
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] SHORT_THUMBNAIL @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()
                try:
                    res = short_thumbnail_main(run_dir=run_dir, debug=True)
                    elapsed = time.time() - t0
                    if not res:
                        print(f"❌ short_thumbnail failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3
                    print(f"✅ short_thumbnail completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "short_thumbnail", "ok", str(short_thumb_out))
                finally:
                    sys.stdout = _stdout

        elif stage == "short_upload":
            with combined_log.open("a", encoding="utf-8") as lf:
                sys.stdout = TeeWriter(_stdout, lf)
                print("\n\n==============================================")
                print(f"[Stage] SHORT_UPLOAD @ {datetime.now().isoformat(timespec='seconds')}")
                print("==============================================")
                t0 = time.time()

                try:
                    # Use the same logic as shorts_generator.py
                    short_titles_json = run_dir / "short_titles.json"

                    # If short_titles.json doesn't exist, create it using shorts_generator logic
                    if not short_titles_json.exists():
                        try:
                            # Load metadata
                            metadata = _read_titles(run_dir)
                            book_name = metadata.get("main_title", "Unknown")

                            # Get main video URL from database
                            from src.infrastructure.adapters.database import check_book_exists
                            db_entry = check_book_exists(book_name, metadata.get("author_name"))
                            main_video_url = db_entry.get("youtube_url") if db_entry else None

                            # Load script for description
                            script_path = run_dir / "short_script.txt"
                            script = ""
                            if script_path.exists():
                                script = script_path.read_text(encoding="utf-8")

                            # Build description (same as shorts_generator)
                            description = f"{script}\n\n"
                            if main_video_url:
                                description += f"📖 Watch Full Summary:\n{main_video_url}\n\n"
                            else:
                                description += f"📖 Watch Full Summary on our channel\n\n"

                            description += f"#books #booksummary #{book_name.replace(' ', '')}"

                            # Extract hook from script (first sentence)
                            hook = script.split('.')[0] if script and '.' in script else script[:50] if script else book_name
                            upload_title = f"{hook[:50]}... - {book_name}"

                            # Create short_titles.json
                            short_metadata = {
                                "youtube_title": upload_title,
                                "youtube_description": description,
                                "TAGS": metadata.get("TAGS", []) + ["shorts"],
                                "main_title": book_name,
                                "author_name": metadata.get("author_name")
                            }

                            with short_titles_json.open("w", encoding="utf-8") as f:
                                json.dump(short_metadata, f, ensure_ascii=False, indent=2)

                            print(f"[short_upload] Title: {upload_title}")
                            print(f"[short_upload] Description preview: {description[:100]}...")

                        except Exception as e:
                            print(f"❌ short_upload failed (metadata preparation): {e}")
                            import traceback
                            traceback.print_exc()
                            sys.stdout = _stdout
                            return 3
                    else:
                        print("[short_upload] Using existing short_titles.json")

                    # Upload short
                    short_video_id = upload_main(
                        run_dir=run_dir,
                        titles_json=short_titles_json,
                        secrets_dir=secrets_dir,
                        privacy_status=args.privacy_status,
                        upload_thumbnail=True,  # ← Upload short thumbnail!
                        allow_fallbacks=True,  # Allow finding short_final.mp4
                    )

                    elapsed = time.time() - t0
                    if not short_video_id:
                        print(f"❌ short_upload failed after {elapsed:.1f}s")
                        sys.stdout = _stdout
                        return 3

                    # Save short video ID to metadata
                    try:
                        metadata = _read_titles(run_dir)
                        metadata["short_video_id"] = short_video_id
                        metadata["short_video_url"] = f"https://youtube.com/watch?v={short_video_id}"
                        with titles_json.open("w", encoding="utf-8") as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                        print(f"✅ Short uploaded: https://youtube.com/watch?v={short_video_id}")
                    except Exception as e:
                        print(f"[warning] could not save short_video_id: {e}")

                    print(f"✅ short_upload completed in {elapsed:.1f}s")
                    _update_summary(run_dir, "short_upload", "ok", f"https://youtube.com/watch?v={short_video_id}")

                finally:
                    sys.stdout = _stdout

        else:
            # Earlier stages (search/transcribe/process) are not handled by resume
            print(f"Skipping unsupported stage in resume context: {stage}")

    # Final: Update database status to "done" after successful resume
    try:
        from src.infrastructure.adapters.database import update_book_status

        meta = _read_titles(run_dir)
        book_name = meta.get("main_title")
        author_name = meta.get("author_name")

        # Check if video was uploaded
        video_id = meta.get("youtube_video_id") or meta.get("video_id")
        main_video_url = f"https://youtube.com/watch?v={video_id}" if video_id else None

        # Check for short
        short_id = meta.get("short_video_id")
        short_url = f"https://youtube.com/watch?v={short_id}" if short_id else None

        if book_name:
            # CRITICAL: Only update to "done" if we have BOTH main video AND short
            if main_video_url and short_url:
                with combined_log.open("a", encoding="utf-8") as lf:
                    sys.stdout = TeeWriter(_stdout, lf)
                    print("\n\n==============================================")
                    print(f"[Database] UPDATE STATUS @ {datetime.now().isoformat(timespec='seconds')}")
                    print("==============================================")
                    try:
                        update_book_status(
                            book_name=book_name,
                            author_name=author_name,
                            status="done",
                            youtube_url=main_video_url,
                            short_url=short_url
                        )
                        print(f"✅ Database updated: Book complete (Main + Short)")
                    finally:
                        sys.stdout = _stdout
            else:
                # Incomplete - keep status as "processing"
                missing = []
                if not main_video_url:
                    missing.append("main video")
                if not short_url:
                    missing.append("short")
                print(f"⚠️ Book incomplete - missing: {', '.join(missing)}")
                print(f"Status remains 'processing' - folder NOT deleted")
    except Exception as e:
        print(f"⚠️ Failed to update database status: {e}")

    with combined_log.open("a", encoding="utf-8") as lf:
        sys.stdout = TeeWriter(_stdout, lf)
        print("\n\n==============================================")
        print(f"[Resume] COMPLETED @ {datetime.now().isoformat(timespec='seconds')}")
        print("==============================================")
        print("✅ Resume completed successfully!")
        sys.stdout = _stdout

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
