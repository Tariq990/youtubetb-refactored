from __future__ import annotations
from pathlib import Path
from typing import Optional
import csv, time, subprocess
from playwright.sync_api import sync_playwright
import json, os, re
import shutil
from mutagen.mp3 import MP3

# Try to import whisper for forced alignment (optional dependency)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


DEFAULT_VOICE = "Shimmer"
DEFAULT_MAX_CHARS = 950
DEFAULT_VOICE_INSTRUCTIONS = (
    "Voice Affect: Deep, calm, and mysterious; like a storyteller guiding the listener into a dream.  \n"
    "Tone: Warm but shadowy, with an undercurrent of suspense.  \n"
    "Pacing: Slow and deliberate, with thoughtful pauses after key sentences.  \n"
    "Emotion: Gentle empathy mixed with intrigue; soothing yet captivating.  \n"
    "Pronunciation: Clear, steady, and slightly elongated on words such as \"dream,\" \"night,\" and \"silence.\"  \n"
    "Pauses: Insert short silences after dramatic lines, as if letting the words echo in the dark.  \n.\n"
)


def _load_prompts() -> dict:
    # look under config/prompts.json relative to repo
    try:
        here = Path(__file__).resolve()
        repo = here.parents[2]
        p = repo / "config" / "prompts.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            v = data.get("tts_voice_instructions")
            if isinstance(v, list):
                data["tts_voice_instructions"] = "\n".join(v)
            return data
    except Exception:
        pass
    return {}


def _clean_script_markers(text: str) -> str:
    """
    Remove prompt structure markers that may leak into generated scripts.

    REMOVES:
    - **[HOOK - 10-15 seconds]** or **[HOOK]**
    - **[CONTEXT - 20-30 seconds]** or **[CONTEXT]**
    - **[MAIN CONTENT]**
    - **[CLOSING - 10-15 seconds]** or **[CLOSING]**
    - [HOOK], [CONTEXT], etc. (without bold)

    PRESERVES:
    - **Bold text** (normal formatting like **Stack new habits**)
    - **Word:** (bold followed by colon, like **Law 1:** or **Important:**)
    - All other markdown/formatting

    Returns:
        Cleaned text ready for TTS
    """
    if not text:
        return text

    # Pattern: **[WORD/PHRASE - optional details]** or **[WORD/PHRASE]**
    # This matches: **[HOOK]**, **[HOOK - 10-15 seconds]**, [CONTEXT - ...], etc.
    # But NOT: **Stack new habits**, **Law 1:**, **Important:**

    # Remove bold markers with square brackets (prompt structure)
    text = re.sub(
        r'\*\*\s*\[([^\]]+)\]\s*\*\*',  # **[anything]**
        '',  # Remove completely
        text,
        flags=re.IGNORECASE
    )

    # Remove non-bold square bracket markers (fallback)
    text = re.sub(
        r'^\s*\[(?:HOOK|CONTEXT|MAIN CONTENT|CLOSING)(?:\s*-[^\]]+)?\]\s*$',  # [HOOK], [CONTEXT - ...], etc. on their own line
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    # Clean up extra blank lines created by removal (max 2 consecutive)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Clean up leading/trailing whitespace
    text = text.strip()

    return text


def _split_text(text: str, max_len: int) -> list[str]:
    if text is None:
        return []
    t = str(text)
    n = len(t)
    i = 0
    parts: list[str] = []
    sentence_seps = set([".", "!", "?", "…", "\n", "؟", "،", "؛", ":"])
    while i < n:
        end = min(i + max_len, n)
        if end == n:
            parts.append(t[i:n])
            break
        cut = -1
        j = end - 1
        while j >= i:
            if t[j] in sentence_seps:
                cut = j + 1
                break
            j -= 1
        if cut == -1:
            j = end - 1
            while j >= i:
                if t[j].isspace():
                    cut = j + 1
                    break
                j -= 1
        if cut == -1 or cut <= i:
            cut = end
        parts.append(t[i:cut])
        i = cut
    return parts


def _build_csv(single_path: Path, out_csv: Path, max_len: int) -> int:
    if not single_path.exists():
        raise FileNotFoundError(f"File not found: {single_path}")
    one_line = single_path.read_text(encoding="utf-8")
    if not one_line.strip():
        raise ValueError("single.txt is empty (only whitespace).")

    # Clean prompt markers before splitting
    one_line = _clean_script_markers(one_line)

    chunks = _split_text(one_line, max_len)
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['text'])
        for ch in chunks:
            w.writerow([ch])
    return len(chunks)


