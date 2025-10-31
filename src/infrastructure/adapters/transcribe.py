from __future__ import annotations
from pathlib import Path
from typing import Optional, Union, Any, Tuple
import argparse
import os
import sys
import time
import re
import subprocess  # CRITICAL: needed for check=True error handling
import random


# Workspace dirs
REPO_ROOT = Path(__file__).resolve().parents[3]  # Fixed: was parents[2], should be parents[3] to reach repo root
TMP_SUBS_DIR = REPO_ROOT / "tmp" / "subs"


# User-Agent pool for rotation (mimics real browsers)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
]


def get_random_user_agent() -> str:
    """Get a random User-Agent from the pool"""
    return random.choice(USER_AGENTS)


def ensure_dir(p: Union[Path, str]) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


_CUE_TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> .*$")


def vtt_to_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    lines = []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            l = raw.rstrip("\n\r")
            if not l:
                continue
            if l.isdigit():
                continue
            if _CUE_TIMESTAMP_RE.match(l):
                continue
            cleaned = re.sub(r"<[^>]+>", "", l).strip()
            if cleaned:
                lines.append(cleaned)
    out_lines = []
    prev = None
    for ln in lines:
        key = ln.strip().lower()
        if key == prev:
            continue
        out_lines.append(ln)
        prev = key
    return "\n".join(out_lines)


def video_id_from_url(url_or_id: str) -> str:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    if len(url_or_id) == 11 and all(c.isalnum() or c in "_-" for c in url_or_id):
        return url_or_id
    raise ValueError(f"Unable to parse video id from: {url_or_id}")


def sanitize_filename(s: str, max_len: int = 30) -> str:
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]+", "-", s)
    s = re.sub(r"\s+", " ", s)
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s


