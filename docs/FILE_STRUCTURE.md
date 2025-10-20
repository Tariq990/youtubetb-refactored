# 📂 Project File Structure - Quick Reference

## 🎯 User-Facing Files

### Main Entry Points
- **`main.py`** - Interactive menu (main entry point)
- **`run.bat`** - Windows batch script to run the program
- **`setup.bat`** - Windows setup script (install dependencies)

### Configuration Files
- **`books.txt`** - 🆕 Your batch processing books list
- **`books_examples.txt`** - 🆕 100+ example books for reference
- **`.env`** - API keys and secrets (create from `.env.example`)

### Documentation
- **`README.md`** - Main project documentation (Arabic + English)
- **`BATCH_QUICK_START.md`** - 🆕 Quick start guide for batch processing
- **`docs/QUICK_START.md`** - General quick start guide
- **`docs/CHANGELOG.md`** - 🆕 Version history (now includes v2.1.0)
- **`docs/user-guide/BATCH_PROCESSING.md`** - 🆕 Comprehensive batch processing guide (500+ lines)

### Testing
- **`test_batch.py`** - 🆕 Test suite for batch processing system

---

## 🧑‍💻 Developer Files

### Core Architecture

#### Domain Layer (`src/core/domain/`)
- **`entities/`** - Business entities
- **`value_objects/`** - Value objects (immutable data)
- **`services/`** - Domain services (business logic)
- **`exceptions/`** - Custom exceptions

#### Application Layer (`src/application/`)
- **`use_cases/`** - Use case implementations
- **`dtos/`** - Data transfer objects
- **`services/`** - Application services

#### Infrastructure Layer (`src/infrastructure/`)
- **`adapters/`** - External service integrations
  - `search.py` - YouTube video search
  - `transcribe.py` - Video transcription
  - `process.py` - AI text processing (Gemini)
  - `tts.py` - Text-to-speech (OpenAI.fm)
  - `render.py` - Video rendering (FFmpeg)
  - `youtube_upload.py` - YouTube upload
  - `shorts_generator.py` - Short video generation
  - `thumbnail.py` - Thumbnail generation
  - `database.py` - Database operations
  - 🆕 Enhanced for batch processing integration

#### Presentation Layer (`src/presentation/cli/`)
- **`run_menu.py`** - Interactive CLI menu
- **`run_pipeline.py`** - Main pipeline orchestration
- **`run_batch.py`** - 🆕 Intelligent batch processing (726 lines, completely rewritten)
- **`check_apis.py`** - API validation
- **`generate_short.py`** - Short generation
- Other CLI utilities

---

## 🗂️ Data & Config

### Configuration (`config/`)
- **`prompts.json`** - AI prompts (clean, translate, script)
- **`settings.json`** - Application settings
- **`template.html`** - Metadata template

### Secrets (`secrets/`)
- **`api_key.txt`** - Gemini API key
- **`cookies.txt`** - YouTube cookies (for age-restricted videos)
- **`client_secret.json`** - YouTube OAuth credentials
- **`token.json`** - YouTube OAuth token (auto-generated)

### Database
- **`database.json`** - 🆕 Book tracking database (status, URLs, folders)
  - Format: `{"books": [{"main_title": "...", "status": "done|processing", ...}]}`

### Runs (`runs/`)
- **`<timestamp>_<book>/`** - Each run's output folder
  - `summary.json` - 🆕 Stage completion tracking (for resume functionality)
  - `search.results.json` - Search results
  - `search.chosen.json` - Chosen video
  - `transcribe.txt` - Extracted transcript
  - `translate.txt` - Translated text
  - `script.txt` - Final script
  - `timestamps.json` - Word-level timestamps
  - `output.titles.json` - Video metadata
  - `captions_highlight.ass` - Subtitle file
  - `thumbnail.jpg` - Generated thumbnail
  - `final_video.mp4` - Rendered video
  - `short_*.json` - Short video metadata
  - `pipeline.log` - Processing logs

- **`latest/path.txt`** - Path to most recent run

---

## 📖 Documentation Structure

### User Guides (`docs/user-guide/`)
- **`BATCH_PROCESSING.md`** - 🆕 **NEW!** Complete batch processing guide
  - Usage examples
  - Book file format
  - How it works (3 steps)
  - Advanced scenarios
  - Troubleshooting
  - Best practices

### Developer Guides (`docs/developer/`)
- **`BATCH_PROCESSING_TECHNICAL.md`** - 🆕 **NEW!** Technical deep-dive
  - Architecture (database + resume + batch integration)
  - Intelligent decision logic
  - Data flow diagrams
  - Error handling
  - Performance considerations
  - API reference
  - Testing strategy
  - Future enhancements