def _merge_mp3s_ffmpeg(in_dir: Path, out_path: Path, reencode: bool, delete_parts: bool) -> Optional[Path]:
    files = sorted(in_dir.glob("*.mp3"))
    if not files:
        print("⚠ No MP3 files to merge.")
        return None
    list_path = in_dir / "concat_list.txt"
    with list_path.open("w", encoding="utf-8", newline="\n") as f:
        for p in files:
            f.write(f"file '{p.resolve().as_posix()}'\n")
    # Delete old output if exists (for re-runs)
    if out_path.exists():
        try:
            print(f"🗑️ Deleting old merged audio: {out_path.name}")
            out_path.unlink()
        except Exception as e:
            print(f"⚠️ Could not delete old audio: {e}")
    base_args = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_path.resolve())
    ]
    if reencode:
        out_args = ["-c:a", "libmp3lame", "-b:a", "320k", "-ar", "48000", "-ac", "2", str(out_path.resolve())]
    else:
        out_args = ["-c", "copy", str(out_path.resolve())]
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("❌ ffmpeg not found in PATH.")
        try:
            list_path.unlink()
        except Exception:
            pass
        return None
    try:
        print("🔗 Merging parts with ffmpeg ...")
        subprocess.run(base_args + out_args, check=True)
        print(f"🎉 Created merged file: {out_path}")
        if delete_parts:
            for p in files:
                try:
                    p.unlink()
                except Exception:
                    pass
        return out_path
    except subprocess.CalledProcessError as e:
        print(f"❌ ffmpeg merge failed: {e}")
        return None
    finally:
        try:
            list_path.unlink()
        except Exception:
            pass


def _save_timestamps_with_whisper(text_path: Path, narration_mp3: Path, run_dir: Path) -> bool:
    """
    Generate precise timestamps using Whisper word-level alignment.
    Uses 'tiny' model for speed since we already know the content.

    Args:
        text_path: Path to script.txt (full text)
        narration_mp3: Path to merged narration.mp3
        run_dir: Directory to save timestamps.json

    Returns:
        True if successful, False otherwise
    """
    try:
        if not WHISPER_AVAILABLE:
            print("⚠️ whisper not available, falling back to segment-based timestamps")
            return False

        if not text_path.exists():
            print(f"⚠️ Text file not found: {text_path}")
            return False

        if not narration_mp3.exists():
            print(f"⚠️ Audio file not found: {narration_mp3}")
            return False

        print(f"🎯 Using Whisper word-level timestamps for precise alignment...")
        print(f"   Text: {text_path}")
        print(f"   Audio: {narration_mp3}")

        # Read the script to use as prompt (helps Whisper align faster)
        text_content = text_path.read_text(encoding="utf-8").strip()
        first_500_chars = text_content[:500]  # Use first part as context

        # Load Whisper model (tiny = fastest, we already know the content!)
        print("   Loading Whisper model (tiny - optimized for speed)...")
        model = whisper.load_model("tiny")

        # Transcribe with word-level timestamps + prompt for guidance
        print("   Processing word-level alignment (tiny model = 4x faster)...")
        result = model.transcribe(
            str(narration_mp3),
            language="en",
            word_timestamps=True,
            verbose=False,
            initial_prompt=first_500_chars,  # Guide with known text
            temperature=0.0,  # Deterministic
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        if not result or "segments" not in result:
            print("⚠️ Whisper transcription failed")
            return False

        # Group words into sentences based on punctuation
        timestamps = []
        current_sentence = []
        sentence_start = 0.0
        idx = 0

        for segment in result["segments"]:
            if "words" not in segment:
                continue

            for word_info in segment["words"]:
                word = word_info.get("word", "").strip()
                start = word_info.get("start", 0.0)
                end = word_info.get("end", 0.0)

                if not current_sentence:
                    sentence_start = start

                current_sentence.append(word)

                # End sentence on punctuation
                if word.endswith(('.', '!', '?', ';')):
                    sentence_text = " ".join(current_sentence)
                    timestamps.append({
                        "index": idx,
                        "text": sentence_text,
                        "start": sentence_start,
                        "duration": end - sentence_start
                    })
                    idx += 1
                    current_sentence = []

        # Add remaining words as final sentence
        if current_sentence:
            sentence_text = " ".join(current_sentence)
            last_word = result["segments"][-1]["words"][-1]
            timestamps.append({
                "index": idx,
                "text": sentence_text,
                "start": sentence_start,
                "duration": last_word.get("end", 0.0) - sentence_start
            })

        # Calculate total duration
        total_duration = result.get("segments", [{}])[-1].get("end", 0.0) if result.get("segments") else 0.0

        # Save to timestamps.json
        output_path = run_dir / "timestamps.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump({
                "method": "whisper_word_level",
                "total_duration": total_duration,
                "segment_count": len(timestamps),
                "segments": timestamps
            }, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved precise timestamps to {output_path}")
        print(f"   Total duration: {total_duration:.2f}s ({int(total_duration//60)}:{int(total_duration%60):02d})")
        print(f"   Segments: {len(timestamps)} sentences")
        print(f"   Accuracy: ~90-95% (tiny model word-level, 4x faster than base)")

        return True

    except Exception as e:
        print(f"⚠️ Whisper alignment failed: {e}")
        print(f"   Falling back to segment-based timestamps")
        import traceback
        traceback.print_exc()
        return False


