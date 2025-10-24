# Gemini API Keys - Fallback System 🔑

## Overview
The system now supports **multiple API keys with automatic fallback**. If one key exceeds quota (429 error), it automatically tries the next key.

## Setup

### 1. Single Key (Old Method)
```
secrets/api_key.txt
```
Single line with one API key.

### 2. Multiple Keys (New Method - Recommended)
```
secrets/api_keys.txt
```

**Format:**
```
# Gemini API Keys (Fallback List)
# Lines starting with # are ignored

AIzaSyAUxXkiTOaEEUdFk7VVJC0vRZU1KTF_qoY
AIzaSyCUxL3eWSJA9Mhi69iQ9Z-C09vyoCQWEbc
AIzaSyC_ANOTHER_KEY_HERE
```

- One key per line
- Comments start with `#`
- Empty lines are ignored
- Keys are tried in order (top to bottom)

## How It Works

1. **Load Keys**: System reads all keys from `api_keys.txt` (or fallback to `api_key.txt`)
2. **Try First Key**: Attempts to use first key
3. **On Quota Error (429)**: Automatically switches to next key
4. **Success**: Uses first working key for entire pipeline
5. **All Failed**: Shows error message with troubleshooting steps

## Example Log Output

```
📋 Loaded 3 API key(s) for fallback
🔑 Trying API key 1/3: AIzaSyAUxX...
⚠️  API key 1 quota exceeded: 429 You exceeded your current quota
🔑 Trying API key 2/3: AIzaSyCUxL...
✅ API key 2 working with model: gemini-2.5-flash
```

## Priority Order

1. **Environment Variable**: `GEMINI_API_KEY` (highest priority)
2. **Multi-key File**: `secrets/api_keys.txt` (recommended)
3. **Single-key File**: `secrets/api_key.txt` (legacy fallback)

## Benefits

- ✅ **Zero Downtime**: Automatic failover between keys
- ✅ **Batch Processing**: Can process more books without waiting
- ✅ **Quota Management**: Distributes load across multiple keys
- ✅ **Easy Setup**: Just add keys to `api_keys.txt`, one per line

## Monitoring

The system logs which key is being used:
```
🔑 Trying API key 1/2: AIzaSyAUxX...
✅ API key 1 working with model: gemini-2.5-flash
```

If a key fails with quota:
```
⚠️  API key 1 quota exceeded: 429 You exceeded your current quota
```

## Getting More Keys

1. Visit: https://aistudio.google.com/apikey
2. Create new API key
3. Add to `secrets/api_keys.txt`
4. No restart needed - next pipeline run will use it

## Troubleshooting

### All Keys Failed
```
❌ CRITICAL: All 3 API key(s) failed!
   Last error: 429 You exceeded your current quota
```

**Solutions:**
1. Wait for quota reset (15 requests/minute, resets every minute)
2. Add more API keys to `api_keys.txt`
3. Upgrade to paid tier for higher quotas
4. Check billing at https://console.cloud.google.com/billing

### Keys Not Loading
```
❌ GEMINI_API_KEY not found. Set env or add secrets/api_keys.txt
```

**Solutions:**
1. Create `secrets/api_keys.txt`
2. Add at least one valid key
3. Ensure no extra spaces/newlines
4. Check file encoding is UTF-8

## Testing

Test the fallback system:
```bash
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'src'); from infrastructure.adapters.process import _configure_model; model = _configure_model(Path('config')); print('✅ Success!' if model else '❌ Failed!')"
```

Expected output:
```
📋 Loaded 2 API key(s) for fallback
🔑 Trying API key 1/2: AIzaSyAUxX...
✅ API key 1 working with model: gemini-2.5-flash
✅ Success!
```

## Migration Guide

**From single key to multiple keys:**

1. Rename existing file:
   ```bash
   move secrets\api_key.txt secrets\api_keys.txt
   ```

2. Add comment header:
   ```
   # Gemini API Keys (Fallback List)
   [existing key here]
   ```

3. Add more keys (one per line):
   ```
   # Gemini API Keys (Fallback List)
   AIzaSyAUxXkiTOaEEUdFk7VVJC0vRZU1KTF_qoY
   AIzaSyCUxL3eWSJA9Mhi69iQ9Z-C09vyoCQWEbc
   AIzaSyC_YOUR_THIRD_KEY_HERE
   ```

4. Test:
   ```bash
   python main.py
   # Select Option 0 to validate APIs
   ```

## Last Updated
October 24, 2025 - Added automatic API key fallback system
