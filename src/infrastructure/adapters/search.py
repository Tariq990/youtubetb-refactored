import os
import sys
import requests
import arabic_reshaper
from typing import Any
from bidi.algorithm import get_display

# Try to set Windows console to use UTF-8 code page so Arabic prints correctly.
# Only run on Windows to avoid "chcp not found" warning on Linux/Mac
try:
    if sys.platform == 'win32':
        os.system('chcp 65001 >nul')
except Exception:
    pass

try:
    reconf = getattr(sys.stdout, "reconfigure", None)
    if callable(reconf):
        reconf(encoding='utf-8')
    else:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except Exception:
    pass


def fix_arabic(text: str) -> str:
    try:
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return str(bidi_text)
    except Exception:
        return str(text)


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((text + '\n').encode('utf-8', errors='replace'))
        except Exception:
            print(text.encode('utf-8', errors='replace'))


def _load_all_youtube_api_keys():
    """Load all available YouTube API keys for fallback system."""
    import os as _os
    api_keys = []
    
    # 1. Environment variable first
    env_key = _os.environ.get("YT_API_KEY") or _os.environ.get("YOUTUBE_API_KEY")
    if env_key:
        api_keys.append(env_key.strip())
    
    # 2. Multi-key file (api_keys.txt)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    api_keys_file = os.path.join(base_dir, "secrets", "api_keys.txt")
    if os.path.exists(api_keys_file):
        try:
            with open(api_keys_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Remove inline comments (split on #)
                        key = line.split('#')[0].strip()
                        if key and key not in api_keys:  # Avoid duplicates
                            api_keys.append(key)
        except Exception:
            pass
    
    # 3. Single-key file fallback (api_key.txt)
    if not api_keys:
        for f in (os.path.join(base_dir, "secrets", "api_key.txt"), os.path.join(base_dir, "api_key.txt")):
            try:
                with open(f, "r", encoding="utf-8") as _kf:
                    key = _kf.read().strip()
                    if key:
                        api_keys.append(key)
                        break
            except Exception:
                pass
    
    return api_keys


def main(query: str | None = None, output_dir: os.PathLike | None = None):
    # Load ALL API keys for fallback
    API_KEYS = _load_all_youtube_api_keys()
    
    if not API_KEYS:
        safe_print("No YouTube API key found. Place your key in 'secrets/api_keys.txt' or set YT_API_KEY.")
        return None
    
    safe_print(f"📋 Loaded {len(API_KEYS)} API key(s) for fallback")

    if query is None:
        print("Enter book name: ", end='')
        book_name = input()
    else:
        book_name = query

    # Save input_name.txt into provided output_dir (if any), avoid legacy outputs/
    if output_dir is not None:
        try:
            os.makedirs(output_dir, exist_ok=True)
            _input_path = os.path.join(output_dir, "input_name.txt")
            with open(_input_path, "w", encoding="utf-8") as _f:
                _f.write(book_name.strip() + "\n")
        except Exception as _e:
            safe_print(f"Failed to save book name to input_name.txt in output_dir: {_e}")

    # Detect language and construct appropriate query
    try:
        import sys
        from pathlib import Path as _Path
        sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))  # Fixed: parents[3] to reach repo root
        from src.shared.utils.language_detector import detect_language
        detected_lang = detect_language(book_name)
    except Exception:
        # Fallback: assume Arabic if detection fails
        detected_lang = "ar"
    
    print(f">>> Detected language: {detected_lang}")
    
    BASE_URL = "https://www.googleapis.com/youtube/v3/search"
    
    # Construct query based on language
    if detected_lang == "ar":
        query_full = f"\u0645\u0644\u062e\u0635 \u0643\u062a\u0627\u0628 {book_name}"  # "ملخص كتاب "
    else:
        query_full = f"{book_name} book summary"
    
    print(f">>> Search query: {query_full}")
    
    # Save detected language to file for downstream stages
    if output_dir is not None:
        try:
            lang_file = os.path.join(output_dir, "detected_language.txt")
            with open(lang_file, "w", encoding="utf-8") as _lf:
                _lf.write(detected_lang)
        except Exception as _e:
            safe_print(f"Warning: Could not save detected language: {_e}")

    # Try each API key with fallback system
    last_error = None
    for key_idx, API_KEY in enumerate(API_KEYS, start=1):
        try:
            # Mask key for security
            masked_key = API_KEY[:10] + "..." if len(API_KEY) > 10 else API_KEY
            if len(API_KEYS) > 1:
                print(f"🔑 Trying API key {key_idx}/{len(API_KEYS)}: {masked_key}")
            
            # Phase 1: Search by relevance (popular videos)
            print(">>> Phase 1: Searching by relevance (popular videos)...")
            params_relevance = {
                "part": "snippet",
                "q": query_full,
                "type": "video",
                "maxResults": 15,
                "order": "relevance",
                "key": API_KEY
            }

            # Phase 2: Search by date (recent videos)
            print(">>> Phase 2: Searching by date (recent videos)...")
            params_date = {
                "part": "snippet",
                "q": query_full,
                "type": "video",
                "maxResults": 10,
                "order": "date",
                "key": API_KEY
            }

            # Collect results from both phases
            all_video_ids = []
            video_ids_set = set()  # Avoid duplicates

            # First search (relevance)
            response1 = requests.get(BASE_URL, params=params_relevance, timeout=15)
            if response1.status_code == 403:
                error_data = response1.json().get("error", {})
                if "quota" in error_data.get("message", "").lower():
                    print(f"⚠️  API key {key_idx}/{len(API_KEYS)}: Quota exceeded")
                    if key_idx < len(API_KEYS):
                        print(f"   Trying next API key...")
                        continue
                    else:
                        print(f"❌ All {len(API_KEYS)} API key(s) quota exceeded!")
                        return None
            
            response1.raise_for_status()  # Raise for other errors
            data1 = response1.json()
            for item in data1.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id and video_id not in video_ids_set:
                    all_video_ids.append(video_id)
                    video_ids_set.add(video_id)

            print(f"   >> Collected {len(all_video_ids)} videos from Phase 1")

            # Second search (date)
            response2 = requests.get(BASE_URL, params=params_date, timeout=15)
            if response2.status_code == 403:
                error_data = response2.json().get("error", {})
                if "quota" in error_data.get("message", "").lower():
                    print(f"⚠️  API key {key_idx}/{len(API_KEYS)}: Quota exceeded (Phase 2)")
                    if key_idx < len(API_KEYS):
                        print(f"   Trying next API key...")
                        continue
                    else:
                        print(f"❌ All {len(API_KEYS)} API key(s) quota exceeded!")
                        return None
            
            response2.raise_for_status()
            data2 = response2.json()
            count_before = len(all_video_ids)
            for item in data2.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id and video_id not in video_ids_set:
                    all_video_ids.append(video_id)
                    video_ids_set.add(video_id)

            new_videos = len(all_video_ids) - count_before
            print(f"   >> Collected {new_videos} new videos from Phase 2")
            print(f">>> Total: {len(all_video_ids)} unique videos\n")

            # If we got here, this API key is working!
            if len(API_KEYS) > 1:
                print(f"✅ API key {key_idx}/{len(API_KEYS)} working!")
            
            video_ids = all_video_ids
            results = []

            if video_ids:
                details_url = "https://www.googleapis.com/youtube/v3/videos"
                details_params = {
                    "part": "snippet,contentDetails",
                    "id": ",".join(video_ids),
                    "key": API_KEY
                }
                details_resp = requests.get(details_url, params=details_params, timeout=15)
                details_resp.raise_for_status()
                details_data = details_resp.json()
                duration_map = {}
                snippet_map = {}
                for item in details_data.get("items", []):
                    vid = item.get("id")
                    duration = item.get("contentDetails", {}).get("duration", "")
                    snip = item.get("snippet", {})
                    duration_map[vid] = duration
                    snippet_map[vid] = snip

                channel_ids = set()
                for snip in snippet_map.values():
                    cid = snip.get('channelId')
                    if cid:
                        channel_ids.add(cid)

                channel_country = {}
                if channel_ids:
                    chan_url = "https://www.googleapis.com/youtube/v3/channels"
                    chan_params = {"part": "snippet", "id": ",".join(channel_ids), "key": API_KEY}
                    try:
                        chan_resp = requests.get(chan_url, params=chan_params, timeout=15)
                        chan_resp.raise_for_status()
                        chan_data = chan_resp.json()
                        for it in chan_data.get('items', []):
                            cid = it.get('id')
                            c_snip = it.get('snippet', {})
                            country = c_snip.get('country') or ""
                            channel_country[cid] = country
                    except Exception:
                        pass

                def parse_iso8601_duration(duration):
                    import re
                    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
                    if not match:
                        return 0
                    hours = int(match.group(1) or 0)
                    minutes = int(match.group(2) or 0)
                    seconds = int(match.group(3) or 0)
                    return hours * 3600 + minutes * 60 + seconds

                filtered = []
                excluded_count = 0
                for vid in video_ids:
                    dur = duration_map.get(vid, "")
                    total_seconds = parse_iso8601_duration(dur)
                    snip = snippet_map.get(vid, {})
                    title = snip.get("title", "")

                    # Print each video for analysis
                    minutes = total_seconds // 60
                    if total_seconds < 900 or total_seconds > 3300:  # 15 min - 55 min
                        print(f"[X] Excluded: {title[:50]}... ({minutes} min)")
                        excluded_count += 1
                        continue

                    # Video accepted
                    print(f"[OK] Accepted: {title[:50]}... ({minutes} min)")
                    channel = snip.get("channelTitle", "")
                    channel_id = snip.get('channelId')
                    city = channel_country.get(channel_id, "")
                    published_at = snip.get("publishedAt", "")
                    url = f"https://www.youtube.com/watch?v={vid}" if vid else ""
                    filtered.append({
                        "title": title,
                        "channel": channel,
                        "city": city,
                        "publishedAt": published_at,
                        "videoId": vid,
                        "url": url,
                        "viewCount": None,
                        "duration": total_seconds
                    })

                print(f"\n>>> Stats: {len(filtered)} accepted, {excluded_count} excluded from {len(video_ids)} videos")

                results = []
                if filtered:
                    filtered_sorted = sorted(filtered, key=lambda x: x["duration"], reverse=True)
                    results = filtered_sorted[:10]  # زيادة من 5 إلى 10 مرشحين

                # enrich view counts
                from datetime import datetime
                vid_ids = [r["videoId"] for r in results if r["videoId"]]
                if vid_ids:
                    vids_url = "https://www.googleapis.com/youtube/v3/videos"
                    vids_params = {"part": "statistics", "id": ",".join(vid_ids), "key": API_KEY}
                    try:
                        vids_resp = requests.get(vids_url, params=vids_params)
                        vids_data = vids_resp.json()
                        stats_map = {}
                        for it in vids_data.get("items", []):
                            vid = it.get("id")
                            vc = it.get("statistics", {}).get("viewCount")
                            try:
                                stats_map[vid] = int(vc) if vc is not None else 0
                            except Exception:
                                stats_map[vid] = 0
                        for r in results:
                            if r["videoId"] in stats_map:
                                r["viewCount"] = stats_map[r["videoId"]]
                    except Exception:
                        pass

                # print results
                if not results:
                    safe_print(fix_arabic("لم يتم العثور على نتائج."))
                    if key_idx < len(API_KEYS):
                        print(f"⚠️  No results with API key {key_idx}/{len(API_KEYS)}, trying next...")
                        continue
                    else:
                        return None

                # Save all candidates to the run folder if provided
                try:
                    if output_dir is not None:
                        import json as _json
                        with open(os.path.join(output_dir, "search.results.json"), "w", encoding="utf-8") as _f:
                            _json.dump({"candidates": results}, _f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

                # Return the best candidate (longest) but embed the full candidates list for downstream retries
                best = dict(results[0])
                best["candidates"] = results
                safe_print(fix_arabic("تم اختيار الفيديو الأطول كأفضل مرشح."))
                safe_print(f"Title: {best['title']} | URL: {best['url']}")
                return best
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"⚠️  API key {key_idx}/{len(API_KEYS)}: Request error - {error_msg[:100]}")
            last_error = e
            if key_idx < len(API_KEYS):
                print(f"   Trying next API key...")
                continue
            else:
                print(f"❌ All {len(API_KEYS)} API key(s) failed!")
                return None
        
        except Exception as e:
            print(f"⚠️  API key {key_idx}/{len(API_KEYS)}: Unexpected error - {str(e)[:100]}")
            last_error = e
            if key_idx < len(API_KEYS):
                print(f"   Trying next API key...")
                continue
            else:
                print(f"❌ All {len(API_KEYS)} API key(s) failed!")
                return None
    
    # If we reach here, all keys failed
    print(f"❌ All {len(API_KEYS)} API key(s) failed!")
    if last_error:
        print(f"   Last error: {str(last_error)[:200]}")
    return None


if __name__ == "__main__":
    # Allow standalone usage for manual testing
    q = None
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    main(q)
