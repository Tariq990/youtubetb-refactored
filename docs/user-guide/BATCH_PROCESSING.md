# 🚀 Intelligent Batch Processing Guide

## Overview

The **Intelligent Batch Processing** system allows you to process multiple books automatically with smart handling of different scenarios.

## Key Features

### ✅ **Smart Skip**
- **Automatically skips** books already completed (`status="done"`)
- Shows YouTube URL and upload date
- **Saves time** by avoiding re-processing

### ♻️ **Smart Resume**
- **Automatically resumes** incomplete books (`status="processing"`)
- Finds the old run folder
- **Continues from last successful stage** (no re-work!)

### 🆕 **Fresh Processing**
- Processes new books from scratch
- Creates new run folder
- Adds to database with `status="processing"`

---

## Usage

### 1. **Basic Usage** (Default: books.txt)

```bash
python -m src.presentation.cli.run_batch
```

### 2. **Custom File**

```bash
python -m src.presentation.cli.run_batch --file my_books.txt
```

### 3. **Process All Books** (Including Completed)

```bash
python -m src.presentation.cli.run_batch --no-skip
```

### 4. **Set YouTube Privacy**

```bash
python -m src.presentation.cli.run_batch --privacy unlisted
```

---

## Book File Format

### **books.txt Example:**

```
# YouTubeTB - Batch Processing
# Format: Book Title | Author Name

# Self-Development
Atomic Habits | James Clear
Deep Work | Cal Newport
The 7 Habits of Highly Effective People | Stephen Covey

# Philosophy
The 48 Laws of Power | Robert Greene
Meditations | Marcus Aurelius

# Psychology
Thinking, Fast and Slow | Daniel Kahneman
Influence: The Psychology of Persuasion | Robert Cialdini

# Books without author (optional)
The Alchemist
1984

# Comments start with #
# Empty lines are ignored
```

---

## How It Works

### **Step 1: Pre-Analysis**

The system analyzes all books **before** processing:

```
📚 BATCH PROCESSING PLAN
┌────┬──────────────────────┬──────────┬──────────┬────────────────────┐
│ #  │ Book                 │ Status   │ Action   │ Details            │
├────┼──────────────────────┼──────────┼──────────┼────────────────────┤
│ 1  │ Atomic Habits        │ ✅ Done  │ ⏭️ Skip  │ youtube.com/...    │
│ 2  │ Deep Work            │ ♻️ Inc.  │ ▶️ Resume│ 2025-10-19_...     │
│ 3  │ The Alchemist        │ 🆕 New   │ 🚀 Process│ Fresh start       │
└────┴──────────────────────┴──────────┴──────────┴────────────────────┘

Total: 3 books
⏭️  Skip (already done): 1
♻️  Resume (incomplete): 1
🚀 Process (new): 1
```

### **Step 2: Processing**

Each book is processed based on its status:

#### **Case 1: Already Completed** (`status="done"`)
```
📖 Book 1/3: Atomic Habits
   Status: done | Action: skip

⏭️  SKIPPED: Already completed!
   YouTube: https://youtube.com/watch?v=...
```

#### **Case 2: Incomplete** (`status="processing"`)
```
📖 Book 2/3: Deep Work
   Status: processing | Action: resume

♻️  RESUMING from last successful stage...
🔧 Running: python -m src.presentation.cli.run_pipeline "Deep Work | Cal Newport"

[Pipeline finds old folder: 2025-10-19_15-30-00_Deep-Work]
[Reads summary.json: search✅ transcribe✅ process✅ tts❌]
[Resumes from TTS stage]
...
✅ SUCCESS (RESUMED): Deep Work
```

#### **Case 3: New Book**
```
📖 Book 3/3: The Alchemist
   Status: new | Action: process

🚀 PROCESSING from scratch...
🔧 Running: python -m src.presentation.cli.run_pipeline "The Alchemist"

[Pipeline creates new folder: 2025-10-19_16-00-00_The-Alchemist]
[Processes: Search → Transcribe → Process → TTS → Render → Upload]
...
✅ SUCCESS: The Alchemist
   📺 Main Video: https://youtube.com/watch?v=...
   🎬 Short: https://youtube.com/shorts/...
```

### **Step 3: Final Summary**

```
📊 BATCH PROCESSING COMPLETE
┌────────────────────┬───────┬────────────┐
│ Category           │ Count │ Percentage │
├────────────────────┼───────┼────────────┤
│ Total Books        │ 3     │ 100%       │
│ ✅ Success (New)   │ 1     │ 33.3%      │
│ ♻️  Success (Res.) │ 1     │ 33.3%      │
│ ❌ Failed          │ 0     │ 0.0%       │
│ ⏭️  Skipped        │ 1     │ 33.3%      │
└────────────────────┴───────┴────────────┘

✅ Successfully Processed (New):
   • The Alchemist
     https://youtube.com/watch?v=xyz123

♻️  Successfully Resumed:
   • Deep Work
     https://youtube.com/watch?v=abc456

⏭️  Skipped Books:
   • Atomic Habits
     Reason: Already completed
```

---

## Advanced Scenarios

### **Scenario 1: All Books Already Completed**

If all books are already in database with `status="done"`:

```bash
$ python -m src.presentation.cli.run_batch

📊 Summary:
   Total: 5
   Skip: 5
   Resume: 0
   Process: 0

📖 Book 1/5: Atomic Habits → ⏭️ SKIPPED
📖 Book 2/5: Deep Work → ⏭️ SKIPPED
...

✅ All books already completed! No processing needed.
```

To force re-processing:
```bash
python -m src.presentation.cli.run_batch --no-skip
```

