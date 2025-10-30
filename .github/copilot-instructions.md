# YouTubeTB - AI Agent Quick Reference Guide

## 🎯 What This Does

Automated YouTube book summary video generator: Arabic YouTube → English videos with AI narration.

**Tech Stack**: Python 3.13, Gemini AI, FFmpeg, Playwright, YouTube API v3, OpenAI.fm TTS

**Current Version**: v2.3.0 (Cookies & Pexels Fallback Systems)

## 🆕 Latest Updates (v2.3.0 - Oct 30, 2025)

- 🍪 **Cookies Fallback**: Multi-file cookies support (cookies.txt → cookies_1.txt → cookies_2.txt → cookies_3.txt)
- 🎬 **Pexels Fallback**: Multi-source API key support (env → .env → pexels_key.txt → api_keys.txt → api_key.txt)
- ✅ **Consistent System**: All fallback systems identical (Gemini, YouTube, Cookies, Pexels)
- 🔍 **Smart Validation**: Auto-validates all files (size, format, content)
- 📋 **Multi-Source**: Support multiple API keys/cookies for fallback
- 🧪 **Test Scripts**: Complete validation tools included

### Previous Updates (v2.2.9 - Oct 26, 2025)

- ✨ **Thumbnail Quality**: Increased to quality=100, dpi=300 (maximum sharpness)
- 🎨 **Book Cover Design**: Elegant soft shadow (Netflix/Audible style) - replaced double border
- 💎 **Main Title Shadow**: Soft 4px shadow with 2px blur for professional depth
- 🔐 **Encrypted Secrets**: Latest OAuth token (6+ months) + API keys on GitHub
- 🚀 **Multi-Device Ready**: Use `python scripts\decrypt_secrets.py` to deploy anywhere

---

## 🚀 Pipeline (11 Stages)

| Stage | Adapter | Input | Output | Key Tech |8. **Thumbnail** → PIL 1920x1080 (8 pro colors)

|-------|---------|-------|--------|----------|9. **Upload** → YouTube OAuth

| 1. Search | `search.py` | Book name (AR/EN) | YouTube video URL | YouTube Data API |10. **Shorts** → 9:16 vertical 60s video

| 2. Transcribe | `transcribe.py` | Video URL | `transcribe.txt` (Arabic) | yt-dlp + cookies |11. **Short Upload** → Shorts to YouTube

| 3. Process | `process.py` | Arabic text | EN script + cover | Gemini AI (3 calls) |

| 4. TTS | `tts.py` | Script | `narration.mp3` | OpenAI.fm (Playwright) |## 📂 Key Files (Quick Access)

| 5. Render | `render.py` | Cover + timestamps | `video_snap.mp4` | FFmpeg + subtitles |```

| 6. Metadata | `youtube_metadata.py` | Script | Title/desc/**tags** | **Gemini AI tags** |src/infrastructure/adapters/

| 7. Merge | `merge_av.py` | Video + audio | Final MP4 | FFmpeg copy codec |├── search.py          # YouTube search (15-90 min filter)

| 8. Thumbnail | `thumbnail.py` | Metadata + cover | `thumbnail.jpg` | PIL + 8 colors |├── transcribe.py      # Extract text

| 9. Upload | `youtube_upload.py` | MP4 + metadata | YouTube video ID | OAuth 2.0 |├── process.py         # AI translation (Gemini)

| 10. Shorts | `shorts_generator.py` | Script + clips | `short_final.mp4` | Pexels API + captions |├── tts.py            # OpenAI.fm TTS (ffprobe only, no Mutagen)

| 11. Short Upload | `youtube_upload.py` | Short MP4 | Shorts video ID | YouTube Shorts API |├── render.py         # Video creation

├── youtube_metadata.py # SEO title/description

---├── merge_av.py       # Final MP4

├── thumbnail.py      # 8-color smart palette

## 📂 Critical File Structure├── youtube_upload.py # OAuth upload

├── shorts_generator.py # Vertical shorts

```└── database.py       # Duplicate detection + YouTube sync

youtubetb_refactored/

├── main.py                    # Entry point → run_menu.pysrc/presentation/cli/

├── books.txt                  # Batch input (one book per line)└── run_pipeline.py   # Main orchestrator (duplicate check FIRST)

├── database.json              # Processed books tracking + YouTube sync```

│

├── config/## ⚡ Critical Code Patterns

│   ├── prompts.json          # Gemini prompts (clean/translate/script)

│   ├── settings.json         # Model, fonts, YouTube sync config### repo_root Calculation

│   └── template.html         # YouTube description template```python

│# ALWAYS use correct depth:

├── secrets/                   # .gitignore - NEVER commit!repo_root = Path(__file__).resolve().parents[3]  # For run_pipeline.py

│   ├── api_key.txt           # Gemini API key (multi-line fallback)repo_root = Path(__file__).resolve().parents[2]  # For adapters/

│   ├── api_keys.txt          # YouTube Data API keys (multi-key)```

│   ├── client_secret.json    # OAuth credentials

│   ├── token.json            # OAuth token (auto-refresh)### Cookies Fallback System (NEW v2.3.0)

│   ├── cookies.txt           # YouTube cookies (Priority 1 - Main)```python

│   ├── cookies_1.txt         # YouTube cookies (Priority 2 - Fallback 1)# Multi-file cookies support (5 locations):

│   ├── cookies_2.txt         # YouTube cookies (Priority 3 - Fallback 2)cookie_paths = [

│   └── cookies_3.txt         # YouTube cookies (Priority 4 - Fallback 3)    "secrets/cookies.txt",      # Priority 1: Main

    "secrets/cookies_1.txt",    # Priority 2: Fallback 1

    "secrets/cookies_2.txt",    # Priority 3: Fallback 2

    "secrets/cookies_3.txt",    # Priority 4: Fallback 3

    "cookies.txt"               # Priority 5: Root fallback

]

# Auto-validates: size > 50 bytes, not HTML, valid format

# Uses first valid, keeps rest as backups

```

│# CORRECT ORDER (check BEFORE add):

├── runs/                      # Generated per bookexisting = check_book_exists(book_name, author_name)

│   └── YYYY-MM-DD_HH-MM-SS_Book-Name/if existing and status == 'uploaded':

│       ├── summary.json       # Pipeline state (resume logic)    shutil.rmtree(d["root"])  # Delete empty folder

│       ├── transcribe.txt     # Arabic source    return  # Stop

│       ├── cleaned.txt        # AI cleanedif not existing:

│       ├── translated.txt     # English translation    add_book(...)  # Only add if NEW

│       ├── script.txt         # Narration script```

│       ├── narration.mp3      # TTS audio

│       ├── video_snap.mp4     # Silent video### Database NoneType Protection (FIXED v2.2.1)

│       ├── output.titles.json # **YouTube metadata + TAGS**```python

│       ├── thumbnail.jpg      # 1920x1080 thumbnail# ALWAYS check None before .strip():

│       ├── bookcover.jpg      # From Google Books/Amazondb_title = book.get("main_title")

│       ├── [YouTube Title].mp4 # Final uploadif not db_title:

│       ├── short_script.txt   # 60s script    continue

│       ├── short_narration.mp3 # Shorts audiotitle_match = str(db_title).strip().lower() == book_lower

