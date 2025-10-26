"""Generate thumbnails with four-word hooks using the same adapter as the pipeline."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import shutil
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory

# Allow importing project modules when the script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrastructure.adapters.thumbnail import generate_thumbnail


PRESETS: dict[str, tuple[list[str], list[str]]] = {
    "compact": (
        ["Own", "The", "Future", "Now"],
        ["Bold", "Ideas", "Drive", "Growth"],
    ),
    "long": (
        ["Unstoppable", "Monopoly", "Mindset", "Blueprint"],
        ["Revolutionary", "Innovation", "Strategy", "Playbook"],
    ),
}


def _maybe_copy_cover(src_cover: Path | None, run_dir: Path, verbose: bool = True) -> None:
    """Copy a cover image into the run dir if provided and exists."""
    if not src_cover:
        return
    if not src_cover.exists():
        return
    target = run_dir / src_cover.name
    try:
        if target.resolve() == src_cover.resolve():
            if verbose:
                print(f"📚 Reusing existing cover in run dir: {src_cover.name}")
            return
    except OSError:
        pass
    shutil.copy(src_cover, target)
    if verbose:
        print(f"📚 Using book cover: {src_cover.name}")


def _write_temp_metadata(
    run_dir: Path,
    main_words: list[str],
    subtitle_words: list[str],
    base_metadata: dict[str, object] | None = None,
) -> Path:
    """Create a temporary metadata JSON file constrained to four-word hooks."""
    payload = dict(base_metadata or {})
    payload.setdefault("main_title", "Zero to One")
    payload.setdefault("author_name", "Peter Thiel")
    payload["thumbnail_title"] = " ".join(main_words)
    payload["thumbnail_subtitle"] = " ".join(subtitle_words)

    with NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8", dir=run_dir) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        return Path(handle.name)


def _resolve_words(
    preset: str | None,
    custom_title: str | None,
    custom_subtitle: str | None,
) -> tuple[list[str], list[str]]:
    if custom_title:
        main_words = custom_title.split()
    else:
        key = preset or "long"
        main_words = PRESETS.get(key, PRESETS["long"])[0]

    if custom_subtitle:
        subtitle_words = custom_subtitle.split()
    else:
        key = preset or "long"
        subtitle_words = PRESETS.get(key, PRESETS["long"])[1]

    return main_words, subtitle_words


def _load_base_metadata(titles_json: Path | None) -> dict[str, object] | None:
    if not titles_json:
        return None
    if not titles_json.exists():
        raise FileNotFoundError(f"titles_json not found: {titles_json}")
    with titles_json.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("titles_json root must be an object")
        return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a quick thumbnail with four-word hook/subtitle.")
    parser.add_argument("--run", type=Path, help="Existing run directory to reuse assets (uses output.titles.json).")
    parser.add_argument("--titles", type=Path, help="Explicit titles JSON file (defaults to run/output.titles.json).")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), help="Hook word preset (default: long).")
    parser.add_argument("--title", help="Override thumbnail title text (provide exactly four words).")
    parser.add_argument("--subtitle", help="Override thumbnail subtitle text (provide exactly four words).")
    parser.add_argument("--cover", type=Path, help="Explicit cover image to use if run dir missing cover.")
    parser.add_argument("--output", type=Path, default=Path("quick_thumbnail.jpg"), help="Output thumbnail path.")
    parser.add_argument("--debug", action="store_true", help="Enable thumbnail adapter debug logs.")
    parser.add_argument(
        "--keep-temp", action="store_true", help="Keep temporary run directory when not using --run.")
    args = parser.parse_args()

    main_words, subtitle_words = _resolve_words(args.preset, args.title, args.subtitle)

    if len(main_words) != 4:
        print(f"⚠️ Expected 4 words for main title, got {len(main_words)}.")
    if len(subtitle_words) != 4:
        print(f"⚠️ Expected 4 words for subtitle, got {len(subtitle_words)}.")

    print("🎨 Generating quick thumbnail with 4-word hook...")
    print(f"   Main: {' '.join(main_words)}")
    print(f"   Sub:  {' '.join(subtitle_words)}")

    if args.output.exists():
        args.output.unlink()

    if args.run:
        run_dir = args.run.resolve()
        if not run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
        titles_json = args.titles.resolve() if args.titles else run_dir / "output.titles.json"
        base_meta = _load_base_metadata(titles_json)
        temp_json = _write_temp_metadata(run_dir, main_words, subtitle_words, base_meta)
        if args.cover:
            _maybe_copy_cover(args.cover.resolve(), run_dir)
        result = generate_thumbnail(
            run_dir=run_dir,
            titles_json=temp_json,
            output_path=args.output,
            debug=args.debug,
        )
        temp_json.unlink(missing_ok=True)
    else:
        temp_manager = TemporaryDirectory(prefix="thumbnail_run_")
        run_dir = Path(temp_manager.name)
        base_meta = _load_base_metadata(args.titles) if args.titles else None
        temp_json = _write_temp_metadata(run_dir, main_words, subtitle_words, base_meta)
        cover_candidate: Path | None = None
        if args.cover:
            cover_candidate = args.cover.resolve()
        else:
            cwd_cover = Path("bookcover.jpg")
            if cwd_cover.exists():
                cover_candidate = cwd_cover
        _maybe_copy_cover(cover_candidate, run_dir)
        result = generate_thumbnail(
            run_dir=run_dir,
            titles_json=temp_json,
            output_path=args.output,
            debug=args.debug,
        )
        temp_json.unlink(missing_ok=True)
        if args.keep_temp:
            print(f"ℹ️ Temporary run dir kept at {run_dir}")
            temp_manager.cleanup = lambda: None  # type: ignore[assignment]
        else:
            temp_manager.cleanup()

    if result:
        print(f"\n✅ Thumbnail saved: {result}")
    else:
        print("\n❌ Failed to generate thumbnail")


if __name__ == "__main__":
    main()