### API Documentation (`docs/api/`)
- API specifications and references

### Architecture (`docs/architecture/`)
- System architecture diagrams and explanations

---

## 🆕 New Files (v2.1.0)

### Batch Processing Enhancement

1. **`books.txt`** - User's batch processing input file
   - Format: `Book Title | Author Name`
   - Supports comments (#) and empty lines
   
2. **`books_examples.txt`** - Example library (100+ books)
   - Organized by category
   - Arabic and English books
   - Testing scenarios
   
3. **`BATCH_QUICK_START.md`** - Quick reference guide
   - Basic usage
   - Examples
   - Quick reference card
   
4. **`docs/user-guide/BATCH_PROCESSING.md`** - Comprehensive guide (500+ lines)
   - All scenarios covered
   - Detailed troubleshooting
   - Performance tips
   
5. **`docs/developer/BATCH_PROCESSING_TECHNICAL.md`** - Technical documentation
   - Architecture diagrams
   - Code examples
   - Testing strategies
   
6. **`test_batch.py`** - Test suite
   - Database matching tests
   - Status detection tests
   - Parsing tests
   
7. **`src/presentation/cli/run_batch.py`** - COMPLETELY REWRITTEN (260 → 726 lines)
   - Intelligent batch processing
   - Pre-flight analysis
   - Beautiful Rich UI
   - Comprehensive error handling

---

## 🔄 Modified Files (v2.1.0)

1. **`README.md`** - Updated with batch processing section
   - New feature highlight
   - Usage examples
   - Documentation links
   
2. **`docs/CHANGELOG.md`** - Added v2.1.0 entry
   - Complete feature list
   - Technical details
   - Breaking changes (none)
   
3. **`.github/copilot-instructions.md`** - Updated architecture notes
   - Batch processing integration
   - Decision logic
   - Database usage

---

## 📊 File Statistics

### Code Lines
- **Total Python Files**: ~50 files
- **Total Lines of Code**: ~15,000 lines
- **New in v2.1.0**: ~2,000 lines (batch processing + docs)

### Documentation
- **Total Docs**: ~20 files
- **Total Doc Lines**: ~3,000 lines
- **New in v2.1.0**: ~1,200 lines

### Test Coverage
- **Unit Tests**: In development
- **Integration Tests**: In development
- **Manual Tests**: `test_batch.py` (functional)

---

## 🗺️ File Navigation Guide

### I want to...

#### **Process a single book**
→ `python main.py` (Option 1)
→ Or: `python -m src.presentation.cli.run_pipeline "Book Title"`

#### **Process multiple books automatically** 🆕
→ Edit `books.txt`
→ `python -m src.presentation.cli.run_batch`
→ See: `BATCH_QUICK_START.md`

#### **Check API keys**
→ `python -m src.presentation.cli.check_apis`

#### **Configure settings**
→ Edit `config/settings.json`
→ Edit `config/prompts.json` (AI prompts)

#### **View batch processing docs** 🆕
→ User: `BATCH_QUICK_START.md` or `docs/user-guide/BATCH_PROCESSING.md`
→ Developer: `docs/developer/BATCH_PROCESSING_TECHNICAL.md`

#### **Test batch system** 🆕
→ `python test_batch.py`

#### **See example books** 🆕
→ `books_examples.txt` (100+ examples)

#### **Check database**
→ `database.json` (JSON format)

#### **View run logs**
→ `runs/<timestamp>_<book>/pipeline.log`

#### **Track completed stages** 🆕
→ `runs/<timestamp>_<book>/summary.json`

#### **Understand architecture**
→ `docs/architecture/` directory
→ `.github/copilot-instructions.md`

---

## 🎯 Quick Access

### Most Important Files

| File | Purpose | Who |
|------|---------|-----|
| `main.py` | Main entry point | Users |
| `books.txt` 🆕 | Batch books list | Users |
| `BATCH_QUICK_START.md` 🆕 | Quick guide | Users |
| `run_batch.py` 🆕 | Batch processor | Devs |
| `database.json` | Book tracking | Both |
| `config/settings.json` | Settings | Both |
| `README.md` | Main docs | Both |

### Configuration Priority

1. **Secrets** (highest priority): `secrets/` folder
2. **Root files**: `.env`, `database.json`
3. **Config folder**: `config/settings.json`, `config/prompts.json`

### Log Files

1. **Pipeline logs**: `runs/<timestamp>/pipeline.log`
2. **Application logs**: `logs/` directory (if configured)
3. **Error logs**: Separate error log file (if configured)

---

**Last Updated:** 2025-10-19  
**Version:** 2.1.0  
**Total Files:** ~100 (including docs, tests, and outputs)
