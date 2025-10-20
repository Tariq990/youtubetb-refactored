# 🧠 Intelligent Batch Processing - Technical Documentation

## Architecture Overview

The intelligent batch processing system is built on top of the existing pipeline infrastructure with three key integrations:

### 1. Database Integration (`database.json`)
- **Purpose**: Track book completion status across runs
- **Schema**:
```json
{
  "books": [
    {
      "main_title": "Atomic Habits",
      "author_name": "James Clear",
      "status": "done",  // "done" | "processing" | null
      "youtube_url": "https://youtube.com/watch?v=...",
      "short_url": "https://youtube.com/shorts/...",
      "date_added": "2025-10-19T10:30:00",
      "run_folder": "2025-10-19_10-30-00_Atomic-Habits"
    }
  ]
}
```

### 2. Resume System (`summary.json`)
- **Purpose**: Track stage completion within each run
- **Location**: `runs/<timestamp>_<book>/summary.json`
- **Schema**:
```json
{
  "search": "success",
  "transcribe": "success",
  "process": "success",
  "tts": "failed",
  "render": null,
  "upload": null,
  "shorts": null
}
```

### 3. Batch Processor (`run_batch.py`)
- **Purpose**: Orchestrate multi-book processing with intelligent decisions
- **Components**:
  - `check_book_status()`: Analyze each book's database state
  - `print_book_status_table()`: Display pre-flight plan
  - `process_books_batch()`: Execute intelligent processing
  - `print_final_summary()`: Show results with statistics

---

## Intelligent Decision Logic

```python
def decide_action(book_name, author_name):
    """
    Determine what action to take for a book.
    
    Returns:
        - "skip": Book already completed (status="done")
        - "resume": Book incomplete (status="processing")
        - "process": Book not in database (new)
    """
    book_info = check_book_exists(book_name, author_name)
    
    if not book_info:
        return "process"  # New book
    
    status = book_info.get("status")
    
    if status == "done":
        return "skip"  # Already completed
    elif status == "processing":
        return "resume"  # Incomplete
    else:
        return "process"  # Unknown status (treat as new)
```

### Action Handlers

#### 1. Skip Action
```python
if action == "skip" and skip_completed:
    print(f"⏭️  SKIPPED: {title}")
    print(f"   YouTube: {book_info['youtube_url']}")
    
    results["skipped"].append({
        "book": title,
        "author": author,
        "reason": "Already completed",
        "youtube_url": book_info.get("youtube_url"),
        "short_url": book_info.get("short_url")
    })
    continue  # Don't process
```

#### 2. Resume Action
```python
elif action == "resume":
    print(f"♻️  RESUMING: {title}")
    
    # Pipeline will automatically detect old folder via output.titles.json
    # and resume from last successful stage (using summary.json)
    result = subprocess.run([
        python_exe,
        "-m", "src.presentation.cli.run_pipeline",
        book_line,  # "Title | Author"
        "--privacy", privacy
    ])
    
    if result.returncode == 0:
        results["resumed"].append({
            "book": title,
            "author": author,
            "youtube_url": "...",  # Retrieved from database after upload
        })
```

#### 3. Process Action
```python
else:  # action == "process"
    print(f"🚀 PROCESSING: {title}")
    
    # Fresh start - pipeline will create new folder
    result = subprocess.run([
        python_exe,
        "-m", "src.presentation.cli.run_pipeline",
        book_line,
        "--privacy", privacy
    ])
    
    if result.returncode == 0:
        results["success"].append({
            "book": title,
            "author": author,
            "youtube_url": "...",
        })
```

---

## Integration Points

### With `run_pipeline.py`

The batch processor calls `run_pipeline.py` as a subprocess:

```python
subprocess.run([
    sys.executable,
    "-m", "src.presentation.cli.run_pipeline",
    f"{title} | {author}" if author else title,
    "--privacy", privacy
])
```

`run_pipeline.py` performs these checks (Lines 573-643):

