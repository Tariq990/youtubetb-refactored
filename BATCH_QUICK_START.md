# 🎯 Quick Start: Intelligent Batch Processing

## What's New? 🚀

The new **intelligent batch processing system** can process multiple books automatically with **smart handling**:

- ✅ **Skips** books already completed (`status="done"`)
- ♻️ **Resumes** incomplete books from last stage (`status="processing"`)  
- 🆕 **Processes** new books from scratch

**No duplicate work!** The system checks `database.json` before processing each book.

---

## Usage

### 1️⃣ Basic Usage

```bash
python -m src.presentation.cli.run_batch
```

This will process books from `books.txt` (default file).

### 2️⃣ Custom File

```bash
python -m src.presentation.cli.run_batch --file my_books.txt
```

### 3️⃣ Force Re-process (Skip Nothing)

```bash
python -m src.presentation.cli.run_batch --no-skip
```

---

## Book File Format

### `books.txt` Example:

```
# Format: Book Title | Author Name

# Self-Development
Atomic Habits | James Clear
Deep Work | Cal Newport
The 7 Habits of Highly Effective People | Stephen Covey

# Philosophy
The 48 Laws of Power | Robert Greene
Meditations | Marcus Aurelius

# Books without author (optional)
The Alchemist
1984
```

**📝 Format Rules:**
- `Book Title | Author Name` (recommended for accuracy)
- OR just `Book Title` (system will search without author filter)
- Lines starting with `#` are comments
- Empty lines are ignored

---

## How It Works

### **Step 1: Pre-Flight Analysis** 📊

Before processing, the system shows you a **plan**:

```
┌────┬─────────────────┬─────────┬──────────┬─────────────────┐
│ #  │ Book            │ Status  │ Action   │ Details         │
├────┼─────────────────┼─────────┼──────────┼─────────────────┤
│ 1  │ Atomic Habits   │ ✅ Done │ ⏭️ Skip  │ youtube.com/... │
│ 2  │ Deep Work       │ ♻️ Inc. │ ▶️ Resume│ Continue...     │
│ 3  │ The Alchemist   │ 🆕 New  │ 🚀 Process│ Fresh start    │
└────┴─────────────────┴─────────┴──────────┴─────────────────┘

Proceed with batch processing? [y/N]:
```

### **Step 2: Smart Processing** 🧠

Each book is handled based on its status:

- **Already Done** (`status="done"`):
  ```
  ⏭️ SKIPPED: Atomic Habits
     YouTube: https://youtube.com/watch?v=...
  ```

- **Incomplete** (`status="processing"`):
  ```
  ♻️ RESUMING: Deep Work
     Last stage: TTS (60% complete)
     Continuing from TTS...
  ```

- **New Book**:
  ```
  🚀 PROCESSING: The Alchemist
     Search → Transcribe → Process → TTS → Render → Upload
  ```

### **Step 3: Final Summary** 📈

```
┌──────────────┬───────┬────────────┐
│ Category     │ Count │ Percentage │
├──────────────┼───────┼────────────┤
│ Total Books  │ 3     │ 100%       │
│ ✅ Success   │ 1     │ 33.3%      │
│ ♻️ Resumed   │ 1     │ 33.3%      │
│ ⏭️ Skipped   │ 1     │ 33.3%      │
└──────────────┴───────┴────────────┘
```

---

## Examples

### Example 1: First Time Run

```bash
# Create books.txt with 5 books
$ python -m src.presentation.cli.run_batch

📊 Plan:
   Total: 5
   Process: 5 (all new)
   
Proceed? [y/N]: y

🚀 Processing 5 books...
✅ Book 1/5: Atomic Habits → SUCCESS
✅ Book 2/5: Deep Work → SUCCESS
...
```

### Example 2: Resume After Interruption