│       ├── short_final.mp4    # Vertical short```

│       └── pipeline.log       # Full logs

│### TTS Duration (FIXED v2.2.3)

└── src/infrastructure/adapters/```python

    ├── search.py              # 15-90 min filter# Use ffprobe ONLY (no Mutagen):

    ├── transcribe.py          # yt-dlp extractionresult = subprocess.run(["ffprobe", "-v", "error", ...])

    ├── process.py             # 3 Gemini calls + book coverduration = float(result.stdout.strip())

    ├── tts.py                 # OpenAI.fm TTS (ffprobe only)# Silent success - no spam logs

    ├── render.py              # FFmpeg video composition```

    ├── youtube_metadata.py    # **GEMINI AI TAG GENERATION** ⭐

    ├── merge_av.py            # Final video merge### Thumbnail Subtitle Colors (FIXED v2.2.4)

    ├── thumbnail.py           # 8-color professional palette```python

    ├── youtube_upload.py      # OAuth upload (26-char tag limit)PROFESSIONAL_SUBTITLE_COLORS = [

    ├── shorts_generator.py    # Pexels videos + captions    (255, 215, 0),    # Gold

    └── database.py            # Duplicate detection + YouTube sync    (255, 140, 0),    # Dark Orange

```    (255, 69, 0),     # Red-Orange

    (50, 205, 50),    # Lime Green

---    (0, 191, 255),    # Deep Sky Blue

    (147, 112, 219),  # Medium Purple

## ⚡ Critical Code Patterns    (255, 20, 147),   # Deep Pink

    (255, 255, 100),  # Bright Yellow

### 1. repo_root Calculation (CRITICAL!)]

```python# Pick best contrast with background automatically

# ALWAYS use correct depth based on file location:```



# For adapters/ (search.py, process.py, etc.)## 🔧 Common Commands

repo_root = Path(__file__).resolve().parents[2]```bash

# Example: src/infrastructure/adapters/search.py → parents[2] → repo root# Run pipeline

python main.py  # Interactive menu

# For run_pipeline.py

repo_root = Path(__file__).resolve().parents[3]# Batch processing

# Example: src/presentation/cli/run_pipeline.py → parents[3] → repo rootpython main.py  # Option 2 (books.txt with 20+ books)



# Common mistake: Using wrong depth breaks secrets/ path resolution!# Resume failed run

```python main.py  # Option 13



### 2. YouTube Tag Generation (NEW v2.2.6-7) ⭐# Test individual stage

