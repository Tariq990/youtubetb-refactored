# YouTubeTB - Quick Reference for AI Agent

## 🎯 What This Does
Automated YouTube book summary video generator: Arabic YouTube → English videos with AI narration.

## 🚀 Pipeline (11 Stages)
1. **Search** → YouTube API (15-90 min videos)
2. **Transcribe** → yt-dlp extract Arabic text
3. **Process** → Gemini AI (clean/translate/script)
4. **TTS** → OpenAI.fm audio (Playwright scraping)
5. **Render** → FFmpeg video + subtitles
6. **YouTube Metadata** → AI title/description
7. **Merge** → Combine video+audio
8. **Thumbnail** → PIL 1920x1080 (8 pro colors)
9. **Upload** → YouTube OAuth
10. **Shorts** → 9:16 vertical 60s video
11. **Short Upload** → Shorts to YouTube

## 📂 Key Files (Quick Access)
```
src/infrastructure/adapters/
├── search.py          # YouTube search (15-90 min filter)
├── transcribe.py      # Extract text
├── process.py         # AI translation (Gemini)
├── tts.py            # OpenAI.fm TTS (ffprobe only, no Mutagen)
├── render.py         # Video creation
├── youtube_metadata.py # SEO title/description
├── merge_av.py       # Final MP4
├── thumbnail.py      # 8-color smart palette
├── youtube_upload.py # OAuth upload
├── shorts_generator.py # Vertical shorts
└── database.py       # Duplicate detection + YouTube sync

src/presentation/cli/
└── run_pipeline.py   # Main orchestrator (duplicate check FIRST)
```

## ⚡ Critical Code Patterns

### repo_root Calculation
```python
# ALWAYS use correct depth:
repo_root = Path(__file__).resolve().parents[3]  # For run_pipeline.py
repo_root = Path(__file__).resolve().parents[2]  # For adapters/
```

### Duplicate Detection (FIXED v2.2.2)
```python
# CORRECT ORDER (check BEFORE add):
existing = check_book_exists(book_name, author_name)
if existing and status == 'uploaded':
    shutil.rmtree(d["root"])  # Delete empty folder
    return  # Stop
if not existing:
    add_book(...)  # Only add if NEW
```

### Database NoneType Protection (FIXED v2.2.1)
```python
# ALWAYS check None before .strip():
db_title = book.get("main_title")
if not db_title:
    continue
title_match = str(db_title).strip().lower() == book_lower
```

### TTS Duration (FIXED v2.2.3)
```python
# Use ffprobe ONLY (no Mutagen):
result = subprocess.run(["ffprobe", "-v", "error", ...])
duration = float(result.stdout.strip())
# Silent success - no spam logs
```

### Thumbnail Subtitle Colors (FIXED v2.2.4)
```python
PROFESSIONAL_SUBTITLE_COLORS = [
    (255, 215, 0),    # Gold
    (255, 140, 0),    # Dark Orange
    (255, 69, 0),     # Red-Orange
    (50, 205, 50),    # Lime Green
    (0, 191, 255),    # Deep Sky Blue
    (147, 112, 219),  # Medium Purple
    (255, 20, 147),   # Deep Pink
    (255, 255, 100),  # Bright Yellow
]
# Pick best contrast with background automatically
```

## 🔧 Common Commands
```bash
# Run pipeline
python main.py  # Interactive menu

# Batch processing
python main.py  # Option 2 (books.txt with 20+ books)

# Resume failed run
python main.py  # Option 13

# Test individual stage
python -m src.infrastructure.adapters.search "العادات الذرية"
python -m src.infrastructure.adapters.thumbnail --run "runs/latest" --debug

# Database sync from YouTube
python -c "from src.infrastructure.adapters.database import sync_database_from_youtube; sync_database_from_youtube()"
```

## 🐛 Recent Fixes (v2.2.x)

### v2.2.4 (2025-10-24)
- **Thumbnail colors**: 8 professional colors with auto-contrast selection
- **TTS logs**: Removed Mutagen spam (use ffprobe only)

