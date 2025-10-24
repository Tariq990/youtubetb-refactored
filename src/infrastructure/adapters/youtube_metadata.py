from __future__ import annotations

from pathlib import Path
from typing import Optional
import json
import importlib
import os
import re
import urllib.parse


def _load_prompts(config_dir: Path) -> dict:
    p = Path(config_dir) / "prompts.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for k in ("youtube_title_template", "youtube_description_template"):
                v = data.get(k)
                if isinstance(v, list):
                    data[k] = "\n".join(v)
            return data
        except Exception:
            pass
    return {}


def _fmt(tpl: str, **values: str) -> str:
    # Handle both string and list templates
    if isinstance(tpl, list):
        tpl = "\n".join(tpl)
    out = tpl
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _configure_model(config_dir: Optional[Path] = None) -> Optional[object]:
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        repo_root = Path(__file__).resolve().parents[3]  # Fixed: parents[3] to reach repo root
        for f in (repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"):
            try:
                if f.exists():
                    API_KEY = f.read_text(encoding="utf-8").strip()
                    break
            except Exception:
                pass
    if not API_KEY:
        print("GEMINI_API_KEY not found. Set env or add secrets/api_key.txt")
        return None
    genai = importlib.import_module("google.generativeai")
    getattr(genai, "configure")(api_key=API_KEY)
    # Determine model name from env or settings.json
    model_name = os.environ.get("GEMINI_MODEL")
    if not model_name and config_dir:
        try:
            sj = json.loads((Path(config_dir) / "settings.json").read_text(encoding="utf-8"))
            model_name = sj.get("gemini_model") or sj.get("gemini_model_name")
        except Exception:
            model_name = None
    if not model_name:
        model_name = "gemini-2.5-flash"
    Model = getattr(genai, "GenerativeModel")
    default_name = "gemini-2.5-flash"
    try_name = model_name or default_name
    model = Model(try_name)
    # Quick sanity ping; if it fails and not default, fallback.
    try:
        _ = model.generate_content("ping")
    except Exception:
        if try_name != default_name:
            try:
                model = Model(default_name)
            except Exception:
                pass
    return model


def _gen(model, prompt: str, mime_type: str = "text/plain") -> str:
    try:
        resp = model.generate_content(prompt, generation_config={"response_mime_type": mime_type})
        return getattr(resp, "text", "") or ""
    except Exception as e:
        print(f"API call failed: {e}")
        return ""


def _generate_title(model, book_name: str, prompts: dict) -> Optional[str]:
    tpl = prompts.get("youtube_title_template") or (
        "You are an expert YouTube title generator.\n\n"
        "Your task: create ONE powerful, catchy, and mysterious video title in English for a YouTube book summary video.\n\n"
        "Rules:\n"
        "- Generate ONLY one title.\n"
        "- Maximum 12 words.\n"
        "- Must include the phrase: \"Book Summary: {book_name}\"\n"
        "- Style: intriguing, emotional, and engaging, like top viral self-help or mystery book channels.\n"
        "- Avoid generic phrases. Make it sound unique and click-worthy.\n"
    )
    prompt = _fmt(tpl, book_name=book_name)
    title_text = _gen(model, prompt, mime_type="text/plain")
    if not title_text:
        return None
    title_text = title_text.strip().strip('"')
    title_text = re.sub(r"\s+", " ", title_text)
    return title_text or None


def _generate_description(model, book_name: str, prompts: dict) -> Optional[str]:
    tpl = prompts.get("youtube_description_template") or (
        "Write a compelling YouTube video description for a book summary video.\n\n"
        "Constraints:\n"
        "- Language: English.\n"
        "- Max ~180 words total.\n"
        "- First 1–2 sentences: a strong hook tied to the book.\n"
        "- Then 3–5 concise bullet points with the most intriguing takeaways.\n"
        "- Avoid links, hashtags, or calls to subscribe.\n"
        "- Keep it clean, unique, and click-worthy.\n\n"
        "Book Name: {book_name}\n"
    )
    prompt = _fmt(tpl, book_name=book_name)
    desc_text = _gen(model, prompt, mime_type="text/plain")
    if not desc_text:
        return None

    # Post-process description to ensure proper formatting
    desc_text = _format_description(desc_text.strip())
    return desc_text


def _format_description(desc: str) -> str:
    """
    Format description to ensure proper spacing:
    - Add blank line after 'Explained.' if missing (even with emoji before it)
    - Clean up multiple consecutive blank lines
    """
    if not desc:
        return desc

    # Ensure blank line after "Explained." (with optional emoji/text before it)
    # Match any character (including emoji) before "Explained."
    desc = re.sub(r'(.*?Explained\.)\s*\n(?!\n)', r'\1\n\n', desc)

    # Clean up 3+ consecutive newlines to max 2
    desc = re.sub(r'\n{3,}', '\n\n', desc)

    return desc.strip()


def _generate_amazon_link(book_name: str, author: Optional[str], affiliate_tag: str) -> str:
    """
    Generate Amazon affiliate search link for the book.

    Args:
        book_name: The book title
        author: Author name (optional, included for better search results)
        affiliate_tag: Amazon affiliate tag (e.g., "yourname-20")

    Returns:
        Shortened Amazon search URL with affiliate tag
    """
    # Use only book name for shorter URL (still effective)
    # Author is optional - we prefer shorter URLs
    search_query = book_name

    # URL encode the search query
    encoded_query = urllib.parse.quote_plus(search_query)

    # Build Amazon search URL with affiliate tag
    # IMPORTANT: Must include 'www.' for Amazon Associates to recognize the tag
    # Format: https://www.amazon.com/s?k=SEARCH&tag=AFFILIATE_TAG
    amazon_url = f"https://www.amazon.com/s?k={encoded_query}&tag={affiliate_tag}"

    return amazon_url
def _add_amazon_link_to_description(
    description: str,
    book_name: str,
    author: Optional[str],
    config_dir: Optional[Path] = None
) -> str:
    """
    Add Amazon affiliate link to video description if enabled in settings.

    Args:
        description: Original video description
        book_name: Book title
        author: Author name (optional)
        config_dir: Path to config directory

    Returns:
        Description with Amazon link appended (if enabled)
    """
    # Load settings
    if config_dir is None:
        config_dir = Path(__file__).resolve().parents[3] / "config"  # Fixed: parents[3]

    settings_path = Path(config_dir) / "settings.json"
    if not settings_path.exists():
        return description

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return description

    # Check if affiliate is enabled
    if not settings.get("amazon_affiliate_enabled", False):
        return description

    affiliate_tag = settings.get("amazon_affiliate_tag", "").strip()
    if not affiliate_tag:
        return description

    # Generate Amazon link
    amazon_url = _generate_amazon_link(book_name, author, affiliate_tag)

    # Get custom link text (default: "📖 Get the Book")
    link_text = settings.get("amazon_link_text", "📖 Get the Book")

    # Add link at the end of description
    # Format: "\n\n📖 Get the Book:\n{url}\n"
    link_section = f"\n\n{link_text}:\n{amazon_url}\n"

    return description.strip() + link_section


def _format_youtube_time(seconds: float) -> str:
    """Convert seconds to YouTube timestamp format (M:SS or H:MM:SS)"""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def _group_segments_into_chapters(segments: list[dict], total_duration: float, target_chapters: int = 8) -> list[dict]:
    """
    Group TTS segments into YouTube chapters with natural distribution.

    Target: 8-10 chapters for videos 20-60 min
    Strategy: Merge consecutive segments into balanced groups

    Rules:
    - First chapter always starts at 0:00 (YouTube requirement)
    - Chapters distributed evenly based on content
    - Minimum 3 chapters, maximum 12 chapters

    Returns: [{"start": 0.0, "segments": [seg1, seg2, ...]}, ...]
    """
    if not segments:
        return []

    # Calculate ideal chapter length
    ideal_chapter_len = total_duration / target_chapters

    grouped = []

    # First chapter ALWAYS starts at 0:00 (YouTube requirement)
    current_group = {"start": 0.0, "segments": []}
    current_duration = 0.0

    for seg in segments:
        seg_duration = seg.get("duration", 0.0)
        seg_start = seg.get("start", 0.0)

        # Skip segments beyond total duration
        if seg_start >= total_duration:
            continue

        # Start new chapter if current one is long enough
        should_start_new_chapter = (
            current_group["segments"] and
            current_duration >= ideal_chapter_len
        )

        if should_start_new_chapter:
            grouped.append(current_group)
            current_group = {"start": seg_start, "segments": []}
            current_duration = 0.0

        current_group["segments"].append(seg)
        current_duration += seg_duration

    # Add last group
    if current_group["segments"]:
        grouped.append(current_group)

    # Ensure first chapter starts at 0:00
    if grouped and grouped[0]["start"] != 0.0:
        grouped[0]["start"] = 0.0

    return grouped


def _get_video_duration(video_path: Path) -> Optional[float]:
    """
    Get actual video duration using ffprobe.
    Returns duration in seconds or None if failed.
    """
    try:
        import subprocess
        # CRITICAL FIX: check=True to ensure ffprobe failures are caught
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        print(f"[metadata] Warning: Could not get video duration: {e}")
    return None


def _adjust_timestamps_to_video(timestamps: dict, actual_duration: float) -> dict:
    """
    Adjust timestamps to match actual video duration.
    If timestamps exceed video duration, scale them proportionally.
    """
    original_duration = timestamps.get("total_duration", 0.0)
    segments = timestamps.get("segments", [])

    if not segments or original_duration <= 0:
        return timestamps

    # If timestamps fit within video, no adjustment needed
    if original_duration <= actual_duration:
        return timestamps

    # Scale factor to fit timestamps within actual duration
    scale_factor = actual_duration / original_duration

    print(f"[metadata] ⚠️ Timestamps ({original_duration:.1f}s) exceed video ({actual_duration:.1f}s)")
    print(f"[metadata] Scaling timestamps by {scale_factor:.2f}x")

    # Adjust each segment
    adjusted_segments = []
    for seg in segments:
        adjusted_seg = seg.copy()
        adjusted_seg["start"] = seg["start"] * scale_factor
        adjusted_seg["duration"] = seg["duration"] * scale_factor
        adjusted_segments.append(adjusted_seg)

    return {
        "total_duration": actual_duration,
        "segment_count": len(adjusted_segments),
        "segments": adjusted_segments
    }


def _generate_chapter_titles_with_ai(model, timestamps: dict, prompts: dict) -> list[dict]:
    """
    Use AI to generate smart chapter titles from GROUPED timestamp segments.
    Returns: [{"time": "0:00", "title": "Introduction"}, ...]
    """
    segments = timestamps.get("segments", [])
    total_duration = timestamps.get("total_duration", 0.0)

    if not segments:
        return []

    # Group segments into 8-10 chapters
    grouped = _group_segments_into_chapters(segments, total_duration, target_chapters=8)

    # Build prompt with grouped segments
    segment_texts = []
    for i, group in enumerate(grouped):
        # Combine text from all segments in this group
        combined_text = " ".join(seg.get("text", "") for seg in group["segments"])
        text_preview = combined_text[:300]  # First 300 chars
        segment_texts.append(f"Chapter {i+1}: {text_preview}...")

    prompt = (
        "You are an expert YouTube content strategist who creates irresistible chapter titles.\n\n"
        "Task: Generate a compelling, clickable title (max 6 words) for each chapter below.\n\n"
        "TITLE GUIDELINES:\n"
        "✅ Use power words: Secret, Hidden, Ultimate, Proven, Instant, Hack, Master, Unlock\n"
        "✅ Create curiosity: Why X Matters, The Truth About Y, What Nobody Tells You\n"
        "✅ Action-oriented: Start with strong verbs (Discover, Master, Build, Break, Transform)\n"
        "✅ Add intrigue: Make viewers want to click and watch\n"
        "✅ Vary your style: Don't repeat the same structure\n"
        "✅ Numbers work: 3 Keys, 5 Steps, The One Thing\n"
        "❌ Avoid repetitive patterns (don't use 'Make...' or 'The...' in every title)\n"
        "❌ Skip generic words like 'Introduction', 'Overview', 'Conclusion'\n\n"
        "Examples of GREAT titles:\n"
        "- \"The Hidden Science of Habits\"\n"
        "- \"Why Small Wins Change Everything\"\n"
        "- \"Master the 2-Minute Rule\"\n"
        "- \"The Instant Gratification Trap\"\n\n"
        "Output: Valid JSON array ONLY: [\"Title 1\", \"Title 2\", ...]\n"
        "No explanations, just the array.\n\n"
        "Chapters:\n" + "\n".join(segment_texts)
    )

    # Retry logic: try 3 times before falling back to generic titles
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        result = _gen(model, prompt, mime_type="application/json")
        
        if not result:
            print(f"⚠️ AI failed to generate chapter titles (attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                import time
                # Progressive backoff: 5s, 10s, 300s (5 minutes for last retry)
                wait_time = 300 if attempt == 2 else (5 * attempt)
                print(f"⏱️ Waiting {wait_time}s ({wait_time//60}min {wait_time%60}s) before retry...")
                time.sleep(wait_time)
                continue
            else:
                print("⚠️ Using fallback generic titles after all retries")
                return [
                    {"time": _format_youtube_time(group["start"]), "title": f"Part {i+1}"}
                    for i, group in enumerate(grouped)
                ]

        try:
            titles = json.loads(result)
            if isinstance(titles, list) and len(titles) == len(grouped):
                print(f"✅ Chapter titles generated successfully (attempt {attempt}/{max_retries})")
                return [
                    {"time": _format_youtube_time(group["start"]), "title": titles[i]}
                    for i, group in enumerate(grouped)
                ]
            else:
                print(f"⚠️ Titles count mismatch: got {len(titles) if isinstance(titles, list) else 'invalid'}, expected {len(grouped)} (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    import time
                    # Progressive backoff: 5s, 10s, 300s (5 minutes for last retry)
                    wait_time = 300 if attempt == 2 else (5 * attempt)
                    print(f"⏱️ Waiting {wait_time}s ({wait_time//60}min {wait_time%60}s) before retry...")
                    time.sleep(wait_time)
                    continue
        except Exception as e:
            print(f"⚠️ Failed to parse AI chapter titles: {e} (attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                import time
                # Progressive backoff: 5s, 10s, 300s (5 minutes for last retry)
                wait_time = 300 if attempt == 2 else (5 * attempt)
                print(f"⏱️ Waiting {wait_time}s ({wait_time//60}min {wait_time%60}s) before retry...")
                time.sleep(wait_time)
                continue

    # Fallback if all retries fail
    print("⚠️ Using fallback generic titles after all parsing attempts")
    return [
        {"time": _format_youtube_time(group["start"]), "title": f"Part {i+1}"}
        for i, group in enumerate(grouped)
    ]


def _generate_description_with_timestamps(
    model,
    book_name: str,
    timestamps_path: Path,
    prompts: dict,
    run_dir: Optional[Path] = None,
    author: Optional[str] = None,
    config_dir: Optional[Path] = None
) -> Optional[str]:
    """
    Generate description with timestamps appended.
    Adjusts timestamps to match actual video duration if available.
    """
    # Generate base description
    base_desc = _generate_description(model, book_name, prompts)
    if not base_desc:
        return None

    # Load timestamps
    try:
        timestamps = json.loads(timestamps_path.read_text(encoding="utf-8"))
    except Exception:
        print("⚠️ Could not read timestamps.json")
        return base_desc

    # Try to get actual video duration
    if run_dir:
        # Look for final video file
        video_candidates = list(run_dir.glob("*.mp4"))
        # Exclude video_snap.mp4 (preview only)
        video_candidates = [v for v in video_candidates if v.name != "video_snap.mp4"]

        if video_candidates:
            # Use the most recent/largest video file
            video_file = max(video_candidates, key=lambda p: p.stat().st_size)
            actual_duration = _get_video_duration(video_file)

            if actual_duration:
                print(f"[metadata] Video duration: {actual_duration:.1f}s ({int(actual_duration//60)}:{int(actual_duration%60):02d})")
                # Adjust timestamps to match video duration
                timestamps = _adjust_timestamps_to_video(timestamps, actual_duration)

    # Generate chapter titles using AI
    print("📍 Generating chapter titles with AI...")
    chapters = _generate_chapter_titles_with_ai(model, timestamps, prompts)

    if not chapters:
        print("⚠️ Could not generate chapters")
        return base_desc

    # Add Amazon affiliate link BEFORE chapters (if enabled)
    if author is not None and config_dir is not None:
        base_desc = _add_amazon_link_to_description(base_desc, book_name, author, config_dir)

    # Format chapters section with proper spacing
    # Add blank line after "CHAPTERS:" for better readability
    chapters_text = "\n\n\n📌 CHAPTERS:\n\n"
    for item in chapters:
        chapters_text += f"{item['time']} {item['title']}\n"

    # Append to description
    final_desc = base_desc + chapters_text

    print(f"✅ Generated description with {len(chapters)} chapters")
    return final_desc


def _generate_tags(book_title: str, author_name: Optional[str]) -> list[str]:
    """Generate basic tags based on book title and author."""
    bt = (book_title or "").strip()
    an = (author_name or "").strip()
    # ALWAYS start with InkEcho as first tag (channel branding)
    tags: list[str] = [
        "InkEcho",
        f"{bt}",
        f"{bt} summary",
        f"{bt} audiobook",
        f"{bt} full audiobook",
    ]
    if an:
        tags.extend([
            f"{bt} BY {an}",
            f"{bt} BY {an} summary",
            f"{bt} BY {an} audiobook",
            f"{bt} BY {an} full audiobook",
            f"{an}",
        ])
    # Filter out any empty entries just in case
    return [t for t in tags if t and t.strip()]


def _generate_ai_tags(model, book_title: str, author_name: Optional[str], prompts: dict) -> list[str]:
    """
    Generate AI-powered topic tags using Gemini.
    Returns 40+ content-related tags without mentioning book/author names.
    Upload stage will trim to fit 500 char limit automatically.
    """
    tpl = prompts.get("tags_template") or (
        "Give me 40 relevant tags for this book that reflect its content and topic.\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT mention the book title: {book_name}\n"
        "- Do NOT mention the author name: {author_name}\n"
        "- Return ONLY topic-related keywords (e.g., 'personal development', 'success strategies')\n"
        "- Each tag should be 1-3 words maximum\n"
        "- Include general AND specific tags\n"
        "- Return as a simple comma-separated list\n\n"
        "Book: {book_name} by {author_name}"
    )

    # Handle list templates
    if isinstance(tpl, list):
        tpl = "\n".join(tpl)

    # Format prompt
    prompt = tpl.replace("{book_name}", book_title).replace("{author_name}", author_name or "Unknown")

    try:
        # Call Gemini
        resp = model.generate_content(prompt)
        raw = resp.text.strip() if hasattr(resp, 'text') else ""

        # Parse comma-separated tags
        if raw:
            tags = [tag.strip() for tag in raw.split(',')]

            # Clean and validate each tag
            cleaned_tags = []
            for t in tags:
                if not t or len(t) <= 2:
                    continue

                # Remove leading numbers and dots (e.g., "1. tag" → "tag")
                import re
                t = re.sub(r'^\d+[\.\)]\s*', '', t)

                # Skip if still has numbers at start or is too long
                if t and not t[0].isdigit() and len(t.split()) <= 3:
                    cleaned_tags.append(t)

            return cleaned_tags[:40]  # Max 40 AI tags (will be combined with basic tags and trimmed to 500 chars in upload stage)
    except Exception as e:
        print(f"[AI Tags] Error: {e}")

    return []


def _generate_thumbnail_elements(model, book_title: str, author_name: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    # Prompt as requested: return ONLY Hook and Subtitle texts (no labels), optimized for thumbnail
    author = author_name or "Unknown"
    prompt = (
        "You are a world-class marketing strategist and YouTube growth expert.\n\n"
        f"Your task: generate thumbnail elements for a video about the book titled: {book_title}, written by {author}.\n\n"
        "Deliver only:\n\n"
        "Main Hook (2–6 words) → extremely clickable, bold, curiosity-driven, professional, and viral-ready; must reflect the core idea of the book and create intrigue. Avoid violent, exaggerated, or misleading words.\n\n"
        "Subtitle (3–6 words) → complements the hook, adds immediate value or insight, short and instantly readable, without repeating the hook; should highlight a key lesson or promise.\n\n"
        "Rules:\n\n"
        "- Return only the text for Main Hook and Subtitle, nothing else.\n"
        "- Do not include any labels, explanations, interpretations, or extra text.\n"
        "- Both elements must be ready to use directly on a thumbnail.\n"
        "- Return only one strongest option, fully optimized for a viral, professional thumbnail.\n"
    )
    text = _gen(model, prompt, mime_type="text/plain")
    if not text:
        return None, None, None
    # Parse first non-empty lines: expect 2 lines (hook, subtitle); third line optional (visual)
    lines = [ln.strip() for ln in str(text).splitlines() if ln and ln.strip()]
    while len(lines) < 2:
        lines.append("")
    hook = lines[0]
    sub = lines[1]
    img = lines[2] if len(lines) >= 3 else ""

    def _strip_md(s: str) -> str:
        # remove surrounding quotes/backticks/asterisks and extra spaces
        s = s.strip().strip('"').strip("'").strip("`")
        s = re.sub(r"^\*+|\*+$", "", s).strip()
        return s

    def _trim_words(s: str, min_w: int, max_w: int) -> str:
        ws = [w for w in re.split(r"\s+", s) if w]
        if len(ws) > max_w:
            ws = ws[:max_w]
        return " ".join(ws) if ws else ""

    def _clean_sentence(s: str) -> str:
        s = _strip_md(s)
        # Remove leading labels like "Main Hook:", "Subtitle:", "Hook:", etc.
        s = re.sub(r"^(?:main\s*hook|hook|subtitle|sub\s*hook|sub\s*title)\s*[:：\-]*\s*(?:\*\*?)?\s*", "", s, flags=re.IGNORECASE).strip()
        # collapse spaces and remove trailing punctuation like . ! ?
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"[\.!?]+$", "", s).strip()
        return s

    def _clean_visual(s: str) -> str:
        s = _strip_md(s)
        # Keep only alphabetic characters for the visual word; no punctuation/symbols
        s = re.sub(r"[^A-Za-z]", "", s)
        return s.strip()

    hook = _clean_sentence(hook)
    sub = _clean_sentence(sub)
    img = _clean_visual(img)

    # enforce word limits (soft): hook 2–6 words, sub 3–6 words
    if hook:
        hook = _trim_words(hook, 2, 6)
    if sub:
        sub = _trim_words(sub, 3, 6)
    if img:
        # one word only already; normalize case (Title Case), drop if too long/low-quality
        img = img.capitalize()
        if len(img) > 12:
            img = ""

    return (hook or None), (sub or None), (img or None)


def main(titles_json: Path, config_dir: Path) -> Optional[str]:
    # Load current titles JSON - READ FIRST to preserve existing data
    try:
        titles = json.loads(Path(titles_json).read_text(encoding="utf-8"))
    except Exception as e:
        print("Failed to read titles JSON:", e)
        return None

    # Preserve original data (CRITICAL: avoid race condition with process.py)
    original_titles = titles.copy()

    book_name = titles.get("main_title") or titles.get("title") or titles.get("book_name")
    if not book_name:
        print("main_title not found in titles JSON")
        return None

    prompts = _load_prompts(config_dir)
    model = _configure_model(config_dir)
    if not model:
        return None

    # Generate title
    yt_title = _generate_title(model, book_name, prompts)

    # Generate description with timestamps if available
    run_dir = Path(titles_json).parent
    timestamps_path = run_dir / "timestamps.json"

    # Always get author for Amazon link (need it before generating description)
    author = titles.get("author_name") or titles.get("author")

    yt_desc = None
    if timestamps_path.exists():
        print("📍 Generating description with timestamps...")
        yt_desc = _generate_description_with_timestamps(
            model, book_name, timestamps_path, prompts,
            run_dir=run_dir, author=author, config_dir=config_dir
        )

    # Fallback to basic description if timestamps unavailable
    if not yt_desc:
        yt_desc = _generate_description(model, book_name, prompts)
        # Add Amazon link to basic description too (only if generation succeeded)
        if yt_desc:
            yt_desc = _add_amazon_link_to_description(yt_desc, book_name, author, config_dir)

    # Always try to generate TAGS based on main_title and author_name

    # Generate basic tags (book title + author)
    basic_tags = _generate_tags(book_name, author)

    # Generate AI-powered topic tags
    ai_tags = _generate_ai_tags(model, book_name, author, prompts)

    # Combine both: basic tags first, then AI tags
    all_tags = basic_tags + ai_tags

    # Remove duplicates while preserving order
    seen = set()
    tags = []
    for tag in all_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            tags.append(tag)

    # Generate thumbnail elements: hook/sub/image word
    hook, sub, img = _generate_thumbnail_elements(model, book_name, author)

    # UPDATE (not overwrite) existing titles - preserve all original fields
    # This prevents race condition with process.py writing same file
    updated_titles = original_titles.copy()  # Start with all original data

    changed = False
    if yt_title:
        updated_titles["youtube_title"] = yt_title
        changed = True
    if yt_desc:
        # Amazon link already added in _generate_description_with_timestamps
        # or in basic description fallback (no need to add again)
        updated_titles["youtube_description"] = yt_desc
        changed = True
    if tags:
        updated_titles["TAGS"] = tags
        changed = True

    # Add playlist name if not exists - Use Gemini classification
    if "playlist" not in updated_titles:
        try:
            from src.infrastructure.adapters.process import _get_book_playlist
            
            # Use model and prompts from outer scope (already loaded)
            # Get classification from Gemini
            playlist = _get_book_playlist(model, book_name, author, prompts)
            updated_titles["playlist"] = playlist
            changed = True
            print(f"✅ Playlist classified by Gemini: {playlist}")
        except Exception as e:
            print(f"❌ Failed to classify playlist: {e}")
            # Use Self-Development as default only if classification fails
            updated_titles["playlist"] = "Self-Development"
            changed = True

    # Save thumbnail elements with correct keys for thumbnail.py
    if hook is not None:
        updated_titles["thumbnail_title"] = hook  # Main hook for thumbnail
        updated_titles["hook thumbanil"] = hook  # Legacy key (backward compatibility)
        changed = True
    if sub is not None:
        updated_titles["thumbnail_subtitle"] = sub  # Subtitle for thumbnail
        updated_titles["sub hook thumbanil"] = sub  # Legacy key (backward compatibility)
        changed = True
    if img is not None:
        updated_titles["thumbnail_visual_word"] = img  # Visual word for thumbnail
        updated_titles["img thumbanil"] = img  # Legacy key (backward compatibility)
        changed = True

    if changed:
        try:
            # Re-read file before writing to catch any concurrent updates
            # This is CRITICAL to avoid race conditions
            try:
                current_data = json.loads(Path(titles_json).read_text(encoding="utf-8"))
                # Merge: keep current data, overlay with our updates
                final_data = {**current_data, **updated_titles}
            except Exception:
                # If re-read fails, use our data (file might not exist yet)
                final_data = updated_titles

            # Write atomically
            Path(titles_json).write_text(
                json.dumps(final_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print("✅ Updated output.titles.json (preserved existing fields)")
        except Exception as e:
            print(f"❌ Failed to save titles JSON: {e}")
            return None

    return str(Path(titles_json).resolve())


if __name__ == "__main__":
    import sys
    try:
        arg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    except Exception:
        arg_path = None
    if not arg_path or not arg_path.exists():
        # Fallback to runs/latest: support both direct file and path.txt pointer
        root = Path(__file__).resolve().parents[3]  # Fixed: parents[3]
        latest_dir = root / "runs" / "latest"
        candidate = latest_dir / "output.titles.json"
        if candidate.exists():
            arg_path = candidate
        else:
            try:
                ptxt = latest_dir / "path.txt"
                if ptxt.exists():
                    latest_root = Path(ptxt.read_text(encoding="utf-8").strip())
                    cand2 = latest_root / "output.titles.json"
                    if cand2.exists():
                        arg_path = cand2
            except Exception:
                pass
    if not arg_path:
        print("Usage: python -m src.pipeline.youtube_metadata <path/to/output.titles.json>")
        raise SystemExit(2)
    cfg_dir = Path(__file__).resolve().parents[3] / "config"  # Fixed: parents[3]
    res = main(arg_path, cfg_dir)
    if not res:
        raise SystemExit(1)
    print(res)