```python
# 1. Early metadata extraction
book_name, author_name = extract_metadata(book_input)

# 2. Database check
book_entry = check_book_exists(book_name, author_name)

# 3. Decision logic
if book_entry and book_entry.get("status") == "done":
    print("⏭️  Book already completed!")
    sys.exit(0)  # Exit without processing

elif book_entry and book_entry.get("status") == "processing":
    # Search for old folder
    old_folder = find_old_run_folder(book_name, author_name)
    
    if old_folder and (old_folder / "output.titles.json").exists():
        run_folder = old_folder
        print(f"♻️  Resuming from: {run_folder}")
        
        # Load summary.json to determine resume stage
        summary = load_summary(run_folder)
        resume_from_stage = get_last_failed_stage(summary)

# 4. Add to database if new
else:
    add_book(book_name, author_name)
    run_folder = create_new_folder(book_name, author_name)
```

### With `database.py`

The database adapter provides these functions:

```python
# 1. Check if book exists (case-insensitive)
book_info = check_book_exists(title, author)
# Returns: Dict or None

# 2. Add new book (prevents duplicates)
add_book(title, author)
# Sets status="processing", creates entry

# 3. Update after upload (marks complete)
update_youtube_url(title, author, youtube_url, short_url)
# Sets status="done", updates URLs
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User creates books.txt                                       │
│    Format: "Book Title | Author Name"                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. run_batch.py reads file                                      │
│    Parses lines, ignores comments (#) and empty lines           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Pre-flight Analysis (check_book_status)                      │
│    For each book:                                               │
│    - Call check_book_exists(title, author)                      │
│    - Get status: "done", "processing", or None                  │
│    - Determine action: "skip", "resume", or "process"           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Display Pre-flight Plan (print_book_status_table)            │
│    Rich table showing:                                          │
│    # | Book | Status | Action | Details                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. User Confirmation                                            │
│    Proceed with batch processing? [y/N]                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Intelligent Processing (process_books_batch)                 │
│    For each book in books_status:                               │
│                                                                  │
│    IF action == "skip" AND skip_completed:                      │
│       - Log skip reason                                         │
│       - Append to results["skipped"]                            │
│       - Continue to next book                                   │
│                                                                  │
│    ELIF action == "resume" OR action == "process":              │
│       - Call run_pipeline via subprocess                        │
│       - run_pipeline checks database internally                 │
│       - run_pipeline resumes from last stage if processing      │
│       - run_pipeline creates new folder if new                  │
│       - Wait for completion                                     │
│       - Check return code                                       │
│       - Append to results["success"/"resumed"/"failed"]         │
│                                                                  │
│    Delay 5 seconds between books                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Final Summary (print_final_summary)                          │
│    Rich table with counts + percentages:                        │
│    - Total Books                                                │
│    - ✅ Success (New)                                           │
│    - ♻️  Success (Resumed)                                      │
│    - ❌ Failed                                                  │
│    - ⏭️  Skipped                                                │
│                                                                  │
│    Detailed lists for each category                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Subprocess Errors

```python
try:
    result = subprocess.run(
        [python_exe, "-m", "src.presentation.cli.run_pipeline", book_line],
        timeout=3600  # 1 hour max per book
    )
    
    if result.returncode != 0:
        results["failed"].append({
            "book": title,
            "error": f"Exit code: {result.returncode}"
        })
        
except subprocess.TimeoutExpired:
    results["failed"].append({
        "book": title,
        "error": "Timeout (>1 hour)"
    })
    
except Exception as e:
    results["failed"].append({
        "book": title,
        "error": str(e)
    })
```

### User Interruption (Ctrl+C)

```python
try:
    for book_status in books_status:
        # Process book...
        
except KeyboardInterrupt:
    print("\n⚠️  INTERRUPTED by user")
    print(f"   Stopped at book {i}/{total}")
    
    # Mark remaining books as skipped
    for remaining in books_status[i:]:
        results["skipped"].append({
            "book": remaining["title"],
            "reason": "User interrupted batch"
        })
    
    # Still show summary of completed books
    print_final_summary(results)