### v2.2.3 (2025-10-24)
- **TTS performance**: Removed Mutagen completely (ffprobe direct)
- **Silent operation**: No more "⚠️ Mutagen failed" warnings

### v2.2.2 (2025-10-24)
- **Empty folders**: Auto-delete when duplicate detected
- **Duplicate check**: Reversed order (check BEFORE add)
- **Clean runs/**: No empty timestamp folders

### v2.2.1 (2025-10-24)
- **Database NoneType**: Fixed 7 functions with defensive None checks
- **Graceful handling**: Skip None entries instead of crash

## 📋 books.txt Format
```
العادات الذرية
الأب الغني والأب الفقير
فن اللامبالاة
...
```
- One book per line
- Arabic or English
- 20 books currently (mixed categories)

## 🗂️ File Structure
```
runs/YYYY-MM-DD_HH-MM-SS_Book-Name/
├── summary.json         # Pipeline state
├── transcribe.txt       # Arabic source
├── cleaned.txt          # AI cleaned
├── translated.txt       # English
├── script.txt           # Narration script
├── narration.mp3        # Final audio
├── video_snap.mp4       # Silent video
├── output.titles.json   # YouTube metadata
├── thumbnail.jpg        # 1920x1080
├── bookcover.jpg        # From Google Books/Amazon
├── [YouTube Title].mp4  # Final upload
├── short_video.mp4      # Vertical short
└── pipeline.log         # Full logs
```

## 🔑 Secrets Structure
```
secrets/
├── api_key.txt          # Gemini API
├── api_keys.txt         # YouTube Data API
├── client_secret.json   # OAuth credentials
├── token.json           # OAuth token (auto-refresh)
└── cookies.txt          # YouTube cookies (age-restricted)
```

## 🎨 Config Files
```
config/
├── prompts.json         # AI prompts (clean/translate/script)
├── settings.json        # Model, fonts, YouTube sync
└── template.html        # Metadata template
```

### settings.json Quick Ref
```json
{
  "gemini_model": "gemini-2.5-flash-latest",
  "thumbnail_font": "Bebas Neue",
  "youtube_sync": {
    "enabled": true,
    "channel_id": "UCQyOYMG7mH7kwM5O5kMF6tQ"
  }
}
```

## ⚠️ Known Issues
1. **Long videos (>90 min)**: Gemini truncates → Use filter in search.py
2. **Cookies required**: Age-restricted videos need `cookies.txt`
3. **ffprobe required**: Critical for TTS timestamps
4. **Playwright setup**: Run `playwright install chromium`

## 🧪 Testing
```bash
# Database tests
python scripts\test_db_none_fix.py
python scripts\test_duplicate_folder_cleanup.py

# Font profiles
python test_font_profiles.py

# YouTube sync
python scripts/test_sync.py
```

## 📊 Database Schema
```json
{
  "books": [
    {
      "main_title": "Book Name",
      "author_name": "Author",
      "status": "processing|uploaded|done",
      "youtube_url": "https://youtube.com/watch?v=...",
      "youtube_short_url": "https://youtube.com/watch?v=...",
      "run_folder": "2025-10-24_XX-XX-XX_Book-Name",
      "date_added": "2025-10-24T18:00:00"
    }
  ]
}
```

## 🎯 AI Agent Guidelines

### When User Reports Error
1. **Check latest logs**: `runs/latest/pipeline.log`
2. **Check summary.json**: See which stage failed
3. **Run stage standalone**: `python -m src.infrastructure.adapters.STAGE`
4. **Check database.json**: For duplicate/NoneType issues

### When User Wants New Feature
1. **Identify stage**: Which adapter needs modification?
2. **Check existing patterns**: Follow defensive coding (None checks)
3. **Test standalone**: Run adapter's `main()` before integration
4. **Update this file**: Add to Recent Fixes section

### When User Asks "Why?"
1. **Search this file first**: Use Ctrl+F
2. **Check Recent Fixes**: Likely documented
3. **Read code comments**: Adapters have inline docs
4. **Check docs/**: Detailed documentation exists

---

**Last Updated**: 2025-10-24 (Optimized for AI agent speed)
  - `process.py`: `parents[2]` (src/infrastructure/adapters → root)
  - `run_pipeline.py`: `parents[3]` (src/presentation/cli → root)
- **Secrets**: Prioritize `secrets/` folder over root (e.g., `secrets/api_key.txt` > `api_key.txt`)
- **Cookies**: Search order: `secrets/cookies.txt` → `cookies.txt` (required for age-restricted videos)

## Core Components

### 1. Search (`search.py`)
**Purpose**: Find optimal book summary videos on YouTube.

**Filters** (Lines 194-199):
```python
if total_seconds < 900 or total_seconds > 5400:  # 15-90 min
    excluded_count += 1
    continue
```
- Excludes: <15 min (too short), >90 min (causes Gemini truncation)
- **Why 90 min max**: Longer videos → 18k+ words → Gemini output limits → severe content loss

**Dual-Phase Search**:
1. Relevance-based (15 results) - popular videos
2. Date-based (10 results) - recent uploads
3. Sorts by duration (longest first) after filtering

### 2. Process (`process.py`) - THE BOTTLENECK
**Three Gemini Calls**:
1. `_clean_source_text()` - Remove intro/outro, keep book content only
2. `_translate_to_english()` - Arabic → English (preserves ALL details)
3. `_scriptify_youtube()` - Reformat for YouTube narration

**Model**: `gemini-2.5-flash-latest` (configurable via `config/settings.json` → `gemini_model`)

**Critical Issue**: No text chunking! Large transcripts (18k words) exceed output limits.
- Result: Gemini auto-summarizes despite "DO NOT SUMMARIZE" prompt
- Example: 18,981 word input → 2,046 word translation (89% loss!)

**Book Cover Fetching** (`_get_book_cover_from_amazon`, Line 220):
- **Primary Method**: Google Books API (fast, reliable, no scraping)
- **Fallback Methods**: Amazon.com scraping (English titles only) with Playwright, then requests
- **Why Google Books First**: Much faster than browser automation, reliable API
- **Amazon Scoring Algorithm** (if used):
  ```python
  position_score = (5 - idx) * 10  # First result = 50 points
  rating_score = rating * 10        # 4.7 stars = 47 points
  review_score = min(reviews/100, 10)  # Capped at 10
  total = position + rating + review
  ```
- **Old Methods Removed**: `_get_cover_goodreads`, `_get_cover_openlibrary`, `_get_cover_googlebooks` (replaced with API)

### 3. TTS (`tts.py`)
**Service**: OpenAI.fm (free TTS via Playwright scraping)
- Chunks text into ≤950 char segments (CSV-based)
- Voice: "Shimmer" (hardcoded, configurable via `DEFAULT_VOICE`)
- Retries: 10 attempts per chunk with exponential backoff
- **Script cleaning** (`_clean_script_markers`, Line 55): Removes prompt structure markers like `**[HOOK]**`, `**[CONTEXT]**` before TTS
- **Legacy**: Mutagen timestamp extraction often fails → falls back to `ffprobe`
- **Whisper alignment**: Optional word-level timestamps via `whisper` (if installed)

### 4. Render (`render.py`)
**FFmpeg Pipeline**:
1. Parse `timestamps.json` (Whisper word-level alignment)
2. Create timed subtitle overlays (`drawtext` filters)
3. Composite: background gradient + book cover + animated text
4. Output: 1920x1080, 30fps, CRF 23

**Key Files**:
- `config/template.html` - Not used in render, only for metadata
- `assets/fonts/` - Custom fonts for text rendering

### 5. YouTube Metadata (`youtube_metadata.py`)
**Purpose**: Generate SEO-optimized YouTube video metadata using Gemini AI.

**What it generates**:
- **YouTube Title**: Catchy, clickable title (max 100 chars)
  - Pattern: `"[Hook] – [Book Name] | Book Summary"`
  - Example: `"Master Your Mind – Atomic Habits | Book Summary"`
- **YouTube Description**: Full description with timestamps, chapters, links
  - Includes: Book intro, key concepts, author info, timestamps
  - Adds: Channel link, playlist links, call-to-action
- **Thumbnail Hooks**: Short punchy text for thumbnail overlay
  - `thumbnail_title`: Main hook (5-6 words max)
  - `thumbnail_subtitle`: Supporting text (author or key benefit)
- **Tags**: Relevant YouTube tags for SEO

**Gemini Prompts** (from `config/prompts.json`):
- `youtube_title_template` - Title generation prompt
- `youtube_description_template` - Description generation prompt
- `thumbnail_hook_template` - Thumbnail text prompt

**Output File**: `output.titles.json` with all metadata fields

**Model Config**:
- Uses same Gemini model as Process stage (configurable in `settings.json`)
- Fallback to `gemini-2.5-flash` if specified model fails

### 6. Merge (`merge_av.py`)
**Purpose**: Combine video and audio into final uploadable MP4.

**Input Files**:
- `video_snap.mp4` - Silent video from Render stage (1920x1080)
- `narration.mp3` - Audio from TTS stage
- `output.titles.json` - YouTube title for filename

**Process**:
1. Read YouTube title from `output.titles.json`
2. Sanitize title for filename (remove special chars, limit length)
3. Run FFmpeg merge:
   ```bash
   ffmpeg -i video_snap.mp4 -i narration.mp3 \
          -c:v copy -c:a aac -b:a 192k \
          -shortest "[YouTube Title].mp4"
   ```
4. Delete old output if re-running (Unicode normalization handling)

**Output**: `[YouTube Title].mp4` ready for upload

**Smart Filename Handling**:
- Handles Unicode issues (em dash → spaces)
- Truncates to 120 chars max
- Fuzzy matching to delete old versions

### 7. Thumbnail (`thumbnail.py`)
**Purpose**: Generate professional 16:9 thumbnail with dynamic text sizing.

**Multi-Font System** (v2.2.0):
Three font profiles with independent sizing dynamics:

1. **Bebas Neue** (Default - Bold Display):
   - Base size: 100px
   - Range: 60-140px
   - Best for: Short punchy hooks (3-5 words)
   - Scaling: Aggressive reduction for long text

2. **Cairo** (Arabic-friendly):
   - Base size: 85px
   - Range: 50-120px
   - Best for: Mixed language titles
   - Scaling: Moderate, balanced

3. **Impact** (Heavy Bold):
   - Base size: 95px
   - Range: 55-130px
   - Best for: Strong statements
   - Scaling: Similar to Bebas but slightly smaller

**Dynamic Sizing Algorithm**:
```python
# Word count based adjustment
if words <= 3: size = base_size
elif words <= 5: size = base_size * 0.9
elif words <= 7: size = base_size * 0.75
else: size = base_size * 0.6

# Enforce min/max bounds
size = max(min_size, min(size, max_size))
```

**Thumbnail Elements**:
1. **Background**: Gradient or solid color
2. **Book Cover**: Positioned and scaled
3. **Main Title**: `thumbnail_title` (large, bold)
4. **Subtitle**: `thumbnail_subtitle` (smaller, under title)
5. **Effects**: Drop shadow, outline for readability

**Input**: `output.titles.json` (needs `thumbnail_title` and `thumbnail_subtitle`)
**Output**: `thumbnail.jpg` (1280x720, 16:9)

**Fallback System**:
- If `thumbnail_title` missing → use `main_title` or `youtube_title`
- If `thumbnail_subtitle` missing → use `author_name` or `"Book Summary"`
- If font not found → graceful degradation to system font

**Font Loading Priority**:
1. `assets/fonts/[FontName].ttf`
2. System fonts (Windows: `C:\Windows\Fonts\`)
3. Fallback to PIL default

### 8. Pipeline Orchestration (`run_pipeline.py`)
**Stage Management**:
- Saves `summary.json` after EVERY stage completion
- Resume capability: `--resume` flag reads last successful stage
- Retry logic: Max 10 attempts per stage with exponential backoff
- **Dual-check validation**: Stage marked complete ONLY if `summary.json` says "ok" AND artifact file exists

**Critical Resume Logic** (`_should_retry_stage`, Line 240):
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

---

**Last Updated**: 2025-10-24 (Added empty folder cleanup fix for duplicate books)
