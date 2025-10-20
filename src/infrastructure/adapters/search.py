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


def main(query: str | None = None, output_dir: os.PathLike | None = None):
    import os as _os
    API_KEY = _os.environ.get("YT_API_KEY")
    if not API_KEY:
        # prefer secrets/api_key.txt then local api_key.txt
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        for f in (os.path.join(base_dir, "secrets", "api_key.txt"), os.path.join(base_dir, "api_key.txt")):
            try:
                with open(f, "r", encoding="utf-8") as _kf:
                    API_KEY = _kf.read().strip()
                    break
            except Exception:
                API_KEY = None

    if not API_KEY:
        safe_print("No YouTube API key found. Place your key in 'secrets/api_key.txt' or set YT_API_KEY.")
        return None

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
        sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
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
    response1 = requests.get(BASE_URL, params=params_relevance)
    data1 = response1.json()
    for item in data1.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id and video_id not in video_ids_set:
            all_video_ids.append(video_id)
            video_ids_set.add(video_id)

    print(f"   >> Collected {len(all_video_ids)} videos from Phase 1")

    # Second search (date)
    response2 = requests.get(BASE_URL, params=params_date)
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

    video_ids = all_video_ids
    results = []

    if video_ids:
        details_url = "https://www.googleapis.com/youtube/v3/videos"
        details_params = {
            "part": "snippet,contentDetails",
            "id": ",".join(video_ids),
            "key": API_KEY
        }
        details_resp = requests.get(details_url, params=details_params)
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
                chan_resp = requests.get(chan_url, params=chan_params)
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


if __name__ == "__main__":
    # Allow standalone usage for manual testing
    q = None
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    main(q)