```

---

## Performance Considerations

### Parallel Processing (Future)

Current implementation is **sequential** (one book at a time):

```python
for book in books:
    process_book(book)  # Blocks until complete
    time.sleep(5)       # Delay between books
```

**Potential Enhancement:** Parallel processing with worker pool:

```python
from concurrent.futures import ProcessPoolExecutor

def process_books_parallel(books, max_workers=3):
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_book, book): book
            for book in books
        }
        
        for future in as_completed(futures):
            book = futures[future]
            try:
                result = future.result()
                results["success"].append(result)
            except Exception as e:
                results["failed"].append({"book": book, "error": str(e)})
```

**Challenges:**
- FFmpeg/TTS resource contention
- API rate limits (YouTube, Gemini)
- Database locking (concurrent writes)

### Resource Management

Each book processing uses:
- **CPU**: High during render (FFmpeg)
- **RAM**: 2-4 GB peak
- **Disk**: ~500 MB temporary (cleaned after upload)
- **Network**: Moderate (API calls) + High (video upload)

**Recommendation:** Process 10-20 books per batch to avoid resource exhaustion.

---

## Testing Strategy

### Unit Tests (Future)

```python
# test_batch_processing.py

def test_check_book_status_new_book():
    """New book should return action='process'."""
    status = check_book_status("New Book", "New Author")
    assert status["action"] == "process"
    assert status["exists"] == False

def test_check_book_status_completed():
    """Completed book should return action='skip'."""
    # Add book to test database with status="done"
    add_book("Test Book", "Test Author")
    update_youtube_url("Test Book", "Test Author", "https://youtube.com/watch?v=test")
    
    status = check_book_status("Test Book", "Test Author")
    assert status["action"] == "skip"
    assert status["status"] == "done"

def test_check_book_status_incomplete():
    """Incomplete book should return action='resume'."""
    # Add book with status="processing"
    add_book("Incomplete Book", "Author")
    
    status = check_book_status("Incomplete Book", "Author")
    assert status["action"] == "resume"
    assert status["status"] == "processing"
```

### Integration Test

```bash
# Create test books file
cat > test_books.txt << EOF
Atomic Habits | James Clear
Deep Work | Cal Newport
The Alchemist
EOF

# Run batch processor
python -m src.presentation.cli.run_batch --file test_books.txt --privacy unlisted

# Verify results
- Check database.json for all books
- Verify status="done" for successful books
- Check runs/ directory for output folders
- Verify YouTube uploads
```

### Manual Testing Checklist

- [ ] Test with 0 books (empty file)
- [ ] Test with 1 book (new)
- [ ] Test with 1 book (already completed) - should skip
- [ ] Test with 1 book (incomplete) - should resume
- [ ] Test with mix of new/completed/incomplete
- [ ] Test with --no-skip flag
- [ ] Test with invalid book names (should fail gracefully)
- [ ] Test with Ctrl+C interruption (should show partial results)
- [ ] Test with books.txt containing comments and empty lines
- [ ] Test with books without authors

---

## Future Enhancements

### 1. Progress Tracking (Web Dashboard)

```python
# Real-time progress via WebSocket
@app.websocket("/ws/batch/{batch_id}")
async def batch_progress(websocket: WebSocket, batch_id: str):
    await websocket.accept()
    
    # Stream progress updates
    async for update in batch_processor.run(batch_id):
        await websocket.send_json({
            "book": update.book,
            "stage": update.stage,  # search, transcribe, etc.
            "progress": update.progress,  # 0-100
            "status": update.status  # running, success, failed
        })
```

### 2. Smart Scheduling

```python
# Schedule batch for off-peak hours
python -m src.presentation.cli.run_batch \
    --schedule "02:00"  # Run at 2 AM
    --notify email@example.com  # Send completion email
```

### 3. Cloud Integration

```python
# Offload processing to cloud workers
python -m src.presentation.cli.run_batch \
    --cloud aws  # Use AWS EC2 instances
    --workers 10  # 10 parallel workers
    --s3-bucket my-videos  # Upload to S3 first