### **Scenario 2: Resume Multiple Incomplete Books**

If you have books stuck at different stages:

```
Book A: Stopped at TTS (50% done)
Book B: Stopped at Render (80% done)
Book C: Stopped at Upload (95% done)
```

The system will:
1. Resume Book A from TTS
2. Resume Book B from Render
3. Resume Book C from Upload

**No re-work!** Each book continues from where it stopped.

### **Scenario 3: Handling Failures**

If a book fails during batch processing:

```
📖 Book 2/5: Failed Book
   Status: processing | Action: resume

❌ FAILED: Failed Book
   Exit code: 1
   Continuing with next book...

⏳ Waiting 5 seconds before next book...

📖 Book 3/5: Next Book
...
```

The system:
- Logs the failure
- **Continues** with remaining books
- Shows failed books in final summary

---

## Interrupting Batch Processing

Press `Ctrl+C` to stop:

```
⚠️  INTERRUPTED by user at book 3/5
   Stopping batch processing...

Remaining books marked as skipped:
   • Book 4
   • Book 5
```

Resume later - the system will pick up where you left off!

---

## Database Integration

All actions are tracked in `database.json`:

```json
{
  "books": [
    {
      "main_title": "Atomic Habits",
      "author_name": "James Clear",
      "status": "done",
      "youtube_url": "https://youtube.com/watch?v=...",
      "date_added": "2025-10-19T10:30:00",
      "run_folder": "2025-10-19_10-30-00_Atomic-Habits"
    },
    {
      "main_title": "Deep Work",
      "author_name": "Cal Newport",
      "status": "processing",
      "date_added": "2025-10-19T11:00:00",
      "run_folder": "2025-10-19_11-00-00_Deep-Work"
    }
  ]
}
```

---

## Best Practices

### ✅ **Do's**
- ✅ Use `Book | Author` format for accuracy
- ✅ Check database before adding new books
- ✅ Let the system skip completed books (default)
- ✅ Keep `books.txt` organized with comments
- ✅ Process books in batches (10-20 at a time)

### ❌ **Don'ts**
- ❌ Don't use `--no-skip` unless necessary (wastes resources)
- ❌ Don't interrupt during upload stage (can corrupt database)
- ❌ Don't manually edit `database.json` while processing
- ❌ Don't process duplicate books in same batch

---

## Troubleshooting

### **Problem 1: Book Not Detected as Complete**

**Symptom:** System tries to re-process a completed book

**Cause:** Book name mismatch in `books.txt` vs database

**Solution:**
```bash
# Check database entry
cat database.json | grep "Book Title"

# Ensure exact match in books.txt
Atomic Habits | James Clear  # ✅ Correct
atomic habits | james clear  # ❌ Wrong (case-insensitive but different)
```

### **Problem 2: Resume Not Working**

**Symptom:** System creates new folder instead of resuming

**Cause:** Old folder not found or `output.titles.json` missing

**Solution:**
1. Check `runs/` directory for old folder
2. Verify `output.titles.json` exists in old folder
3. Ensure book name + author match exactly

### **Problem 3: All Books Skipped**

**Symptom:** `Skip: 10, Process: 0`

**Cause:** All books already completed

**Solution:**
- This is **normal behavior** (intelligent skip)
- To force re-process: use `--no-skip`
- Or remove books from `database.json` (advanced)

---

## Command Reference

```bash
# Basic batch processing
python -m src.presentation.cli.run_batch

# Custom file
python -m src.presentation.cli.run_batch --file my_books.txt

# Process all (no skip)
python -m src.presentation.cli.run_batch --no-skip

# Set privacy
python -m src.presentation.cli.run_batch --privacy unlisted

# Combine options
python -m src.presentation.cli.run_batch --file books.txt --privacy public --no-skip

# Show help
python -m src.presentation.cli.run_batch --help
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | All successful |
| `1`  | All failed |
| `2`  | Some failures, some success |

Example:
```bash
python -m src.presentation.cli.run_batch
echo $?  # Linux/Mac
echo %ERRORLEVEL%  # Windows

# 0 = success
# 1 = failure
# 2 = partial success
```

---

## Performance Tips

### **Optimal Batch Size**
- **Small batches** (5-10 books): Better for testing
- **Medium batches** (10-20 books): Recommended for production
- **Large batches** (20+ books): Use with caution (takes hours!)

### **Time Estimates**
- **Short video** (15-30 min source): ~10-15 min processing
- **Medium video** (30-60 min source): ~20-30 min processing
- **Long video** (60-90 min source): ~40-60 min processing

**Example:** Batch of 10 books (avg 30 min each) = **~4-5 hours total**

### **Resource Usage**
- **CPU**: High during render stage
- **RAM**: Moderate (2-4 GB)
- **Disk**: ~500 MB per book (temporary)
- **Network**: High during upload stage

---

## Future Improvements (Planned)

- [ ] **Parallel Processing**: Process multiple books simultaneously
- [ ] **Priority Queue**: Set book priorities (high/medium/low)
- [ ] **Scheduling**: Auto-process at specific times
- [ ] **Email Notifications**: Alert when batch completes
- [ ] **Web Dashboard**: Monitor progress in browser
- [ ] **Cloud Integration**: Process on remote servers

---

## Related Documentation

- [Pipeline Architecture](../architecture/PIPELINE.md)
- [Database Schema](../api/DATABASE.md)
- [Resume System](./RESUME.md)
- [Error Handling](./TROUBLESHOOTING.md)

---

**Last Updated:** 2025-10-19
**Version:** 2.0.0 (Intelligent Batch Processing)