```pythonpython -m src.infrastructure.adapters.search "العادات الذرية"

# Gemini AI generates ALL tags with SEO optimizationpython -m src.infrastructure.adapters.thumbnail --run "runs/latest" --debug

def _generate_ai_tags(model, book_title, author_name, prompts, target_count=60):

    """# Database sync from YouTube

    Gemini AI generates optimized YouTube tags:python -c "from src.infrastructure.adapters.database import sync_database_from_youtube; sync_database_from_youtube()"

    - 25-30 tags total```

    - Each tag ≤26 chars (YouTube's ACTUAL limit, not 30!)

    - Target 450-495 raw chars## 🐛 Recent Fixes (v2.2.x)

    - Mix: book/author (7), SEO keywords (12), topic tags (10)

    - Prefer spaced tags (80%+) for better SEO### v2.2.6 (2025-10-24)

    - Auto-enforces API limit (499 chars)- **YouTube tags**: Fixed "invalid video keywords" error

    """- **Tag cleanup**: Removed long tags that exceed 30-char limit when truncated

    prompt = f"""You are a YouTube SEO expert...

    Book: {book_title}### v2.2.4 (2025-10-24)

    Author: {author_name}- **Thumbnail colors**: 8 professional colors with auto-contrast selection

    - **TTS logs**: Removed Mutagen spam (use ffprobe only)

    Generate EXACTLY 25-30 tags, each ≤26 chars...

    Return JSON array: ["tag1", "tag2", ...]### v2.2.3 (2025-10-24)

    """- **TTS performance**: Removed Mutagen completely (ffprobe direct)

    - **Silent operation**: No more "⚠️ Mutagen failed" warnings

    # Call Gemini

    resp = model.generate_content(prompt)### v2.2.2 (2025-10-24)

    tags = json.loads(resp.text)  # Parse JSON response- **Empty folders**: Auto-delete when duplicate detected

    - **Duplicate check**: Reversed order (check BEFORE add)

    # Enforce API limit (raw_chars + 2×spaced_tags ≤ 495)- **Clean runs/**: No empty timestamp folders

    final_tags = []

    api_chars = 0### v2.2.1 (2025-10-24)

    for tag in tags:- **Database NoneType**: Fixed 7 functions with defensive None checks

        tag_cost = len(tag) + (2 if " " in tag else 0)- **Graceful handling**: Skip None entries instead of crash

        if api_chars + tag_cost <= 495:

            final_tags.append(tag)## 📋 books.txt Format

            api_chars += tag_cost```

    العادات الذرية

    return final_tags  # ~29 tags, 441 raw chars, 489 API charsالأب الغني والأب الفقير

فن اللامبالاة

# Tag Priority System (FIXED v2.2.7):...

def _merge_tags(primary, ai, density, book_title, author_name):```

    # Register tags by priority (LOWER = HIGHER):- One book per line

    register(must_have, priority=0)    # InkEcho, book summary, audiobook- Arabic or English

    register(ai, priority=1)           # 🌟 AI TAGS HIGHEST (was 3)- 20 books currently (mixed categories)

    register(density, priority=2)      # Compressed tags

    register(primary, priority=3)      # Old basic tags (was 1) - fallback only## 🗂️ File Structure

    register(FALLBACK_DENSE_TAGS, priority=4)```

    runs/YYYY-MM-DD_HH-MM-SS_Book-Name/

    # Result: AI tags override old manual tags ✅├── summary.json         # Pipeline state

```├── transcribe.txt       # Arabic source

├── cleaned.txt          # AI cleaned

### 3. YouTube Upload Tag Limit (FIXED v2.2.6)├── translated.txt       # English

```python├── script.txt           # Narration script

# youtube_upload.py - _sanitize_tag_for_api()├── narration.mp3        # Final audio

# CRITICAL: YouTube's REAL limit is 26 chars, NOT 30!├── video_snap.mp4       # Silent video

├── output.titles.json   # YouTube metadata

if len(s) > 26:  # Changed from 30├── thumbnail.jpg        # 1920x1080

    s = s[:26].rstrip()├── bookcover.jpg        # From Google Books/Amazon

    ├── [YouTube Title].mp4  # Final upload

# Discovered via empirical testing:├── short_video.mp4      # Vertical short

# - Tags ≤26 chars → ✅ SUCCESS└── pipeline.log         # Full logs

# - Tags 27-30 chars → ❌ "invalid video keywords" error```

```

## 🔑 Secrets Structure

### 4. Duplicate Detection (FIXED v2.2.2)```

```pythonsecrets/

# CORRECT ORDER (check BEFORE add to database):├── api_key.txt          # Gemini API

existing = check_book_exists(book_name, author_name)├── api_keys.txt         # YouTube Data API

if existing and existing.get("status") == "uploaded":├── client_secret.json   # OAuth credentials

    shutil.rmtree(run_dir)  # Delete empty folder├── token.json           # OAuth token (auto-refresh)

    print(f"✓ Book already uploaded: {existing['youtube_url']}")└── cookies.txt          # YouTube cookies (age-restricted)

    return  # Stop pipeline```



# Only add if NEW book## 🎨 Config Files

if not existing:```

    add_book(book_name, author_name, status="processing", ...)config/

```├── prompts.json         # AI prompts (clean/translate/script)

├── settings.json        # Model, fonts, YouTube sync

### 5. Database NoneType Protection (FIXED v2.2.1)└── template.html        # Metadata template

```python```

# ALWAYS check None before .strip() or string operations:

db_title = book.get("main_title")### settings.json Quick Ref

if not db_title:  # Skip None entries```json

    continue{

      "gemini_model": "gemini-2.5-flash-latest",

title_match = str(db_title).strip().lower() == book_lower  "thumbnail_font": "Bebas Neue",

```  "youtube_sync": {

    "enabled": true,

---    "channel_id": "UCQyOYMG7mH7kwM5O5kMF6tQ"

  }

## 🔧 Stage-by-Stage Deep Dive}

```

### Stage 6: YouTube Metadata (`youtube_metadata.py`) ⭐ CRITICAL!

## ⚠️ Known Issues

**Tag Generation System** (v2.2.6-7):1. **Long videos (>90 min)**: Gemini truncates → Use filter in search.py

2. **Cookies required**: Age-restricted videos need `cookies.txt`

```python3. **ffprobe required**: Critical for TTS timestamps

# Main function orchestrates tag generation:4. **Playwright setup**: Run `playwright install chromium`

def main(titles_json_path, config_dir=None):

    # ... load metadata ...## 🧪 Testing

    ```bash

    # OLD System (still exists but deprioritized):# Database tests

    basic_tags = _generate_tags(book_title, author_name)  # 21 tagspython scripts\test_db_none_fix.py

    density_tags = _build_density_tags(book_title, author_name)  # 10 compressedpython scripts\test_duplicate_folder_cleanup.py

    

    # NEW System (PRIMARY):# Font profiles

    ai_tags = _generate_ai_tags(model, book_title, author_name, prompts, target_count=60)python test_font_profiles.py

    # Returns: 25-30 content-aware tags

    # Example: "habit stacking", "1 percent better", "four laws of behavior"# YouTube sync

    python scripts/test_sync.py

    # Merge with correct priority:```

    tags, raw_chars, api_chars = _merge_tags(

        primary=basic_tags,      # Priority 3 (low - fallback)## 📊 Database Schema

        ai=ai_tags,              # Priority 1 (HIGH) ⭐```json

        density=density_tags,    # Priority 2 (medium){

        book_title=book_title,  "books": [

        author_name=author_name    {

    )      "main_title": "Book Name",

          "author_name": "Author",

    # Save to output.titles.json:      "status": "processing|uploaded|done",

    metadata["tags"] = tags  # ~29 tags, ≤26 chars each      "youtube_url": "https://youtube.com/watch?v=...",

```      "youtube_short_url": "https://youtube.com/watch?v=...",

      "run_folder": "2025-10-24_XX-XX-XX_Book-Name",

**AI Tag Generation Details**:      "date_added": "2025-10-24T18:00:00"

    }

```python  ]

def _generate_ai_tags(model, book_title, author_name, prompts, target_count=60):}

    """```

    Gemini generates tags optimized for YouTube SEO

    ## 🎯 AI Agent Guidelines

    Prompt includes:

    - EXACTLY 25-30 tags### When User Reports Error

    - Each MUST be ≤26 characters (STRICT)1. **Check latest logs**: `runs/latest/pipeline.log`

    - Target 450-495 total raw chars2. **Check summary.json**: See which stage failed

    - Mix of:3. **Run stage standalone**: `python -m src.infrastructure.adapters.STAGE`

      * Book/Author combos (5-7): "Atomic Habits", "James Clear", "Atomic Habits James Clear"4. **Check database.json**: For duplicate/NoneType issues

      * SEO keywords (10-12): "self improvement", "personal development", "productivity"

      * Topic-specific (8-10): "habit stacking", "1 percent better", "identity based habits"### When User Wants New Feature

    - Prefer spaced tags over compressed (80%+ for SEO)1. **Identify stage**: Which adapter needs modification?

    - Return JSON array format2. **Check existing patterns**: Follow defensive coding (None checks)

    3. **Test standalone**: Run adapter's `main()` before integration

    Returns:4. **Update this file**: Add to Recent Fixes section

        List of sanitized tags with API limit enforcement

    """### When User Asks "Why?"

    1. **Search this file first**: Use Ctrl+F

    # Example output for "Atomic Habits":2. **Check Recent Fixes**: Likely documented

    [3. **Read code comments**: Adapters have inline docs

        "Atomic Habits",              # 13 chars4. **Check docs/**: Detailed documentation exists

        "James Clear",                # 11 chars

        "Atomic Habits book summary", # 26 chars---

        "habit stacking",             # 14 chars

        "1 percent better",           # 16 chars**Last Updated**: 2025-10-24 (Optimized for AI agent speed)

        "four laws of behavior",      # 21 chars  - `process.py`: `parents[2]` (src/infrastructure/adapters → root)

        "identity based habits",      # 21 chars  - `run_pipeline.py`: `parents[3]` (src/presentation/cli → root)

        # ... 22 more tags- **Secrets**: Prioritize `secrets/` folder over root (e.g., `secrets/api_key.txt` > `api_key.txt`)

    ]- **Cookies**: Search order: `secrets/cookies.txt` → `cookies.txt` (required for age-restricted videos)

    # Total: 29 tags, 441 raw chars, 489 API chars (80%+ spaced)

```## Core Components



**Tag Priority Merge**:### 1. Search (`search.py`)

**Purpose**: Find optimal book summary videos on YouTube.

```python

def _merge_tags(primary, ai, density, book_title, author_name):**Filters** (Lines 194-199):

    """```python

    Deduplicates and prioritizes tagsif total_seconds < 900 or total_seconds > 5400:  # 15-90 min

        excluded_count += 1

    Priority levels (lower = higher priority):    continue

    0. must_have: InkEcho, book summary, audiobook (always included)```

    1. AI tags: Content-aware Gemini tags (HIGHEST - v2.2.7 fix)- Excludes: <15 min (too short), >90 min (causes Gemini truncation)

    2. density: Compressed tags without spaces- **Why 90 min max**: Longer videos → 18k+ words → Gemini output limits → severe content loss

    3. basic/primary: Old manual tags (FALLBACK only)

    4. FALLBACK_DENSE_TAGS: Last resort**Dual-Phase Search**:

    1. Relevance-based (15 results) - popular videos

    Deduplication: Uses casefold() keys2. Date-based (10 results) - recent uploads

    API limit: Stops at 495 chars (leaves 4-char buffer)3. Sorts by duration (longest first) after filtering

    Max tags: 30 (YouTube limit)

    """### 2. Process (`process.py`) - THE BOTTLENECK

    **Three Gemini Calls**:

    # Example priority resolution:1. `_clean_source_text()` - Remove intro/outro, keep book content only

    # AI tag: "habit stacking" (priority 1)2. `_translate_to_english()` - Arabic → English (preserves ALL details)

    # Manual tag: "James Clear business strategy" (priority 3)3. `_scriptify_youtube()` - Reformat for YouTube narration

    # → AI tag wins ✅

```**Model**: `gemini-2.5-flash-latest` (configurable via `config/settings.json` → `gemini_model`)



**Why This Matters**:**Critical Issue**: No text chunking! Large transcripts (18k words) exceed output limits.

- Result: Gemini auto-summarizes despite "DO NOT SUMMARIZE" prompt

1. **Content-Aware Tags**: AI understands book content- Example: 18,981 word input → 2,046 word translation (89% loss!)

   - "habit stacking" (from Atomic Habits chapter)

   - "1 percent better" (book's main concept)**Book Cover Fetching** (`_get_book_cover_from_amazon`, Line 220):

   - "four laws of behavior" (book framework)- **Primary Method**: Google Books API (fast, reliable, no scraping)

   - **Fallback Methods**: Amazon.com scraping (English titles only) with Playwright, then requests

2. **Better SEO**: 80%+ spaced tags- **Why Google Books First**: Much faster than browser automation, reliable API

   - "self improvement" >> "selfimprovement"- **Amazon Scoring Algorithm** (if used):

   - Natural language matches search queries  ```python

  position_score = (5 - idx) * 10  # First result = 50 points

3. **API Compliance**: Respects YouTube's REAL limits  rating_score = rating * 10        # 4.7 stars = 47 points

   - 26 chars per tag (not 30!)  review_score = min(reviews/100, 10)  # Capped at 10

   - 499 API chars total (raw + 2×spaced)  total = position + rating + review

  ```

4. **Automatic**: No manual tag maintenance needed- **Old Methods Removed**: `_get_cover_goodreads`, `_get_cover_openlibrary`, `_get_cover_googlebooks` (replaced with API)



---### 3. TTS (`tts.py`)

**Service**: OpenAI.fm (free TTS via Playwright scraping)

## 🎯 Common Workflows- Chunks text into ≤950 char segments (CSV-based)

- Voice: "Shimmer" (hardcoded, configurable via `DEFAULT_VOICE`)

### Test Tag Generation- Retries: 10 attempts per chunk with exponential backoff

```bash- **Script cleaning** (`_clean_script_markers`, Line 55): Removes prompt structure markers like `**[HOOK]**`, `**[CONTEXT]**` before TTS

# Test integrated system:- **Legacy**: Mutagen timestamp extraction often fails → falls back to `ffprobe`

python scripts/test_integrated_tags.py- **Whisper alignment**: Optional word-level timestamps via `whisper` (if installed)



# Expected output:### 4. Render (`render.py`)

# ✅ 29 tags**FFmpeg Pipeline**:

# ✅ 441 raw chars (target: 450-495)1. Parse `timestamps.json` (Whisper word-level alignment)

# ✅ 489 API chars (limit: 499)2. Create timed subtitle overlays (`drawtext` filters)

# ✅ All tags ≤26 chars3. Composite: background gradient + book cover + animated text

# ✅ 80%+ spaced tags4. Output: 1920x1080, 30fps, CRF 23

```

**Key Files**:

### Debug Tag Issues- `config/template.html` - Not used in render, only for metadata

```bash- `assets/fonts/` - Custom fonts for text rendering

# Check generated tags:

cat runs/latest/output.titles.json | python -m json.tool### 5. YouTube Metadata (`youtube_metadata.py`)

**Purpose**: Generate SEO-optimized YouTube video metadata using Gemini AI.

# Verify tag lengths:

python -c "import json; tags=json.load(open('runs/latest/output.titles.json'))['tags']; print([(t, len(t)) for t in tags])"**What it generates**:

- **YouTube Title**: Catchy, clickable title (max 100 chars)

# Check API chars:  - Pattern: `"[Hook] – [Book Name] | Book Summary"`

python -c "import json; tags=json.load(open('runs/latest/output.titles.json'))['tags']; print(sum(len(t) + (2 if ' ' in t else 0) for t in tags))"  - Example: `"Master Your Mind – Atomic Habits | Book Summary"`

```- **YouTube Description**: Full description with timestamps, chapters, links

  - Includes: Book intro, key concepts, author info, timestamps

---  - Adds: Channel link, playlist links, call-to-action

- **Thumbnail Hooks**: Short punchy text for thumbnail overlay

## 🐛 Known Issues & Fixes  - `thumbnail_title`: Main hook (5-6 words max)

  - `thumbnail_subtitle`: Supporting text (author or key benefit)

### Issue 7: AI Tags Ignored by Old Tags (FIXED v2.2.7) ⭐- **Tags**: Relevant YouTube tags for SEO

**Symptom**: Generic manual tags override smart AI tags

**Gemini Prompts** (from `config/prompts.json`):

**Example**:- `youtube_title_template` - Title generation prompt

```python- `youtube_description_template` - Description generation prompt

# Before fix:- `thumbnail_hook_template` - Thumbnail text prompt

# AI generates: "habit stacking" (relevant to Atomic Habits)

# Manual generates: "James Clear business strategy" (generic)**Output File**: `output.titles.json` with all metadata fields

# Result: Manual tag used (wrong priority) ❌

**Model Config**:

# After fix:- Uses same Gemini model as Process stage (configurable in `settings.json`)

# AI tag priority: 1 (highest)- Fallback to `gemini-2.5-flash` if specified model fails

# Manual tag priority: 3 (fallback)

# Result: AI tag used ✅### 6. Merge (`merge_av.py`)

```**Purpose**: Combine video and audio into final uploadable MP4.



**Cause**: Wrong priority assignment in `_merge_tags()`**Input Files**:

- `video_snap.mp4` - Silent video from Render stage (1920x1080)

**Fix**: Reversed priorities (commit 240e5ab)- `narration.mp3` - Audio from TTS stage

```python- `output.titles.json` - YouTube title for filename

# Before:

register(primary, priority=1)  # Manual tags high**Process**:

register(ai, priority=3)       # AI tags low ❌1. Read YouTube title from `output.titles.json`

2. Sanitize title for filename (remove special chars, limit length)

# After:3. Run FFmpeg merge:

register(ai, priority=1)       # AI tags high ✅   ```bash

register(primary, priority=3)  # Manual tags fallback   ffmpeg -i video_snap.mp4 -i narration.mp3 \

```          -c:v copy -c:a aac -b:a 192k \

          -shortest "[YouTube Title].mp4"

**Result**:    ```

- Content-aware tags now used4. Delete old output if re-running (Unicode normalization handling)

- "habit stacking", "1 percent better" appear in final output

- Better SEO and discoverability**Output**: `[YouTube Title].mp4` ready for upload



---**Smart Filename Handling**:

- Handles Unicode issues (em dash → spaces)

## 🚀 Recent Changes (Version History)- Truncates to 120 chars max

- Fuzzy matching to delete old versions

### v2.2.7 (2025-10-26) - Tag Priority Fix ⭐

- ✅ AI tags now priority 1 (was 3)### 7. Thumbnail (`thumbnail.py`)

- ✅ Old manual tags fallback to priority 3 (was 1)**Purpose**: Generate professional 16:9 thumbnail with dynamic text sizing.

- ✅ Prevents generic tags from overriding content-aware AI tags

- ✅ Result: "habit stacking", "1 percent better" now used**Multi-Font System** (v2.2.0):

- ✅ Commit: 240e5abThree font profiles with independent sizing dynamics:



### v2.2.6 (2025-10-24) - Gemini AI Tag Generation ⭐1. **Bebas Neue** (Default - Bold Display):

- ✅ Complete rewrite of `_generate_ai_tags()` with SEO-focused prompt   - Base size: 100px

- ✅ JSON output parsing (was CSV)   - Range: 60-140px

- ✅ Auto-enforces API limit (495 chars)   - Best for: Short punchy hooks (3-5 words)

- ✅ Each tag ≤26 chars (discovered YouTube's real limit)   - Scaling: Aggressive reduction for long text

- ✅ Generates 25-30 tags, 450-495 raw chars, 80%+ spaced tags

- ✅ Content-aware: "habit stacking", "1 percent better", "four laws"2. **Cairo** (Arabic-friendly):

- ✅ YouTube upload: 26-char limit (was 30)   - Base size: 85px

- ✅ Commits: ab8cff3, 9cce9df   - Range: 50-120px

   - Best for: Mixed language titles

### v2.2.4 (2025-10-24) - Thumbnail & TTS   - Scaling: Moderate, balanced

- ✅ 8 professional subtitle colors with auto-contrast

- ✅ TTS: Removed Mutagen completely (ffprobe only)3. **Impact** (Heavy Bold):

- ✅ Silent operation (no spam logs)   - Base size: 95px

   - Range: 55-130px

### v2.2.2 (2025-10-24) - Empty Folder Cleanup   - Best for: Strong statements

- ✅ Duplicate books auto-delete empty run folders   - Scaling: Similar to Bebas but slightly smaller

- ✅ Reversed duplicate check order (check BEFORE add)

- ✅ Clean `runs/` directory**Dynamic Sizing Algorithm**:

```python

### v2.2.1 (2025-10-24) - Database NoneType Fix# Word count based adjustment

- ✅ Defensive None checks in 7 database functionsif words <= 3: size = base_size

- ✅ Graceful handling of None titles/authorselif words <= 5: size = base_size * 0.9

elif words <= 7: size = base_size * 0.75

### v2.1.0 - YouTube Sync Systemelse: size = base_size * 0.6

- ✅ Auto-sync database.json from YouTube channel

- ✅ Cross-environment duplicate detection# Enforce min/max bounds

size = max(min_size, min(size, max_size))

---```



## 🎯 Key Takeaways for AI Agent**Thumbnail Elements**:

1. **Background**: Gradient or solid color

1. **Tag Generation**: Gemini AI is PRIMARY (v2.2.6+)2. **Book Cover**: Positioned and scaled

2. **Tag Priority**: AI = 1, Manual = 3 (v2.2.7 fix)3. **Main Title**: `thumbnail_title` (large, bold)

3. **Tag Limit**: 26 chars per tag (NOT 30!)4. **Subtitle**: `thumbnail_subtitle` (smaller, under title)

4. **API Limit**: 499 chars (raw + 2×spaced)5. **Effects**: Drop shadow, outline for readability

5. **repo_root**: Always use correct `parents[N]` depth

6. **None checks**: Always check before string ops**Input**: `output.titles.json` (needs `thumbnail_title` and `thumbnail_subtitle`)

7. **Duplicate check**: BEFORE creating folder**Output**: `thumbnail.jpg` (1280x720, 16:9)

8. **YouTube sync**: Auto-syncs from channel

**Fallback System**:

**When debugging tags**:- If `thumbnail_title` missing → use `main_title` or `youtube_title`

1. Check `output.titles.json` → `tags` field- If `thumbnail_subtitle` missing → use `author_name` or `"Book Summary"`

2. Verify each tag ≤26 chars- If font not found → graceful degradation to system font

3. Calculate API chars: `sum(len(t) + (2 if ' ' in t else 0))`

4. Should see content-aware tags (e.g., "habit stacking")**Font Loading Priority**:

5. 80%+ should be spaced tags1. `assets/fonts/[FontName].ttf`

2. System fonts (Windows: `C:\Windows\Fonts\`)

**This file is the single source of truth for the entire project.**3. Fallback to PIL default

When in doubt, search this file first! 🎯

### 8. Pipeline Orchestration (`run_pipeline.py`)

---**Stage Management**:

- Saves `summary.json` after EVERY stage completion

**Last Updated**: 2025-10-26- Resume capability: `--resume` flag reads last successful stage

**Version**: v2.2.7- Retry logic: Max 10 attempts per stage with exponential backoff

**AI Agent Optimized**: ✅ Yes- **Dual-check validation**: Stage marked complete ONLY if `summary.json` says "ok" AND artifact file exists

**Total Sections**: 15

**Total Lines**: ~600**Critical Resume Logic** (`_should_retry_stage`, Line 240):

```python
# If stage was completed successfully → Skip
# If stage was the one that failed → Retry
# If stage comes after failed stage → Run (continue pipeline)
```

**Preflight Checks** (`_preflight_check`, Line 344):
```python
repo_root = Path(__file__).resolve().parents[3]  # CRITICAL: Must be 3, not 2!
```
- Validates: Internet, FFmpeg, yt-dlp, Playwright, cookies, API keys
- Fixed Bug: Was using `parents[2]` → couldn't find `secrets/cookies.txt`

**Database Sync** (`_ensure_database_synced`, Line 47):
- Called at pipeline start to check if `database.json` has data
- If empty → auto-syncs from YouTube channel using `sync_database_from_youtube()`
- Prevents duplicate processing across machines (Local → Colab → Server)
- See `docs/DUPLICATE_CHECK_SYSTEM.md` for complete sync architecture

### 9. Upload (`youtube_upload.py`)
**Purpose**: Upload video to YouTube using OAuth 2.0.

**OAuth Flow**:
1. **First Run**: Reads `secrets/client_secret.json` (OAuth credentials)
2. Opens browser for user consent
3. Saves `secrets/token.json` for future runs
4. **Subsequent Runs**: Uses saved token (auto-refresh)

**Upload Parameters**:
- **Title**: From `output.titles.json` → `youtube_title`
- **Description**: From `output.titles.json` → `youtube_description`
- **Privacy**: `public` / `private` / `unlisted` (configurable)
- **Category**: 27 (Education)
- **Tags**: From `output.titles.json` (if available)

**Thumbnail Upload Priority**:
```python
# Priority order (first found is used):
1. short_thumbnail.jpg  # For Shorts (9:16 vertical)
2. thumbnail.jpg        # Main video (16:9 horizontal)
3. cover_processed.jpg  # From render stage
4. bookcover.jpg        # Original book cover
```

**Video File Detection**:
- Uses `youtube_title` from metadata to find `[YouTube Title].mp4`
- Sanitizes filename to match merge output

**Database Update**:
- After successful upload → updates `database.json`:
  ```python
  update_book_status(
      book_name=book_name,
      status="uploaded",  # or "done" after shorts upload
      youtube_url="https://youtube.com/watch?v=VIDEO_ID"
  )
  ```

**Error Handling**:
- Retries upload on failure (max 10 attempts)
- Exponential backoff between retries
- Validates token before upload

### 10. Shorts Generator (`shorts_generator.py`)
**Purpose**: Create engaging 60-second vertical video (9:16) for YouTube Shorts.

**Complete Workflow**:
1. **Script Generation**: AI creates 60s engaging script with hook
2. **TTS Conversion**: Generate audio (auto-trim if >60s)
3. **Subtitle Creation**: Word-level timestamps using Whisper
4. **Vertical Video Composition**: 
   - Resolution: 1080x1920 (9:16)
   - Background: Gaussian blur + vignette effect
   - Book cover: Centered, scaled appropriately
   - Captions: Single-line with word-by-word highlighting

**AI Script Generation**:
- Gemini prompt: "Create 60-second engaging script"
- Focus: Hook first 3 seconds, build curiosity, CTA at end
- Output: `short_script.txt`

**TTS with Auto-Trim**:
- Uses same OpenAI.fm as main TTS
- **Critical**: If audio >60s → automatically trims to 60s
- Preserves quality: Fades out last 2s to avoid abrupt cut

**Subtitle System**:
- **Primary**: Whisper word-level alignment (if installed)
- **Fallback**: Simple word duration estimate
- Format: JSON with `[{word, start, end}]`

**Video Effects**:
```python
# Background: Gaussian blur (sigma=20)
background = book_cover.filter(ImageFilter.GaussianBlur(20))

# Vignette: Darker edges, brighter center
vignette = radial_gradient(center_bright=1.0, edge_dark=0.4)

# Caption styling:
- Font: Bold, high contrast (white + black outline)
- Position: Bottom third (safe zone)
- Highlighting: Current word in yellow/gold
- Animation: Word-by-word reveal
```

**FFmpeg Composition**:
```bash
ffmpeg -loop 1 -i background_blur.jpg \
       -i book_cover.png \
       -i captions_%d.png \
       -filter_complex "[overlay + vignette + captions]" \
       -t 60 -r 30 short_video.mp4
```

**Output Files**:
- `short_video.mp4` - Final vertical video (1080x1920)
- `short_script.txt` - AI-generated script
- `short_audio.mp3` - TTS audio (≤60s)
- `short_subtitles.json` - Word timestamps

**YouTube Shorts Constraints**:
- ⚠️ **NO custom thumbnails** (YouTube Shorts limitation)
- Must be <60s duration
- Must be 9:16 aspect ratio
- First frame used as thumbnail (auto-generated by YouTube)

**Upload Integration**:
- After shorts generation → `short_upload` stage
- Links to main video in description
- Separate video ID in database (`short_url` field)

### 11. Database & Duplicate Detection (`database.py`)
**Purpose**: Track processed books and prevent duplicates across environments.

**Key Functions**:
- `check_book_exists(book_name, author_name)` - Returns existing book entry or None
- `add_book()` - Adds new book with status="processing"
- `update_book_status()` - Updates status to "uploaded" with YouTube URLs
- `sync_database_from_youtube()` - **CRITICAL** for cross-environment sync

**YouTube Channel Sync** (Line 600+):
- Solves: Local `database.json` not synced to Colab/remote (in `.gitignore`)
- How: Fetches all videos from channel, extracts book names from titles
- Pattern: `"[Intro] – [Book Name] | Book Summary"` → extracts "Book Name"
- Triggered: Automatically when `database.json` is empty (see `run_pipeline.py:47`)
- Config: `config/settings.json` → `youtube_sync.enabled` and `youtube_sync.channel_id`

**Example Flow**:
```python
# Local machine processes "Atomic Habits" → uploads to YouTube
# Colab starts with empty database.json
# Pipeline calls _ensure_database_synced()
# → Syncs from YouTube → Finds "Atomic Habits" already exists
# → Skips duplicate processing ✅
```

## Configuration

### `config/prompts.json`
- **Immutable Templates**: `clean_template`, `translate_template`, `youtube_script_template`
- **Key Instruction**: Line 24: `"Do NOT add, omit, or summarize."` (often ignored due to Gemini limits)

### `config/settings.json` (Dynamic)
- `gemini_model`: Model selection (default: `gemini-2.5-flash`)
- `prefer_local_cover`: Download cover locally vs. use URL
- `cover_source`: Legacy field (now always uses Google Books API → Amazon fallback)
- `thumbnail_font_profiles`: **NEW!** Font-specific sizing dynamics (Bebas Neue, Cairo, Impact)
  - Each font has independent base_size, min/max bounds, scaling factors
  - See `docs/FONT_PROFILE_SYSTEM.md` for complete guide
- **YouTube Sync** (NEW - v2.1.0):
  ```json
  "youtube_sync": {
    "enabled": true,
    "channel_id": "UCQyOYMG7mH7kwM5O5kMF6tQ",
    "cache_duration_hours": 1
  }
  ```
  - Auto-syncs `database.json` from YouTube channel (prevents duplicates across machines)
  - Extracts book names from video titles using pattern: `"– Book Name | Book Summary"`
  - Critical for Colab/remote environments where local database is empty
- **YouTube Sync** (NEW - v2.1.0):
  ```json
  "youtube_sync": {
    "enabled": true,
    "channel_id": "UCQyOYMG7mH7kwM5O5kMF6tQ",
    "cache_duration_hours": 1
  }
  ```
  - Auto-syncs `database.json` from YouTube channel (prevents duplicates across machines)
  - Extracts book names from video titles using pattern: `"– Book Name | Book Summary"`
  - Critical for Colab/remote environments where local database is empty

## Developer Workflows

### Run Full Pipeline
```bash
python main.py  # Interactive menu (Option 1: Single book)
# Batch processing (Option 2: Multiple books from books.txt)
run.bat         # Windows shortcut with venv activation
```

### Batch Processing (Auto-Continue Mode)
```bash
# Create books.txt in root with book titles (one per line, Arabic or English)
# Option 2 from menu OR:
python -m src.presentation.cli.run_pipeline --batch books.txt --auto-continue

# --auto-continue: No user prompts, automatic error handling
# Perfect for overnight processing or remote servers
# Exit codes: 0=success, 1=critical error, 130=interrupted
```

### Test Individual Stages
```python
# Each adapter has standalone main()
python -m src.infrastructure.adapters.search "العادات الذرية"
python -m src.infrastructure.adapters.transcribe --url "https://youtube.com/watch?v=..."
python -m src.infrastructure.adapters.process "path/to/run_dir"
python -m src.infrastructure.adapters.tts "path/to/script.txt" "path/to/output_dir"
python -m src.infrastructure.adapters.render "path/to/run_dir"
python -m src.infrastructure.adapters.youtube_metadata "path/to/run_dir"
python -m src.infrastructure.adapters.merge_av "path/to/run_dir"
python -m src.infrastructure.adapters.thumbnail "path/to/run_dir"
python -m src.infrastructure.adapters.youtube_upload "path/to/run_dir"

# Test shorts generation
from src.infrastructure.adapters.shorts_generator import generate_short
generate_short(run_dir=Path("runs/latest"))
```

### Resume Failed Run
```bash
python main.py
# Option 13 → Auto-detects last run and resumes from failed/incomplete stage
# Checks both summary.json status AND artifact files existence
```

### Test YouTube Metadata Generation
```bash
# Standalone test
cd runs/<timestamp>_<book_name>
python -m src.infrastructure.adapters.youtube_metadata .

# Check output
cat output.titles.json
```

### Test Thumbnail Generation
```bash
# With custom font
python -m src.infrastructure.adapters.thumbnail runs/latest

# Test different fonts (in config/settings.json)
{
  "thumbnail_font": "Bebas Neue",  // or "Cairo" or "Impact"
  "thumbnail_font_profiles": {...}
}
```

### Test Merge Stage
```bash
# Ensure video_snap.mp4 and narration.mp3 exist
python -m src.infrastructure.adapters.merge_av runs/latest

# Output: [YouTube Title].mp4
```

### Debugging Process Issues
```python
# Check transcript size
words = len(open("runs/.../transcribe.txt").read().split())
# If >15k words → expect translation truncation

# Verify model config
import json
cfg = json.load(open("config/settings.json"))
print(cfg.get("gemini_model"))  # Should be gemini-2.5-flash or gemini-2.5-flash-latest

# Test database sync
from src.infrastructure.adapters.database import sync_database_from_youtube
synced = sync_database_from_youtube()  # Syncs from YouTube channel

# Test OAuth token
from src.infrastructure.adapters.youtube_upload import _get_credentials
creds = _get_credentials(secrets_dir=Path("secrets"))
print("Token valid!" if creds else "Token expired/missing")

# Test database NoneType fix
python scripts\test_db_none_fix.py  # Verifies defensive None checks work
```

### Test Shorts Generator
```bash
# Full shorts generation (AI script → TTS → video → upload)
python main.py
# Option 14: Generate shorts for existing run

# Or programmatically:
from src.infrastructure.adapters.shorts_generator import generate_short
success = generate_short(
    run_dir=Path("runs/2025-10-24_18-03-26_Book-Name"),
    debug=True
)
```

## Common Patterns

### Error Handling: Silent Failures
Most adapters use `try/except` with print statements, not exceptions:
```python
try:
    result = risky_operation()
except Exception as e:
    print(f"❌ Failed: {e}")
    return None  # Caller checks for None
```

### Arabic Text Display
All CLI modules use:
```python
from bidi.algorithm import get_display
import arabic_reshaper
text = get_display(arabic_reshaper.reshape(arabic_text))
```

### Path Resolution Pattern
```python
from pathlib import Path
repo_root = Path(__file__).resolve().parents[N]  # N = depth
secrets_file = repo_root / "secrets" / "api_key.txt"
if secrets_file.exists():
    api_key = secrets_file.read_text().strip()
```

## Known Issues & Workarounds

### 1. Long Videos Cause Content Loss
**Symptom**: 13-min audio from 118-min source video (should be 30+ min)
**Root Cause**: No text chunking in `_translate_to_english()` → Gemini truncates
**Workaround**: Filter videos to <90 min (already implemented in search.py)
**Proper Fix**: Implement chunked translation:
```python
def _translate_in_chunks(model, text, chunk_size=5000):
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return "\n".join(_translate_to_english(model, chunk) for chunk in chunks)
```

### 2. Cookies Not Found (Despite Existing)
**Symptom**: "cookies.txt not found" even when `secrets/cookies.txt` exists
**Cause**: Incorrect `repo_root` calculation (was `parents[2]`, should be `parents[3]`)
**Fix**: Line 344 in `run_pipeline.py` now uses `parents[3]`

### 3. OpenAI.fm TTS Unreliable
**Symptom**: Random timeouts, "Download failed" errors
**Workaround**: Built-in retry logic (10 attempts, exponential backoff)
**Alternative**: Consider ElevenLabs API (paid but reliable)

### 4. YouTube OAuth Token Expired
**Symptom**: Upload fails with "invalid_grant" or "token expired"
**Cause**: Token refresh failed or credentials changed
**Fix**: Delete `secrets/token.json` and re-authenticate
```bash
rm secrets/token.json
python -m src.infrastructure.adapters.youtube_upload runs/latest
# Browser will open for OAuth consent
```

### 5. Thumbnail Generation Fails
**Symptom**: `thumbnail.jpg` not created, uses `bookcover.jpg` as fallback
**Cause**: Font not found or missing `thumbnail_title` in metadata
**Fix 1**: Install Bebas Neue font to `assets/fonts/BebasNeue.ttf`
**Fix 2**: Check `output.titles.json` has `thumbnail_title` and `thumbnail_subtitle`
```bash
# Verify font
ls assets/fonts/BebasNeue.ttf

# Check metadata
cat runs/latest/output.titles.json | grep thumbnail_title
```

### 6. FFmpeg Merge Fails
**Symptom**: `[YouTube Title].mp4` not created
**Cause**: Missing `video_snap.mp4` or `narration.mp3`
**Fix**: Check Render and TTS stages completed successfully
```bash
ls runs/latest/video_snap.mp4
ls runs/latest/narration.mp3
```

### 7. Shorts Upload Fails (Main Video Uploaded)
**Symptom**: Main video uploaded but short fails
**Cause**: Short video not generated or YouTube API quota exceeded
**Fix**: Check `short_video.mp4` exists and re-upload manually
```bash
# Check short video
ls runs/latest/short_video.mp4

# Manual upload
python -m src.infrastructure.adapters.youtube_upload runs/latest --is-short
```

### 8. Database Not Syncing from YouTube
**Symptom**: Duplicate videos uploaded despite YouTube sync enabled
**Cause**: Wrong channel ID or API quota exceeded
**Fix**: Verify `config/settings.json` → `youtube_sync.channel_id`
```bash
# Test sync manually
python -c "from src.infrastructure.adapters.database import sync_database_from_youtube; sync_database_from_youtube()"
```

### 9. Database NoneType Error (FIXED - v2.2.1)
**Symptom**: `⚠️ Failed to update database status: 'NoneType' object has no attribute 'strip'`
**Cause**: Books with `None` values in `main_title` or `author_name` fields
**Fix Applied**: Added defensive None checks to 7 functions in `database.py`
**Status**: ✅ RESOLVED - All database operations now skip None entries gracefully
**Test**: Run `python scripts\test_db_none_fix.py` to verify
**Documentation**: See `docs/DATABASE_NONETYPE_FIX.md` for complete details

Functions Fixed:
- `check_book_exists()` - Book existence check
- `update_book_status()` - Status updates (processing → uploaded → done)
- `update_youtube_url()` - Main video URL updates
- `update_book_youtube_url()` - Legacy URL updates
- `remove_book()` - Book removal
- `update_book_short_url()` - Shorts URL updates
- `update_run_folder()` - Run folder path updates

**Pattern Applied**:
```python
# Before (unsafe):
title_match = book.get("main_title", "").strip().lower() == book_lower

# After (safe):
db_title = book.get("main_title")
if not db_title:
    continue  # Skip books with None titles
title_match = str(db_title).strip().lower() == book_lower
```

### 10. Empty Run Folders for Duplicate Books (FIXED - v2.2.2)
**Symptom**: When duplicate book detected, pipeline stops but leaves empty folder `runs/2025-10-24_XX-XX-XX/`
**Root Cause**: 
1. Pipeline creates run folder FIRST
2. Then adds book to database
3. Then checks for duplicates
4. If duplicate found → stops but doesn't delete folder
5. Result: Empty folders clutter `runs/` directory

**Fix Applied**: 
1. Reversed order: Check duplicates BEFORE adding to database
2. Auto-delete empty folder when duplicate detected
3. Prevents database pollution (no duplicate entries)

**Code Changes** (`run_pipeline.py`):
```python
# BEFORE (wrong order):
add_book(book_name, author_name, ...)  # Add first
existing = check_book_exists(...)      # Then check (too late!)
if existing: return                    # Folder already created ❌

# AFTER (correct order):
existing = check_book_exists(...)      # Check FIRST ✅
if existing and status == 'uploaded':
    shutil.rmtree(d["root"])          # Delete empty folder ✅
    return                             # Stop cleanly
if not existing:
    add_book(...)                      # Only add if NEW ✅
```

**Status**: ✅ RESOLVED  
**Test**: `python scripts\test_duplicate_folder_cleanup.py`  
**Impact**: No more empty folders in `runs/`, cleaner file structure

## Testing Strategy

**No formal test suite** - Validation via:
1. `run_menu.py` → Option 0: Comprehensive API/tool validation
2. Stage isolation: Each adapter's `main()` function
3. Real-world runs: Check `runs/*/pipeline.log` for errors

**Example Manual Tests**:
```bash
# Test search filter changes
python -m src.infrastructure.adapters.search "الأب الغني والأب الفقير"
# Verify: Only videos 15-90 min accepted

# Test Amazon scraper
python -c "from src.infrastructure.adapters.process import _get_book_cover_from_amazon; \
print(_get_book_cover_from_amazon('Atomic Habits', 'James Clear'))"

# Test YouTube metadata generation
python -m src.infrastructure.adapters.youtube_metadata runs/latest
cat runs/latest/output.titles.json

# Test thumbnail with specific font
python -m src.infrastructure.adapters.thumbnail runs/latest
# Check output: thumbnail.jpg (1280x720)

# Test merge
python -m src.infrastructure.adapters.merge_av runs/latest
ls runs/latest/*.mp4  # Should show [YouTube Title].mp4

# Test shorts generation
python -c "from src.infrastructure.adapters.shorts_generator import generate_short; \
from pathlib import Path; \
generate_short(Path('runs/latest'), debug=True)"

# Test database sync
python -c "from src.infrastructure.adapters.database import sync_database_from_youtube; \
synced = sync_database_from_youtube(); \
print('✅ Synced!' if synced else '❌ Failed')"

# Test OAuth token validity
python scripts/check_youtube_token.py

# Test duplicate book folder cleanup
python scripts\test_duplicate_folder_cleanup.py
```

## Dependencies & Versions

**Critical**:
- `google-generativeai>=0.3.0` - Gemini AI
- `playwright` - Must run `playwright install chromium` post-install
- `yt-dlp>=2023.10.13` - YouTube downloads
- `absl-py>=1.0.0` - Recently added (was missing)

**Arabic Support**:
- `arabic-reshaper` + `python-bidi` - Required for CLI display

## Entry Points

1. **User**: `main.py` → `src.presentation.cli.run_menu:main()`
2. **Batch Scripts**: `run.bat` (Windows) - Handles venv activation
3. **Direct Module**: `python -m src.infrastructure.adapters.<adapter>`

## Recent Changes (Session Context)

1. **Empty Folder Cleanup Fix** (v2.2.2): Duplicate books no longer leave empty `runs/` folders
2. **Database NoneType Fix** (v2.2.1): Fixed `'NoneType' object has no attribute 'strip'` errors in 7 database functions
3. **YouTube Sync System** (v2.1.0): Auto-syncs `database.json` from channel to prevent duplicates
4. **Batch Processing** (v2.0.0): Process multiple books from `books.txt` with `--auto-continue` flag
5. **Font Profile System** (v2.2.0): Multi-font support with independent sizing dynamics
6. **Cleaned `process.py`**: Removed 5 duplicate/old functions (24 → 19 functions)
7. **Fixed search filter**: Max video length 120min → 90min (Line 194)
8. **Fixed preflight cookies check**: `parents[2]` → `parents[3]` (Line 344)
9. **Book cover fetching**: Added Google Books API as primary method (fast), Amazon as fallback
10. **Added `absl-py`**: Was missing from requirements.txt, caused import errors
11. **TTS script cleaning**: Removes prompt markers like `**[HOOK]**` before TTS generation

## Git Workflow

**Main Branch**: `master` (default branch should be `main` - consider renaming)
**Recent Commits**:
- "Clean up process.py: Remove duplicate and old unused functions, keep only Amazon book cover scraper"
- "Remove sensitive files and large media from git tracking"

**.gitignore Rules**:
- `secrets/` - All API keys
- `runs/` - Generated videos/audio
- `*.mp3`, `*.mp4` - Media files
- `cookies.txt` - Session cookies

## Quick Reference

**Common Commands**:
```bash
run.bat                          # Interactive menu (Windows)
python main.py                   # Interactive menu (cross-platform)
python -m src.infrastructure.adapters.process "path/to/run"  # Reprocess text
```

**Key Files to Edit**:
- Search filters: `src/infrastructure/adapters/search.py:194`
- Gemini prompts: `config/prompts.json`
- Model config: `config/settings.json`
- Cover scraping: `src/infrastructure/adapters/process.py:220`
- Font profiles: `config/settings.json` → `thumbnail_font_profiles`

**Log Locations**:
- Pipeline: `runs/<timestamp>_<book>/pipeline.log`
- Preflight: `runs/<timestamp>/preflight.log`

**Batch Processing**:
- Input file: `books.txt` in repo root (one book title per line, Arabic or English)
- Command: `python main.py` → Option 2 (or use `--batch books.txt`)
- Auto-continue mode: `--auto-continue` flag (no prompts, perfect for overnight runs)
- Exit codes: 0=success, 1=critical error, 130=interrupted
- Duplicate check: Auto-syncs from YouTube channel before processing
- See `docs/AUTO_CONTINUE_MODE.md` for unattended processing guide

**Recent Additions**:
- Empty Folder Cleanup (v2.2.2): Auto-deletes empty run folders for duplicate books
  - Test: `python scripts\test_duplicate_folder_cleanup.py`
  - Fix: Reversed duplicate check order + auto-cleanup
- Database NoneType Fix (v2.2.1): Defensive None checks in 7 database functions
  - Documentation: `docs/DATABASE_NONETYPE_FIX.md`
  - Test: `python scripts\test_db_none_fix.py`
- Font profile system (v2.2.0): Multiple fonts with independent sizing dynamics
  - Documentation: `docs/FONT_PROFILE_SYSTEM.md`
  - Test: `python test_font_profiles.py`
- YouTube Sync (v2.1.0): Cross-environment duplicate detection
  - Documentation: `docs/DUPLICATE_CHECK_SYSTEM.md`
  - Config: `config/settings.json` → `youtube_sync`

**Recent Updates (v2.2.9 - 2025-10-26):**
- Thumbnail quality maximized: quality=100, dpi=300 for sharpest possible output
- Book cover design: Replaced double border with elegant soft shadow (Netflix/Audible style)
- Main title shadow: Added soft 4px shadow for depth and professionalism
- Encrypted secrets: Latest OAuth token (6+ months) and API keys committed to GitHub
- Ready for multi-device deployment with `decrypt_secrets.py`

---

**Last Updated**: 2025-10-26 (Quality & design improvements + encrypted secrets update)