```

### 4. Retry Logic

```python
# Automatic retry with exponential backoff
if result.returncode != 0:
    for attempt in range(max_retries):
        wait = 2 ** attempt  # 2, 4, 8, 16 seconds
        time.sleep(wait)
        
        result = retry_book(book)
        if result.returncode == 0:
            break
    else:
        results["failed"].append(book)
```

---

## API Reference

### `check_book_status(book_name, author_name=None) -> dict`

Analyzes a book's current state in the database.

**Parameters:**
- `book_name` (str): Book title
- `author_name` (str, optional): Author name for accurate matching

**Returns:**
```python
{
    "exists": bool,           # In database?
    "status": str or None,    # "done", "processing", or None
    "book_info": dict or None, # Full database entry
    "action": str,            # "skip", "resume", or "process"
    "title": str,             # Normalized title
    "author": str or None     # Normalized author
}
```

### `print_book_status_table(books_status) -> None`

Displays pre-flight plan as Rich table.

**Parameters:**
- `books_status` (list): List of dicts from `check_book_status()`

**Output:**
```
┌────┬─────────────┬─────────┬──────────┬─────────┐
│ #  │ Book        │ Status  │ Action   │ Details │
├────┼─────────────┼─────────┼──────────┼─────────┤
│ 1  │ Book Title  │ ✅ Done │ ⏭️ Skip  │ URL     │
└────┴─────────────┴─────────┴──────────┴─────────┘
```

### `process_books_batch(books_status, privacy, skip_completed) -> dict`

Executes intelligent batch processing.

**Parameters:**
- `books_status` (list): Pre-analyzed book statuses
- `privacy` (str): YouTube privacy ("public", "unlisted", "private")
- `skip_completed` (bool): Skip books with status="done"

**Returns:**
```python
{
    "success": [{"book": str, "author": str, "youtube_url": str}],
    "resumed": [{"book": str, "author": str, "youtube_url": str}],
    "failed": [{"book": str, "error": str}],
    "skipped": [{"book": str, "reason": str}]
}
```

### `print_final_summary(results) -> None`

Displays final summary with Rich tables.

**Parameters:**
- `results` (dict): Results from `process_books_batch()`

**Output:**
```
┌──────────────┬───────┬────────────┐
│ Category     │ Count │ Percentage │
├──────────────┼───────┼────────────┤
│ Total Books  │ 10    │ 100%       │
│ ✅ Success   │ 7     │ 70%        │
│ ♻️  Resumed  │ 2     │ 20%        │
│ ❌ Failed    │ 1     │ 10%        │
└──────────────┴───────┴────────────┘
```

---

## Troubleshooting

### Issue: All Books Skipped

**Symptom:**
```
Total: 10
Skip: 10
Process: 0
```

**Cause:** All books have `status="done"` in database.

**Solutions:**
1. Use `--no-skip` to force re-processing
2. Remove books from `database.json` (advanced)
3. Change book titles to create "new" entries

### Issue: Resume Not Working

**Symptom:** System creates new folder instead of resuming.

**Cause:** 
- Old folder not found in `runs/`
- `output.titles.json` missing from old folder
- Book name/author mismatch

**Solutions:**
1. Check `database.json` for exact book entry
2. Verify old folder exists: `runs/<timestamp>_<book>/`
3. Ensure `output.titles.json` exists in old folder
4. Match book name + author exactly (case-insensitive, but spelling matters)

### Issue: Database Corruption

**Symptom:** `json.decoder.JSONDecodeError`

**Cause:** Corrupted `database.json` file.

**Solutions:**
1. Backup current database: `copy database.json database.json.bak`
2. Restore from backup: `copy database.json.bak database.json`
3. Or reset: `echo {"books": []} > database.json`

---

**Last Updated:** 2025-10-19  
**Author:** YouTubeTB Development Team  
**Version:** 2.0.0