```bash
# Same books.txt, but you stopped at book 3
$ python -m src.presentation.cli.run_batch

📊 Plan:
   Total: 5
   Skip: 2 (already done)
   Resume: 1 (incomplete)
   Process: 2 (new)
   
Proceed? [y/N]: y

⏭️ Book 1/5: Atomic Habits → SKIPPED
⏭️ Book 2/5: Deep Work → SKIPPED
♻️ Book 3/5: The Alchemist → RESUMED (from Upload)
🚀 Book 4/5: Think and Grow Rich → SUCCESS
🚀 Book 5/5: Rich Dad Poor Dad → SUCCESS
```

### Example 3: All Already Done

```bash
$ python -m src.presentation.cli.run_batch

📊 Plan:
   Total: 5
   Skip: 5 (all done)
   
⚠️  All books already completed! No processing needed.
   
Use --no-skip to force re-processing.
```

---

## Testing the System

### Test Database Integration

```bash
python test_batch.py
```

This will:
- Show database statistics
- Test book matching logic
- Test intelligent action detection
- Parse sample batch file

---

## Advanced Options

### Set YouTube Privacy

```bash
python -m src.presentation.cli.run_batch --privacy unlisted
# Options: public, unlisted, private
```

### Combine Options

```bash
python -m src.presentation.cli.run_batch \
    --file arabic_books.txt \
    --privacy public \
    --no-skip
```

### Show Help

```bash
python -m src.presentation.cli.run_batch --help
```

---

## Performance Tips

### Recommended Batch Sizes

- **Testing**: 3-5 books
- **Production**: 10-20 books
- **Large batches**: 20+ books (takes hours!)

### Time Estimates

| Video Length | Processing Time |
|--------------|-----------------|
| 15-30 min    | ~10-15 min     |
| 30-60 min    | ~20-30 min     |
| 60-90 min    | ~40-60 min     |

**Example:** 10 books × 30 min avg = **~5 hours total**

---

## Troubleshooting

### Problem: Book not detected as complete

**Cause:** Name mismatch between `books.txt` and database

**Solution:** Ensure exact match (case-insensitive):
```
✅ Atomic Habits | James Clear
❌ atomic habits | james clear  (different case, but should work)
❌ Atomic Habit | James Clear   (missing 's')
```

### Problem: All books skipped

**Cause:** All books already in database with `status="done"`

**Solution:** This is **normal behavior** (intelligent skip!)
- To re-process: use `--no-skip` flag
- Or remove books from `database.json` (advanced)

### Problem: Resume not working

**Cause:** Old run folder not found

**Solution:**
1. Check `runs/` directory for old folder
2. Verify `output.titles.json` exists
3. Ensure book name + author match exactly

---

## Files Involved

- **Input**: `books.txt` (or custom file via `--file`)
- **Database**: `database.json` (tracks all books + statuses)
- **Runs**: `runs/*/summary.json` (tracks stage completion)
- **Script**: `src/presentation/cli/run_batch.py`

---

## Next Steps

1. **Create** `books.txt` with your books (see `books_examples.txt` for examples)
2. **Test** with 3-5 books first
3. **Run** `python -m src.presentation.cli.run_batch`
4. **Monitor** progress in terminal
5. **Check** final summary for results

---

## Full Documentation

See `docs/user-guide/BATCH_PROCESSING.md` for:
- Detailed architecture
- All scenarios and examples
- Troubleshooting guide
- Best practices

---

**Last Updated:** 2025-10-19  
**Version:** 2.0.0 (Intelligent Batch Processing)

---

## Quick Reference Card 📋

```bash
# Basic run
python -m src.presentation.cli.run_batch

# Custom file
python -m src.presentation.cli.run_batch --file my_books.txt

# Force re-process
python -m src.presentation.cli.run_batch --no-skip

# Set privacy
python -m src.presentation.cli.run_batch --privacy unlisted

# Test system
python test_batch.py

# Show help
python -m src.presentation.cli.run_batch --help
```

**🎯 Pro Tip:** Start with 3-5 books to test the system, then scale up to 10-20 books for production use!