def _save_timestamps(segments_dir: Path, run_dir: Path) -> bool:
    """
    Calculate timestamps from MP3 segments and save to timestamps.json in run directory.
    Returns True if successful.
    """
    try:
        timestamps = []
        cumulative_time = 0.0

        # Get all MP3 files sorted by name (000_*.mp3, 001_*.mp3, etc.)
        mp3_files = sorted(segments_dir.glob("*.mp3"))

        if not mp3_files:
            print("⚠️ No MP3 files found in segments directory")
            return False

        # Read text segments from CSV to get the actual text
        csv_path = segments_dir / "texts.csv"
        texts = []
        if csv_path.exists():
            with csv_path.open(newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                texts = [row.get("text", "") for row in reader]

        for idx, mp3_file in enumerate(mp3_files):
            # Get duration using multiple fallback methods
            duration = None

            # Method 1: Try mutagen (primary method)
            try:
                audio = MP3(mp3_file)
                duration = audio.info.length
            except Exception as e:
                print(f"⚠️ Mutagen failed for {mp3_file.name}: {e}")

            # Method 2: Fallback to ffprobe if mutagen fails
            if duration is None:
                try:
                    import subprocess
                    # CRITICAL FIX: check=True for ffprobe reliability
                    result = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_file)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=True
                    )
                    # Debug output (only if check=True didn't raise exception)
                    if not result.stdout.strip():
                        print(f"[DEBUG] ffprobe returned empty output for {mp3_file.name}")
                        print(f"  Stderr: '{result.stderr}'")

                    # With check=True, we only get here if ffprobe succeeded
                    if result.stdout.strip():
                        duration = float(result.stdout.strip())
                        print(f"✓ Used ffprobe for {mp3_file.name}: {duration:.2f}s")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ ffprobe failed for {mp3_file.name}: exit code {e.returncode}")
                except subprocess.TimeoutExpired:
                    print(f"⏱️ ffprobe timed out for {mp3_file.name}")
                except Exception as e:
                    print(f"⚠️ ffprobe exception for {mp3_file.name}: {e}")

            # Method 3: REMOVED - File size estimation was unreliable
            # If we get here, all reliable methods failed
            if duration is None:
                print(f"❌ CRITICAL: All methods failed for {mp3_file.name}")
                print(f"   Cannot determine duration. Skipping this segment.")
                print(f"   This will cause timestamp misalignment!")
                continue

            # Get corresponding text
            text = texts[idx] if idx < len(texts) else ""

            timestamps.append({
                "index": idx,
                "file": mp3_file.name,
                "text": text,
                "start": cumulative_time,
                "duration": duration
            })

            cumulative_time += duration

        # Save to run directory
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "timestamps.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump({
                "total_duration": cumulative_time,
                "segment_count": len(timestamps),
                "segments": timestamps
            }, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved timestamps to {output_path}")
        print(f"   Total duration: {cumulative_time:.2f}s ({int(cumulative_time//60)}:{int(cumulative_time%60):02d})")
        print(f"   Segments: {len(timestamps)}")
        return True

    except Exception as e:
        print(f"⚠️ Failed to save timestamps: {e}")
        return False


