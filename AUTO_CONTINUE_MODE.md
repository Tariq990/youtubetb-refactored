# Auto-Continue Mode - Unattended Batch Processing

## Overview
Auto-continue mode allows the pipeline to run without user interaction, automatically handling errors and skipping prompts. Perfect for batch processing overnight or on remote servers.

## Usage

### Single Pipeline Run
```bash
python -m src.presentation.cli.run_pipeline "Book Title" --auto-continue
```

### Batch Processing
```bash
python -m src.presentation.cli.run_batch --file books.txt --auto-continue
```

## Behavior Changes

### With `--auto-continue` flag:

#### ✅ Cookies Error
**Without flag:**
```
❌ CRITICAL: Cookies not found
Set up cookies now? (y/n):  [WAITS FOR INPUT]
```

**With flag:**
```
❌ Auto-continue mode: Cannot set up cookies automatically
Pipeline cannot continue without valid cookies.
[EXIT CODE 1]
```

#### ✅ API Errors
**Without flag:**
```
❌ Cookie check error: timeout
Continue anyway? (yes/no):  [WAITS FOR INPUT]
```

**With flag:**
```
❌ Cookie check error: timeout
🤖 Auto-continue mode: Proceeding despite cookie error...
[CONTINUES]
```

#### ✅ Batch Confirmation
**Without flag:**
```
⚠️ About to process 10 books sequentially.
Continue? (yes/no):  [WAITS FOR INPUT]
```

**With flag:**
```
⚠️ About to process 10 books sequentially.
🤖 Auto-continue mode: Starting batch without confirmation...
[STARTS IMMEDIATELY]
```

## Exit Codes

- **0**: Success
- **1**: Critical error (missing cookies, API keys, etc.)
- **130**: Interrupted by user (Ctrl+C)

## Prerequisites

For auto-continue to work successfully, ensure:

1. ✅ **Cookies are valid**: `secrets/cookies.txt` exists and is up-to-date
2. ✅ **API keys configured**: 
   - YouTube API: `secrets/api_key.txt` or `YT_API_KEY` env variable
   - Gemini API: Same file or `GEMINI_API_KEY` env variable
3. ✅ **Network is stable**: No timeouts or connection issues
4. ✅ **Sufficient disk space**: Videos can be large (500MB-2GB each)

## Examples

### Process books overnight
```bash
# Redirect output to log file
python -m src.presentation.cli.run_batch \
  --file books.txt \
  --auto-continue \
  --privacy unlisted \
  > batch_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

### Cron job (daily at 2 AM)
```cron
0 2 * * * cd /path/to/youtubetb && python -m src.presentation.cli.run_batch --auto-continue >> logs/batch.log 2>&1
```

### Docker/CI Environment
```dockerfile
CMD ["python", "-m", "src.presentation.cli.run_batch", "--auto-continue"]
```

## Monitoring

### Check batch status
```bash
tail -f batch_*.log | grep -E "SUCCESS|FAILED|SKIPPED"
```

### Count results
```bash
grep -c "✅ SUCCESS" batch_*.log
grep -c "❌ FAILED" batch_*.log
```

## Limitations

1. **Cannot set up cookies interactively** - Must be done before running
2. **No user intervention** - All errors are either skipped or cause exit
3. **Less flexible** - Cannot pause/resume midway through

## Troubleshooting

### Pipeline exits immediately
**Cause**: Missing cookies or API keys
**Solution**: Run preflight check first
```bash
python -m src.presentation.cli.run_pipeline "test" --skip-api-check=false
```

### Books fail silently
**Cause**: Auto-continue mode continues despite errors
**Solution**: Check logs for error messages
```bash
grep "ERROR\|FAILED\|Exception" batch_*.log
```

### Want to stop batch processing
```bash
# Find process ID
ps aux | grep run_batch

# Kill process
kill -SIGINT <PID>  # Graceful shutdown
kill -9 <PID>       # Force kill (last resort)
```

## Best Practices

1. ✅ **Test first**: Run 1-2 books manually before batch
2. ✅ **Monitor logs**: Use `tail -f` to watch progress
3. ✅ **Validate cookies**: Check expiry before long batches
4. ✅ **Sufficient resources**: Ensure CPU/RAM/Disk available
5. ✅ **Backup database**: Copy `database.json` before large batches

---

**Created**: 2025-10-24
**Last Updated**: 2025-10-24
