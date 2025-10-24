# YouTubeTB - AI Agent Instructions

## Project Overview
**YouTubeTB** is an automated YouTube book summary video generator. It transforms Arabic book summaries from YouTube into polished English videos with AI-enhanced narration, visual effects, and automatic upload.

**Core Flow**: Search YouTube → Transcribe → AI Process (clean/translate/scriptify) → TTS → Render → Upload → Generate Shorts

## Architecture

### Layered Structure (Hexagonal Architecture)
```
src/
├── presentation/cli/          # User interface (Typer CLI, run_menu.py)
├── application/              # Use cases (currently minimal)
├── infrastructure/adapters/  # External service integrations
│   ├── search.py            # YouTube Data API (15-90 min filter)
│   ├── transcribe.py        # yt-dlp + youtube-transcript-api
│   ├── process.py           # Gemini AI (clean/translate/script)
│   ├── tts.py              # OpenAI.fm scraper (Playwright)
│   ├── render.py           # FFmpeg video composition
│   ├── youtube_upload.py   # OAuth + YouTube API v3
│   └── shorts_generator.py # Short-form content creation
├── core/domain/             # Business entities (exceptions mainly)
└── shared/                  # Cross-cutting (logging, errors)
```

**Key Principle**: Adapters are independent. Each can run standalone via `main()` for testing.

### Critical Paths
- **repo_root**: Always `Path(__file__).resolve().parents[N]` where N varies by file depth
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
- Voice: "Shimmer" (hardcoded)
- Retries: 10 attempts per chunk with exponential backoff
- **Legacy**: Mutagen timestamp extraction often fails → falls back to `ffprobe`

### 4. Render (`render.py`)
**FFmpeg Pipeline**:
1. Parse `timestamps.json` (Whisper word-level alignment)
2. Create timed subtitle overlays (`drawtext` filters)
3. Composite: background gradient + book cover + animated text
4. Output: 1920x1080, 30fps, CRF 23

**Key Files**:
- `config/template.html` - Not used in render, only for metadata
- `assets/fonts/` - Custom fonts for text rendering

### 5. Pipeline Orchestration (`run_pipeline.py`)
**Stage Management**:
- Saves `summary.json` after EVERY stage completion
- Resume capability: `--resume` flag reads last successful stage
- Retry logic: Max 10 attempts per stage with exponential backoff

**Preflight Checks** (Line 344, `_preflight_check`):
```python
repo_root = Path(__file__).resolve().parents[3]  # CRITICAL: Must be 3, not 2!
```
- Validates: Internet, FFmpeg, yt-dlp, Playwright, cookies, API keys
- Fixed Bug: Was using `parents[2]` → couldn't find `secrets/cookies.txt`

## Configuration

### `config/prompts.json`
- **Immutable Templates**: `clean_template`, `translate_template`, `youtube_script_template`
- **Key Instruction**: Line 24: `"Do NOT add, omit, or summarize."` (often ignored due to Gemini limits)

### `config/settings.json` (Dynamic)
- `gemini_model`: Model selection (default: `gemini-2.5-flash-latest`)
- `prefer_local_cover`: Download cover locally vs. use URL
- `cover_source`: Legacy field (now always Amazon)
- `thumbnail_font_profiles`: **NEW!** Font-specific sizing dynamics (Bebas Neue, Cairo)
  - Each font has independent base_size, min/max bounds, scaling factors
  - See `docs/FONT_PROFILE_SYSTEM.md` for complete guide

## Developer Workflows

### Run Full Pipeline
```bash
python main.py  # Interactive menu
# Option 1 → Enter book title (Arabic)
```

### Test Individual Stages
```python
# Each adapter has standalone main()
python -m src.infrastructure.adapters.search "العادات الذرية"
python -m src.infrastructure.adapters.transcribe --url "https://youtube.com/watch?v=..."
```

### Resume Failed Run
```bash
python main.py
# Option 13 → Auto-detects last run and resumes
```

### Debugging Process Issues
```python
# Check transcript size
words = len(open("runs/.../transcribe.txt").read().split())
# If >15k words → expect translation truncation

# Verify model config
import json
cfg = json.load(open("config/settings.json"))
print(cfg.get("gemini_model"))  # Should be gemini-2.5-flash-latest
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

## Testing Strategy

**No formal test suite** - Validation via:
1. `run_menu.py` → Option 0: Comprehensive API/tool validation
2. Stage isolation: Each adapter's `main()` function
3. Real-world runs: Check `runs/*/pipeline.log` for errors

**Example Manual Test**:
```bash
# Test search filter changes
python -m src.infrastructure.adapters.search "الأب الغني والأب الفقير"
# Verify: Only videos 15-90 min accepted

# Test Amazon scraper
python -c "from src.infrastructure.adapters.process import _get_book_cover_from_amazon; \
print(_get_book_cover_from_amazon('Atomic Habits', 'James Clear'))"
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

1. **Cleaned `process.py`**: Removed 5 duplicate/old functions (24 → 19 functions)
2. **Fixed search filter**: Max video length 120min → 90min (Line 194)
3. **Fixed preflight cookies check**: `parents[2]` → `parents[3]` (Line 344)
4. **Book cover fetching**: Added Google Books API as primary method (fast), Amazon as fallback
5. **Added `absl-py`**: Was missing from requirements.txt, caused import errors

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

**Recent Additions**:
- Font profile system (v2.2.0): Multiple fonts with independent sizing dynamics
  - Documentation: `docs/FONT_PROFILE_SYSTEM.md`
  - Test: `python test_font_profiles.py`

---

**Last Updated**: 2025-10-24 (Added font profile system for multi-font support)