def main(
    text_path: Path,
    segments_dir: Path,
    output_mp3: Path,
    *,
    voice_name: str = DEFAULT_VOICE,
    headless: bool = True,
    max_chars: int = DEFAULT_MAX_CHARS,
    voice_instructions: str = DEFAULT_VOICE_INSTRUCTIONS,
    reencode: bool = True,
    delete_parts_after_merge: bool = True,
    run_dir: Optional[Path] = None,
) -> Optional[Path]:
    # override defaults from prompts.json if available
    try:
        prompts = _load_prompts()
        if not voice_name and prompts.get("tts_default_voice"):
            voice_name = str(prompts.get("tts_default_voice"))
        if prompts.get("tts_default_voice") and voice_name == DEFAULT_VOICE:
            voice_name = str(prompts.get("tts_default_voice"))
        if prompts.get("tts_voice_instructions") and voice_instructions == DEFAULT_VOICE_INSTRUCTIONS:
            voice_instructions = str(prompts.get("tts_voice_instructions"))
    except Exception:
        pass
    segments_dir = Path(segments_dir)
    segments_dir.mkdir(parents=True, exist_ok=True)
    csv_path = segments_dir / "texts.csv"
    count = _build_csv(Path(text_path), csv_path, max_chars)
    print(f"✅ Created {csv_path} with {count} chunk(s) (≤ {max_chars} chars).")

    OPENAI_FM = "https://www.openai.fm/"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--autoplay-policy=no-user-gesture-required",
                "--mute-audio",
            ],
        )
        context = browser.new_context(accept_downloads=True)
        try:
            context.grant_permissions(["clipboard-read", "clipboard-write"], origin=OPENAI_FM)
        except Exception:
            pass
        page = context.new_page()
        page.set_default_timeout(20000)
        print("Opening OpenAI.fm ...")
        page.goto(OPENAI_FM, wait_until="domcontentloaded")

        def ensure_two_textareas():
            tas = page.locator("textarea")
            for _ in range(30):
                try:
                    if tas.count() >= 2:
                        return tas
                except Exception:
                    pass
                time.sleep(0.5)
            raise Exception("Could not find the two textarea fields (left and right).")

        def clear_and_type(textarea, text):
            textarea.wait_for(timeout=10000)
            textarea.click()
            page.keyboard.press("Control+A"); page.keyboard.press("Backspace"); time.sleep(0.01)
            target = "" if text is None else str(text)
            try:
                textarea.fill(target)
                if textarea.input_value() == target:
                    return True
            except Exception:
                pass
            try:
                textarea.click(); page.keyboard.insert_text(target); time.sleep(0.01)
                if textarea.input_value() == target:
                    return True
            except Exception:
                pass
            try:
                page.evaluate("""
                    async (t) => { try { await navigator.clipboard.writeText(t); } catch(e){} }
                """, target)
                textarea.click(); page.keyboard.press("Control+V"); time.sleep(0.01)
                if textarea.input_value() == target:
                    return True
            except Exception:
                pass
            try:
                page.evaluate(
                    """
                    ({t, idx}) => {
                        const areas = document.querySelectorAll('textarea');
                        const el = areas && areas[idx] ? areas[idx] : null;
                        if (el){
                            el.value = t; const fire = (type) => el.dispatchEvent(new Event(type, { bubbles: true }));
                            fire('input'); fire('change');
                        }
                    }
                    """,
                    {"t": target, "idx": textarea.index},
                )
                time.sleep(0.01)
                return textarea.input_value() == target
            except Exception:
                return False

        def set_voice_instructions_left(instructions_text):
            tas = ensure_two_textareas(); left = tas.nth(0)
            return clear_and_type(left, instructions_text)

        def set_main_text_right(main_text):
            tas = ensure_two_textareas(); right = tas.nth(1)
            ok = clear_and_type(right, main_text)
            try:
                page.keyboard.press("Tab"); page.keyboard.press("Shift+Tab")
            except Exception:
                pass
            return ok

        def click_play():
            for name in ["Play", "Speak", "Generate", "▶", "Start"]:
                try:
                    page.get_by_role("button", name=name).first.click(timeout=3000)
                    return True
                except Exception:
                    pass
            try:
                page.keyboard.press("Enter"); return True
            except Exception:
                pass
            try:
                page.locator("button").nth(0).click(timeout=3000); return True
            except Exception:
                return False

        def wait_and_click_download(idx: int) -> bool:
            time.sleep(4.0)
            download_btn = None
            for _ in range(12):
                try:
                    download_btn = page.get_by_role("button", name="Download").first
                    download_btn.wait_for(timeout=1000)
                    break
                except Exception:
                    time.sleep(1)
            if not download_btn:
                print(f"[{idx}] ⏳ Download button did not appear.")
                return False
            try:
                with page.expect_download(timeout=30000) as dl_info:
                    download_btn.click()
                download = dl_info.value
                out_name = f"{idx:03d}_{voice_name}.mp3"
                out_path = segments_dir / out_name
                download.save_as(out_path)
                print(f"✅ Saved: {out_path}")
                return True
            except Exception as e:
                print(f"[{idx}] Download error: {e}")
                return False

        with csv_path.open(newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            i = 0
            while i < len(rows):
                row = rows[i]
                main_text = row.get("text")
                if not main_text:
                    i += 1
                    continue

                # CRITICAL FIX: Add max retries to prevent infinite loops
                MAX_RETRIES = 10
                attempt = 0
                success = False

                while attempt < MAX_RETRIES:
                    attempt += 1
                    print(f"\n[{i+1}] Attempt {attempt}/{MAX_RETRIES}: processing text ({len(main_text)} chars)")
                    try:
                        print("↻ Reloading page...")
                        page.reload(wait_until="domcontentloaded")
                        try:
                            page.get_by_text(voice_name, exact=True).first.click()
                        except Exception:
                            print(f"⚠ Voice '{voice_name}' not found, continuing with default.")
                        if not set_voice_instructions_left(voice_instructions):
                            print(f"[{i+1}] ❌ Failed to paste voice instructions. Retrying...")
                            raise Exception("Failed to set voice instructions.")
                        if not set_main_text_right(main_text):
                            print(f"[{i+1}] ❌ Failed to paste main text. Retrying...")
                            raise Exception("Failed to set main text.")
                        if not click_play():
                            print(f"[{i+1}] ❌ Play button not found. Retrying...")
                            raise Exception("Failed to click play button.")
                        if not wait_and_click_download(i+1):
                            print(f"[{i+1}] ❌ Download failed. Retrying...")
                            raise Exception("Download failed.")
                        success = True
                        print(f"[{i+1}] ✅ Conversion and download successful.")
                        break
                    except Exception as e:
                        if attempt >= MAX_RETRIES:
                            print(f"\n❌ CRITICAL: Failed after {MAX_RETRIES} attempts for segment {i+1}")
                            print(f"   Text: {main_text[:100]}...")
                            print(f"   Last error: {e}")
                            raise RuntimeError(f"TTS failed for segment {i+1} after {MAX_RETRIES} attempts") from e

                        # Exponential backoff: 5s, 10s, 20s, 40s, ...
                        wait_time = min(5 * (2 ** (attempt - 1)), 60)  # Max 60 seconds
                        print(f"[{i+1}] Error occurred: {e}")
                        print(f"⏳ Retrying in {wait_time} seconds... ({attempt}/{MAX_RETRIES})")
                        time.sleep(wait_time)

                if success:
                    i += 1
                else:
                    # This should never happen due to raise above, but just in case
                    raise RuntimeError(f"TTS failed for segment {i+1} - unexpected error")

        context.close(); browser.close()

    # merge
    output_mp3.parent.mkdir(parents=True, exist_ok=True)

    # Save timestamps BEFORE merging (so files still exist) - this is the legacy method
    if run_dir and segments_dir.exists():
        print("\n📍 Saving timestamps from TTS segments (legacy method)...")
        _save_timestamps(segments_dir, run_dir)

    merged = _merge_mp3s_ffmpeg(segments_dir, Path(output_mp3), reencode, delete_parts_after_merge)

    # After successful merge, try to generate precise timestamps with Whisper
    if merged and run_dir and text_path and Path(output_mp3).exists():
        print("\n🎯 Attempting precise timestamp generation with Whisper (tiny model)...")
        whisper_success = _save_timestamps_with_whisper(text_path, Path(output_mp3), run_dir)
        if whisper_success:
            print("✅ Using Whisper timestamps (90-95% accuracy, word-level, fast)")
        else:
            print("ℹ️ Using legacy segment-based timestamps (~70% accuracy)")

    try:
        if csv_path.exists():
            csv_path.unlink()
    except Exception:
        pass
    # Remove the entire segments directory after a successful merge to clean up temp files
    try:
        if merged and segments_dir.exists():
            shutil.rmtree(segments_dir, ignore_errors=True)
    except Exception:
        pass
    return merged