def run_yt_dlp_download_subs(
    video_url: str,
    video_id: str,
    cookies: Optional[Path],
    forced_lang: Optional[str],
    prefer_title: bool = False,
    user_agent: Optional[str] = None,  # NEW: Accept User-Agent parameter
) -> Tuple[Optional[Path], Optional[str]]:
    try:
        from yt_dlp import YoutubeDL  # type: ignore
        use_lib = True
    except Exception:
        use_lib = False

    ensure_dir(TMP_SUBS_DIR)

    manual_avail = set()
    auto_avail = set()
    _info_title = ''
    _info_language = ''
    
    # Get random User-Agent if not provided (for fallback rotation)
    if user_agent is None:
        user_agent = get_random_user_agent()
    print(f"[INFO] Using User-Agent: {user_agent[:50]}...")  # Show first 50 chars
    
    try:
        from yt_dlp import YoutubeDL  # type: ignore
        ydl_opts: dict[str, Any] = {
            'http_headers': {
                'User-Agent': user_agent
            }
        }
        if cookies is not None and cookies.exists():
            ydl_opts['cookiefile'] = str(cookies)
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(video_url, download=False)
            subs = info.get('subtitles') or {}
            autos = info.get('automatic_captions') or {}

            def norm(code: str) -> str:
                return code.split('-')[0].lower()

            def has_vtt(entries) -> bool:
                for e in entries:
                    if isinstance(e, dict) and e.get('ext') == 'vtt':
                        return True
                return False

            manual_avail_vtt = set()
            manual_avail_any = set()
            auto_avail_vtt = set()
            auto_avail_any = set()

            for k, v in subs.items():
                lc = norm(k)
                if v:
                    manual_avail_any.add(lc)
                    if has_vtt(v):
                        manual_avail_vtt.add(lc)
            for k, v in autos.items():
                lc = norm(k)
                if v:
                    auto_avail_any.add(lc)
                    if has_vtt(v):
                        auto_avail_vtt.add(lc)

            manual_avail = manual_avail_any
            auto_avail = auto_avail_any
            _manual_vtt = manual_avail_vtt
            _auto_vtt = auto_avail_vtt
            _info_title = (info.get('fulltitle') or info.get('title') or '')
            _info_language = (info.get('language') or '')
    except Exception:
        try:
            cmd = ["yt-dlp", "--list-subs", "--user-agent", user_agent, video_url]
            if cookies is not None and cookies.exists():
                cmd[1:1] = ["--cookies", str(cookies)]
            # CRITICAL FIX: check=True to catch yt-dlp failures
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            out = (res.stdout or "") + "\n" + (res.stderr or "")
        except subprocess.CalledProcessError as e:
            print(f"❌ yt-dlp --list-subs failed with exit code {e.returncode}")
            out = ""
        except subprocess.TimeoutExpired:
            print("⏱️ yt-dlp --list-subs timed out after 60s")
            out = ""
        except Exception as e:
            print("yt-dlp --list-subs failed:", e)
            out = ""

        mode: Optional[str] = None
        for line in out.splitlines():
            s = line.strip()
            if not s:
                continue
            low = s.lower()
            if 'available automatic captions' in low or 'available automatic subtitles' in low:
                mode = 'auto'
                continue
            if 'available subtitles for' in low or 'available subtitles' in low:
                mode = 'manual'
                continue

            parts = s.split()
            if not parts:
                continue
            first = parts[0]
            m = re.match(r'^([A-Za-z0-9_-]{1,20})', first)
            if m:
                code = m.group(1).lower()
                if code in ('language', 'name', 'formats'):
                    continue
                if mode == 'manual':
                    manual_avail.add(code)
                elif mode == 'auto':
                    auto_avail.add(code)
                else:
                    manual_avail.add(code)

    avail = manual_avail | auto_avail

    def pick_from_set(s):
        return sorted(s)[0] if s else None

    chosen_lang = None
    preferred_source = 'none'

    if forced_lang:
        chosen_lang = forced_lang.lower()
        preferred_source = 'forced'

    if not chosen_lang and prefer_title:
        try:
            info_lang = (_info_language or '').split('-')[0].lower() if _info_language else None
            title_lang = None
            t = (_info_title or '').strip()
            if t:
                if any('\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F' for ch in t):
                    title_lang = 'ar'
                else:
                    title_lang = 'en'
            if info_lang:
                chosen_lang = info_lang
                preferred_source = 'title'
            elif title_lang:
                chosen_lang = title_lang
                preferred_source = 'title'
        except Exception:
            pass

    if not chosen_lang:
        if 'ar' in locals().get('_manual_vtt', set()):
            chosen_lang = 'ar'; preferred_source = 'manual'
        elif 'en' in locals().get('_manual_vtt', set()):
            chosen_lang = 'en'; preferred_source = 'manual'
        elif pick_from_set(locals().get('_manual_vtt', set())):
            chosen_lang = pick_from_set(locals().get('_manual_vtt', set())); preferred_source = 'manual'
        elif 'ar' in manual_avail:
            chosen_lang = 'ar'; preferred_source = 'manual'
        elif 'en' in manual_avail:
            chosen_lang = 'en'; preferred_source = 'manual'
        elif manual_avail:
            chosen_lang = pick_from_set(manual_avail); preferred_source = 'manual'
        elif 'ar' in locals().get('_auto_vtt', set()):
            chosen_lang = 'ar'; preferred_source = 'auto'
        elif 'en' in locals().get('_auto_vtt', set()):
            chosen_lang = 'en'; preferred_source = 'auto'
        elif pick_from_set(locals().get('_auto_vtt', set())):
            chosen_lang = pick_from_set(locals().get('_auto_vtt', set())); preferred_source = 'auto'
        elif 'ar' in auto_avail:
            chosen_lang = 'ar'; preferred_source = 'auto'
        elif 'en' in auto_avail:
            chosen_lang = 'en'; preferred_source = 'auto'
        elif auto_avail:
            chosen_lang = pick_from_set(auto_avail); preferred_source = 'auto'
        else:
            chosen_lang = None

    if not chosen_lang:
        print("No Arabic or English subtitle track was found for this video via yt-dlp.")
        return (None, _info_title if _info_title else None)

    print(f"[INFO] Will attempt to download subtitles in: {chosen_lang} (preferred source: {preferred_source})")

    out_template = str(Path(TMP_SUBS_DIR) / "%(id)s.%(lang)s.vtt")
    if cookies is not None and cookies.exists():
        cookies_arg = ["--cookies", str(cookies)]
    else:
        cookies_arg = []

    download_order = ['manual', 'auto'] if preferred_source in ('manual', 'none') else ['auto', 'manual']
    for mode in download_order:
        if use_lib:
            opts: dict[str, Any] = {
                'quiet': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': (mode == 'auto'),
                'subtitlesformat': 'vtt',
                'outtmpl': out_template,
                'subtitleslangs': [chosen_lang],
                'http_headers': {
                    'User-Agent': user_agent
                }
            }
            if cookies is not None and cookies.exists():
                opts['cookiefile'] = str(cookies)
            try:
                with YoutubeDL(opts) as ydl:  # type: ignore[name-defined]
                    ydl.download([video_url])
            except Exception as e:
                print("yt-dlp (lib) failed to download subtitles (mode=", mode, "):", e)
        else:
            cmd = [
                "yt-dlp", "--no-warnings", "--skip-download", "-o", out_template,
                "--sub-lang", chosen_lang, "--sub-format", "vtt",
                "--user-agent", user_agent,
            ]
            if mode == 'manual':
                cmd += ["--write-sub"]
            else:
                cmd += ["--write-auto-sub"]
            cmd += cookies_arg + [video_url]
            try:
                # CRITICAL FIX: check=True ensures yt-dlp failures raise exceptions
                # instead of silently continuing with corrupted/missing subtitles
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 min timeout for subtitle download
                )
                if result.stdout:
                    print(f"[yt-dlp] {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"❌ yt-dlp failed (mode={mode}): exit code {e.returncode}")
                if e.stderr:
                    print(f"   Error: {e.stderr.strip()}")
                raise  # Re-raise to abort pipeline
            except subprocess.TimeoutExpired:
                print(f"⏱️ yt-dlp timed out (mode={mode}) after 120s")
                raise
            except Exception as e:
                print("yt-dlp CLI invocation failed (mode=", mode, "):", e)
                raise  # Re-raise instead of silently continuing

        pattern = str(Path(TMP_SUBS_DIR) / f"*{video_id}*{chosen_lang}*.vtt")
        import glob as _glob
        candidates = sorted(set(_glob.glob(pattern)))
        if not candidates:
            pattern2 = str(Path(TMP_SUBS_DIR) / f"*{video_id}*.vtt")
            candidates = sorted(set(_glob.glob(pattern2)))
        if candidates:
            chosen = None
            for c in candidates:
                if f".{chosen_lang}.vtt" in c.lower():
                    chosen = c
                    break
            if not chosen:
                chosen = candidates[0]
            print(f"[INFO] Selected subtitle file: {os.path.basename(chosen)} (mode={mode})")
            return (Path(chosen), _info_title if _info_title else None)

    print(f"Failed to find a .vtt file for language {chosen_lang} after download attempts.")
    return (None, _info_title if _info_title else None)


def method_youtube_transcript_api(video_id: str, cookies: Optional[Path]) -> Optional[str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except Exception:
        print("youtube-transcript-api not installed; skipping this fallback. Install with: pip install youtube-transcript-api")
        return None

    print("Trying youtube-transcript-api list/fetch (new interface)...")
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        chosen = None
        for t in transcript_list:
            if t.language_code == 'ar':
                chosen = t
                break
        if not chosen:
            for t in transcript_list:
                if t.language_code == 'en':
                    chosen = t
                    break
        if not chosen:
            for t in transcript_list:
                chosen = t
                break
        if not chosen:
            print("No transcripts found via youtube-transcript-api.")
            return None
        data = chosen.fetch()
        lines = [x.text.strip() for x in data if getattr(x, "text", None)]
        if lines:
            return '\n'.join(lines)
    except Exception as e:
        print("youtube-transcript-api error:", e)
    return None


def run_dedupe_and_clean(
    output_basename: str,
    original_txt_path: Path,
    output_dir: Path,
    keep_temp: bool,
    final_ext: str = ".transcibe.txt",
    final_path: Optional[Path] = None,
) -> Optional[Path]:
    in_path = Path(original_txt_path)
    if not in_path.exists():
        print("Raw transcript missing:", in_path)
        return None

    try:
        out_lines: list[str] = []
        prev_norm: Optional[str] = None

        def normalize_line(s: str) -> str:
            return " ".join(s.split()).strip()

        with in_path.open("r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                ln = raw.rstrip("\n\r")
                norm = normalize_line(ln)
                if not norm:
                    if out_lines and out_lines[-1] == "":
                        continue
                    out_lines.append("")
                    prev_norm = None
                    continue
                if prev_norm is not None and norm.lower() == prev_norm:
                    continue
                out_lines.append(ln)
                prev_norm = norm.lower()

        dedup_path = in_path.with_name(in_path.stem + ".dedup" + in_path.suffix)
        with dedup_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(out_lines).rstrip() + "\n")
    except Exception as e:
        print("Dedupe step failed:", e)
        return None

    try:
        RE_VTT_HEADER = re.compile(r"^(WEBVTT|Kind:|Language:)\\b", re.IGNORECASE)
        RE_BRACKET = re.compile(r"\[[^\]]+\]")
        RE_BACKTICKS = re.compile(r"^`{3,}.*$")

        with dedup_path.open('r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        cleaned: list[str] = []
        for raw in lines:
            ln = raw.rstrip("\n\r")
            s = ln.strip()
            low = s.lower()
            if low.startswith("kind:") or low.startswith("language:"):
                continue
            if RE_VTT_HEADER.match(s):
                continue
            if RE_BACKTICKS.match(s):
                continue
            new = RE_BRACKET.sub("", ln)
            new = " ".join(new.split())
            cleaned.append(new)

        final_lines: list[str] = []
        prev_blank = False
        for l in cleaned:
            if l == "":
                if prev_blank:
                    continue
                final_lines.append("")
                prev_blank = True
            else:
                final_lines.append(l)
                prev_blank = False

        ensure_dir(output_dir)
        _final_path = Path(final_path) if final_path is not None else (Path(output_dir) / f"{output_basename}{final_ext}")
        with _final_path.open('w', encoding='utf-8') as f:
            f.write("\n".join(final_lines).rstrip() + "\n")
        print("Wrote cleaned file:", _final_path)
    except Exception as e:
        print("Clean step failed:", e)
        return None

    if not keep_temp:
        try:
            if dedup_path.exists():
                dedup_path.unlink()
            # Avoid deleting the final file if paths coincide
            if in_path.exists():
                try:
                    if final_path is None or Path(in_path) != Path(final_path):
                        in_path.unlink()
                except Exception:
                    in_path.unlink()
        except Exception as e:
            print("Warning: failed to remove intermediate output files:", e)

    return _final_path


def main(
    search_result: Union[dict, str],
    output_dir: Path,
    force_lang: Optional[str] = None,
    prefer_title: bool = True,
    keep_temp: bool = False,
    basename: Optional[str] = None,
) -> Optional[Path]:
    """Transcribe a YouTube video and return path to cleaned transcript."""
    url = None
    if isinstance(search_result, dict):
        url = search_result.get("url") or search_result.get("video")
    elif isinstance(search_result, str):
        url = search_result
    if not url:
        return None

    try:
        vid = video_id_from_url(url)
    except Exception:
        return None

    # ===== COOKIES FALLBACK SYSTEM (Multi-file support) =====
    cookies = None
    cookie_paths = [
        REPO_ROOT / "secrets" / "cookies.txt",      # Priority 1: Main cookies
        REPO_ROOT / "secrets" / "cookies_1.txt",    # Priority 2: Fallback 1
        REPO_ROOT / "secrets" / "cookies_2.txt",    # Priority 3: Fallback 2
        REPO_ROOT / "secrets" / "cookies_3.txt",    # Priority 4: Fallback 3
        REPO_ROOT / "cookies.txt"                   # Priority 5: Root fallback
    ]
    
    cookies_found = []  # Track all valid cookies files
    
    # Scan all cookie files
    for idx, c in enumerate(cookie_paths, 1):
        if c.exists():
            # Verify cookies file is not empty and has valid format
            try:
                content = c.read_text(encoding='utf-8').strip()
                if content and len(content) > 50:  # Basic validation
                    cookies_found.append(c)
                    print(f"[Cookies] ✓ Valid cookies file {idx}/{len(cookie_paths)}: {c.name}")
                else:
                    print(f"[Cookies] ⚠️  File {idx} exists but appears empty or invalid: {c.name}")
            except Exception as e:
                print(f"[Cookies] ⚠️  Failed to read file {idx}: {c.name} ({e})")
    
    # Use first valid cookies file (priority order)
    if cookies_found:
        cookies = cookies_found[0]
        print(f"[Cookies] 🍪 Using primary cookies: {cookies}")
        if len(cookies_found) > 1:
            print(f"[Cookies] 📋 {len(cookies_found)-1} backup cookies available for fallback")
    else:
        print("[Cookies] ❌ No valid cookies.txt found")
        print("[Cookies] 📂 Locations checked:")
        for cp in cookie_paths:
            print(f"  - {cp}")
        print("[Cookies] 💡 Tip: Export cookies.txt from browser using 'Get cookies.txt' extension")
        print("[Cookies] 🔐 Make sure to login to YouTube first, then export cookies")

    attempts = 2
    methods = ['yt-dlp', 'transcript-api']
    result: Optional[str] = None
    used_title: Optional[str] = None
    
    # ===== AUTO-RETRY SYSTEM: Try each cookies file until success =====
    current_cookie_index = 0
    max_cookie_retries = len(cookies_found) if cookies_found else 0

    for method in methods:
        if method == 'yt-dlp':
            for attempt in range(1, attempts + 1):
                print(f"Method yt-dlp attempt {attempt}/{attempts}")
                vtt, info_title = run_yt_dlp_download_subs(url, vid, cookies, force_lang, prefer_title=prefer_title)
                
                # ===== AUTO-RETRY WITH FALLBACK COOKIES ON FAILURE =====
                # If download failed and we have backup cookies, try them
                if not vtt and current_cookie_index < max_cookie_retries - 1:
                    print(f"    🔄 Primary cookies failed - trying backup cookies...")
                    
                    # Try each remaining backup cookies file
                    for retry_idx in range(current_cookie_index + 1, max_cookie_retries):
                        backup_cookies = cookies_found[retry_idx]
                        cookies = backup_cookies
                        current_cookie_index = retry_idx
                        
                        # Generate NEW User-Agent for this retry (rotation)
                        new_user_agent = get_random_user_agent()
                        print(f"    🔄 Rotating User-Agent: {new_user_agent[:50]}...")
                        print(f"    🍪 Attempting with backup cookies {retry_idx + 1}/{max_cookie_retries}: {backup_cookies.name}...")
                        
                        # Retry the same request with new cookies AND new User-Agent
                        vtt, info_title = run_yt_dlp_download_subs(
                            url, vid, cookies, force_lang, 
                            prefer_title=prefer_title,
                            user_agent=new_user_agent  # Pass new User-Agent
                        )
                        
                        if vtt:
                            print(f"    ✅ Success with backup cookies {retry_idx + 1}!")
                            break  # Success - continue with this cookies file
                    else:
                        # All cookies failed
                        if max_cookie_retries > 0:
                            print(f"    ❌ All {max_cookie_retries} cookies files exhausted")
                
                if vtt:
                    try:
                        text = vtt_to_text(str(vtt))
                    except Exception:
                        text = None
                    if text and text.strip():
                        result = text
                        used_title = info_title
                        break
                # Exponential backoff: 5s, 10s, 15s, 20s...
                time.sleep(5 * attempt)
            if result:
                print("Success with yt-dlp")
                break
        else:
            for attempt in range(1, attempts + 1):
                print(f"Method {method} attempt {attempt}/{attempts}")
                text = method_youtube_transcript_api(vid, cookies)
                if text and text.strip():
                    result = text
                    break
                # Exponential backoff: 5s, 10s, 15s...
                time.sleep(5 * attempt)
            if result:
                print(f"Success with {method}")
                break

    if not result:
        print("لم يتم العثور على أي ترجمات أو تفريغ صوتي لهذا الفيديو.")
        return None

    ensure_dir(output_dir)
    base = sanitize_filename(basename) if basename else (sanitize_filename(used_title) if used_title else vid)
    raw_out = Path(output_dir) / f"{base}.txt"
    raw_out.write_text(result, encoding='utf-8')
    print(f"Raw transcript saved to: {raw_out}")

    # Standardize final transcript filename within the run root
    standardized_final = Path(output_dir) / "transcribe.txt"
    final = run_dedupe_and_clean(base, raw_out, output_dir, keep_temp=keep_temp, final_ext=".txt", final_path=standardized_final)

    # cleanup subtitle files for this video id
    try:
        if not keep_temp and TMP_SUBS_DIR.exists():
            for f in TMP_SUBS_DIR.glob(f"{vid}*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                if not any(TMP_SUBS_DIR.iterdir()):
                    TMP_SUBS_DIR.rmdir()
            except Exception:
                pass
    except Exception as e:
        print("Warning during tmp/subs cleanup:", e)

    return final


def cli_main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('video', nargs='?', help='YouTube url or id')
    p.add_argument('--keep-temp', action='store_true')
    p.add_argument('--force-lang')
    p.add_argument('--prefer-title', action='store_true')
    p.add_argument('--basename')
    args = p.parse_args()

    if not args.video:
        try:
            args.video = input('Enter YouTube video URL: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nNo video URL provided; exiting.')
            return 2

    out_dir = REPO_ROOT / "outputs"
    res = main(
        search_result=args.video,
        output_dir=out_dir,
        force_lang=args.force_lang,
        prefer_title=args.prefer_title,
        keep_temp=args.keep_temp,
        basename=args.basename,
    )
    if not res:
        return 3
    print(f"Final cleaned transcript at: {res}")
    return 0


if __name__ == '__main__':
    raise SystemExit(cli_main())
