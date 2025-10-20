from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import os
import json
import absl.logging
import importlib
import requests
from urllib.parse import quote_plus
import re
import unicodedata
import time
import random
from bs4 import BeautifulSoup


def _load_prompts(config_dir: Path) -> dict:
    p = Path(config_dir) / "prompts.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # join list-valued templates into strings for convenience
            for k in ("clean_template","translate_template","book_meta_template","titles_template"):
                v = data.get(k)
                if isinstance(v, list):
                    data[k] = "\n".join(v)
            return data
        except Exception:
            pass
    return {}


absl.logging.set_verbosity(absl.logging.ERROR)


def _load_detected_language(run_dir: Path) -> str:
    """
    Load detected language from search stage.
    
    Args:
        run_dir: Run directory containing detected_language.txt
        
    Returns:
        "ar" for Arabic (default), "en" for English
    """
    lang_file = Path(run_dir) / "detected_language.txt"
    if lang_file.exists():
        try:
            lang = lang_file.read_text(encoding="utf-8").strip()
            if lang in ("ar", "en"):
                return lang
        except Exception:
            pass
    # Default to Arabic for backward compatibility
    return "ar"


def _fmt(tpl, **values):
    """
    Replace {key} placeholders in template, leaving all
    other braces (like JSON { ... }) untouched.
    If tpl is a list, join it first.
    """
    # Handle list templates (from prompts.json)
    if isinstance(tpl, list):
        tpl = "\n".join(tpl)

    out = tpl
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _safe_text(resp) -> str:
    try:
        return getattr(resp, "text", "") or ""
    except Exception:
        return ""


def _gen(model, prompt: str, mime_type: str = "text/plain") -> str:
    try:
        resp = model.generate_content(prompt, generation_config={"response_mime_type": mime_type})
        return _safe_text(resp)
    except Exception as e:
        print(f"API call failed: {e}")
        return ""


def _configure_model(config_dir: Optional[Path] = None) -> Optional[object]:
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        repo_root = Path(__file__).resolve().parents[2]
        for f in (repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"):
            try:
                if f.exists():
                    API_KEY = f.read_text(encoding="utf-8").strip()
                    break
            except Exception:
                pass
    if not API_KEY:
        print("GEMINI_API_KEY not found. Set env or add secrets/api_key.txt")
        return None
    # Determine model name from env or settings.json
    model_name = os.environ.get("GEMINI_MODEL")
    if not model_name and config_dir:
        try:
            sj = json.loads((Path(config_dir) / "settings.json").read_text(encoding="utf-8"))
            model_name = sj.get("gemini_model") or sj.get("gemini_model_name")
        except Exception:
            model_name = None
    if not model_name:
        model_name = "gemini-2.5-flash"
    genai = importlib.import_module("google.generativeai")
    getattr(genai, "configure")(api_key=API_KEY)
    Model = getattr(genai, "GenerativeModel")
    default_name = "gemini-2.5-flash"
    try_name = model_name or default_name
    model = Model(try_name)
    # Quick sanity ping; if it fails and not default, fallback.
    try:
        _ = model.generate_content("ping")
    except Exception:
        if try_name != default_name:
            try:
                model = Model(default_name)
            except Exception:
                pass
    return model


def _clean_source_text(model, text: str, prompts: dict) -> str:
    tpl = prompts.get("clean_template") or (
        "\nYour task is to clean a raw Arabic transcript for a YouTube script.\n\nCRITICAL RULES FOR CLEANING:\n1. Remove all introductory and credit-related text (production/company/publisher/CTA/etc.).\n2. Start directly with the book's main content or author's introduction.\n3. Keep tone simple and conversational.\n4. Output ONLY the core content in Arabic.\n5. Do not translate or summarize.\n\nArabic Text:\n{text}\n"
    )
    prompt = _fmt(tpl, text=text)
    return _gen(model, prompt)


def _clean_english_transcript(model, text: str, prompts: dict) -> str:
    """
    Clean English transcript (remove intro/outro, fix typos).
    Used when source video is already in English.
    """
    tpl = prompts.get("clean_english_template") or (
        "\nYour task is to clean a raw English transcript from YouTube.\n\nCRITICAL RULES:\n1. Remove ALL intro/outro (channel promotions, subscribe requests, credits).\n2. Start directly with the book's main content.\n3. Fix obvious auto-transcription errors and typos.\n4. Remove repeated sentences or filler.\n5. Do NOT translate, summarize, or add new content.\n6. Output ONLY the core book content in English.\n\nEnglish Transcript:\n{text}\n"
    )
    prompt = _fmt(tpl, text=text)
    return _gen(model, prompt)


def _translate_to_english(model, text: str, prompts: dict) -> str:
    tpl = prompts.get("translate_template") or (
        "\nTranslate the following Arabic text into fluent, natural English.\n\nSTRICT RULES:\n- Preserve ALL details, events, and examples exactly as in the Arabic.\n- Keep rhetorical and motivational style.\n- Do NOT add, omit, or summarize.\n- Output only the full English translation.\n\nArabic Text:\n{text}\n"
    )
    prompt = _fmt(tpl, text=text)
    return _gen(model, prompt)


def _get_official_book_name(model, arabic_text: str, prompts: dict) -> Tuple[Optional[str], Optional[str]]:
    tpl = prompts.get("book_meta_template") or (
        "\nExtract the official English book title and author for the mentioned book.\nReturn JSON only: {\"book_name\":\"<English Name>\",\"author_name\":\"<English Author>\"}\n\nText:\n{arabic_text}\n"
    )
    prompt = _fmt(tpl, arabic_text=arabic_text)
    raw = _gen(model, prompt, mime_type="application/json")
    try:
        data = json.loads(raw)
        return data.get("book_name"), data.get("author_name")
    except Exception:
        return None, None


def _get_book_playlist(model, book_name: str, author_name: Optional[str], prompts: dict) -> Optional[str]:
    """
    Classify book into a YouTube playlist category.
    Returns one of the predefined playlist names.
    """
    tpl = prompts.get("book_playlist_template") or (
        "Classify the following book into ONE of these categories:\n\n"
        "1. Self-Development\n"
        "2. Philosophy & Thought\n"
        "3. Business & Finance\n"
        "4. Psychology\n"
        "5. Literary Novels\n"
        "6. Spirituality\n"
        "7. History & Biographies\n"
        "8. Science & Knowledge\n"
        "9. Culture & Society\n"
        "10. Quotes & Reflections\n\n"
        "Book: {book_name} by {author_name}\n\n"
        "Return ONLY the category name (exactly as written above), nothing else."
    )
    prompt = _fmt(tpl, book_name=book_name, author_name=author_name or "Unknown")
    raw = _gen(model, prompt)

    # Clean and validate the response
    category = raw.strip()

    # List of valid playlists
    valid_playlists = [
        "Self-Development",
        "Philosophy & Thought",
        "Business & Finance",
        "Psychology",
        "Literary Novels",
        "Spirituality",
        "History & Biographies",
        "Science & Knowledge",
        "Culture & Society",
        "Quotes & Reflections"
    ]

    # Check if response matches any valid playlist (case-insensitive)
    for playlist in valid_playlists:
        if category.lower() == playlist.lower():
            return playlist

    # If no match, try to find partial match
    for playlist in valid_playlists:
        if playlist.lower() in category.lower() or category.lower() in playlist.lower():
            return playlist

    # Default fallback
    print(f"[Playlist] Warning: Could not classify '{book_name}', defaulting to Self-Development")
    return "Self-Development"


def _generate_titles(model, book_name: str, prompts: dict) -> Optional[dict]:
    tpl = prompts.get("titles_template") or (
        "\nGenerate JSON with these keys:\n- main_title: Must be exactly the English name of the book ({book_name}), unchanged.\n- subtitle: Creative subtitle in English, max 3 words only.\n- footer: Engaging footer in English, must be 4 or 5 words.\n\nReturn ONLY valid JSON.\n"
    )
    prompt = _fmt(tpl, book_name=book_name)
    raw = _gen(model, prompt, mime_type="application/json")
    try:
        data = json.loads(raw)
        return data
    except Exception as e:
        print("Failed to parse titles JSON:", e, "Raw:", raw)
        return None




def _get_random_user_agent() -> str:
    """الحصول على User Agent عشوائي لتجنب الحظر"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    return random.choice(user_agents)


def _get_book_cover_from_amazon(title: str, author: Optional[str]) -> Optional[str]:
    """
    البحث عن غلاف الكتاب في Amazon وإرجاع رابط الصورة.
    يبحث باسم الكتاب + اسم الكاتب (إنجليزي فقط).
    يختار الطبعة الأعلى تقييماً من أول 5 نتائج.
    
    Args:
        title: اسم الكتاب (بالإنجليزية)
        author: اسم الكاتب (بالإنجليزية، اختياري)
    
    Returns:
        رابط صورة الغلاف إذا نجح، None إذا فشل
    """
    try:
        import urllib.parse
        
        # بناء استعلام البحث
        query = f"{title} {author}" if author else title
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.amazon.com/s?k={encoded_query}&i=stripbooks&s=relevancerank"
        
        print(f"[Amazon] البحث عن: {query}")
        
        # إعداد headers أقوى (تقليد متصفح حقيقي)
        headers = {
            'User-Agent': _get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        
        # محاولة مع retry (3 محاولات)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # تأخير عشوائي أطول بين المحاولات
                if attempt > 0:
                    delay = random.uniform(5.0, 10.0) * (attempt + 1)
                    print(f"[Amazon] محاولة {attempt + 1}/{max_retries} بعد {delay:.1f} ثانية...")
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(2.0, 4.0))
                
                # إرسال الطلب
                response = requests.get(search_url, headers=headers, timeout=20)
                response.raise_for_status()
                break  # نجح، اخرج من loop
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [503, 403]:
                    if attempt < max_retries - 1:
                        print(f"[Amazon] ⚠️ تم حظر الطلب ({e.response.status_code}), إعادة المحاولة...")
                        continue
                    else:
                        print(f"[Amazon] ❌ تم حظر الطلب ({e.response.status_code}) بعد {max_retries} محاولات")
                        return None
                raise
        else:
            print("[Amazon] ❌ فشلت جميع المحاولات")
            return None
        
        # تحليل HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # البحث عن نتائج البحث
        search_results = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        if not search_results:
            # احتياطي: استخدام selector أبسط
            print("[Amazon] لم يتم العثور على نتائج منظمة، محاولة طريقة احتياطية...")
            product_img = soup.find('img', class_='s-image')
            if product_img and product_img.get('src'):
                cover_img = str(product_img['src'])
                # تحسين جودة الصورة
                cover_img = re.sub(r'_AC_U[XY]\d+_', '_AC_UL600_', cover_img)
                print(f"[Amazon] ✅ تم العثور على الغلاف (طريقة احتياطية)")
                return cover_img
            print("[Amazon] ❌ لم يتم العثور على غلاف")
            return None
        
        print(f"[Amazon] تم العثور على {len(search_results)} نتيجة، جاري التحليل...")
        
        # تحليل أول 5 نتائج لإيجاد الأعلى تقييماً
        best_result = None
        best_score = -1
        
        for idx, result in enumerate(search_results[:5]):
            # استخراج التقييم
            rating_elem = result.find('span', class_='a-icon-alt')
            rating = 0.0
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # استخراج عدد المراجعات
            review_count_elem = result.find('span', {'aria-label': re.compile(r'\d+')})
            review_count = 0
            if review_count_elem:
                review_text = review_count_elem.get('aria-label')
                if review_text and isinstance(review_text, str):
                    review_match = re.search(r'(\d+)', review_text.replace(',', ''))
                    if review_match:
                        review_count = int(review_match.group(1))
            
            # حساب النقاط: الموقع (50-10) + التقييم (×10) + المراجعات (÷100، حد أقصى 10)
            position_score = (5 - idx) * 10
            rating_score = rating * 10
            review_score = min(review_count / 100, 10)
            total_score = position_score + rating_score + review_score
            
            print(f"[Amazon]   النتيجة {idx+1}: تقييم={rating}, مراجعات={review_count}, نقاط={total_score:.1f}")
            
            if total_score > best_score:
                best_score = total_score
                best_result = result
        
        # استخراج الصورة من أفضل نتيجة
        if best_result:
            img_tag = best_result.find('img', class_='s-image')
            if img_tag and img_tag.get('src'):
                cover_img = str(img_tag['src'])
                # تحسين جودة الصورة
                cover_img = re.sub(r'_AC_U[XY]\d+_', '_AC_UL600_', cover_img)
                print(f"[Amazon] ✅ تم العثور على الغلاف الأعلى تقييماً")
                return cover_img
        
        print("[Amazon] ❌ لم يتم العثور على غلاف مناسب")
        return None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            print(f"[Amazon] ❌ تم حظر الطلب (503 Service Unavailable)")
        elif e.response.status_code == 403:
            print(f"[Amazon] ❌ تم حظر الطلب (403 Forbidden)")
        else:
            print(f"[Amazon] ❌ خطأ HTTP: {e.response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Amazon] ❌ خطأ في الشبكة: {str(e)}")
        return None
    except Exception as e:
        print(f"[Amazon] ❌ خطأ في التحليل: {str(e)}")
        return None


def _get_book_cover(title: str, author: Optional[str], model=None) -> Optional[str]:
    """
    البحث عن غلاف الكتاب باستخدام Amazon.
    يبحث باسم الكتاب + اسم الكاتب (إنجليزي فقط).
    يختار الطبعة الأعلى تقييماً.
    
    Args:
        title: Book title (English)
        author: Book author (English, optional)
        model: Unused (kept for compatibility)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    if author:
        print(f"[Cover] البحث عن غلاف: {title} - {author}")
    else:
        print(f"[Cover] البحث عن غلاف: {title}")

    # استخدام Amazon للبحث
    url = _get_book_cover_from_amazon(title, author)
    
    if url:
        print(f"[Cover] ✅ تم العثور على الغلاف من Amazon")
        return url
    
    print("[Cover] ❌ لم يتم العثور على غلاف")
    return None


def _scriptify_youtube(model, english_text: str, prompts: dict) -> str:
    tpl = prompts.get("youtube_script_template")
    if isinstance(tpl, list):
        tpl = "\n".join(tpl)
    if not tpl:
        # fallback safe prompt
        tpl = (
            "Rewrite the following English narration into a polished YouTube script with:\n"
            "- engaging, conversational style\n"
            "- short paragraphs (2–3 sentences)\n"
            "- concise sentences for voice narration\n"
            "- strong hook at the start and simple closing line\n\n"
            "English Text:\n{text}\n"
        )
    prompt = _fmt(tpl, text=english_text)
    return _gen(model, prompt)


def cover_only(config_dir: Path, output_titles: Path) -> Optional[str]:
    """Update cover image and settings using existing titles JSON.

    This avoids running the LLM steps and only performs the cover lookup and
    settings update, honoring prefer_local_cover.
    Returns the chosen cover URL or local path if downloaded.
    """
    # Configure Gemini model for smart cover lookup
    model = _configure_model(config_dir)
    
    try:
        titles = json.loads(Path(output_titles).read_text(encoding="utf-8"))
    except Exception as e:
        print("Failed to read titles JSON:", e)
        return None

    cover_title = titles.get("main_title") or titles.get("book_name")
    cover_author = titles.get("author_name")
    if not cover_title:
        print("No main_title found in titles JSON; cannot look up cover.")
        return None

    cover_url = _get_book_cover(str(cover_title), str(cover_author) if cover_author else None, model=model)

    # Read optional preference from settings.json
    prefer_local = True
    try:
        cfg_path = Path(config_dir) / "settings.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            val = cfg.get("prefer_local_cover")
            if isinstance(val, bool):
                prefer_local = val
    except Exception:
        pass

    cover_local: Optional[str] = None
    if cover_url and prefer_local:
        try:
            run_root = Path(output_titles).resolve().parent
            downloaded = _download_cover_to_local(cover_url, run_root, name_hint=str(cover_title), force_name="bookcover")
            if downloaded and downloaded.exists():
                cover_local = str(downloaded)
        except Exception as e:
            print("Local cover preparation failed:", e)

    _update_settings(config_dir, titles, cover_local or cover_url)

    return cover_local or cover_url


def _update_settings(config_dir: Path, titles: dict, cover_url: Optional[str]) -> None:
    settings_path = Path(config_dir) / "settings.json"
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            settings = {}

    # No auto-trimming for now (use full text as returned by the model)
    settings["main_title"] = titles.get("main_title", "")
    settings["subtitle"] = titles.get("subtitle", "")
    settings["footer"] = titles.get("footer", "")
    if cover_url:
        settings["cover_image"] = cover_url

    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def _sanitize_for_filename(s: str, max_len: int = 80) -> str:
    s = s or "cover"
    s = re.sub(r"[\\/:*?\"<>|]+", "-", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s or "cover"


def _download_cover_to_local(url: str, dest_dir: Path, name_hint: Optional[str] = None, force_name: Optional[str] = None) -> Optional[Path]:
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        base = _sanitize_for_filename(force_name or name_hint or "cover")
        ext = ".jpg"
        # naive extension guess from URL
        m = re.search(r"\.(jpg|jpeg|png|webp)(?:\?|#|$)", url, re.IGNORECASE)
        if m:
            ext = "." + m.group(1).lower()
        out_path = dest_dir / f"{base}{ext}"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path
    except Exception as e:
        print("Cover download failed:", e)
        return None


def main(transcript_path: Path, config_dir: Path, output_text: Path, output_titles: Path) -> Optional[str]:
    model = _configure_model(config_dir)
    if not model:
        return None
    prompts = _load_prompts(config_dir)

    # Load detected language from search stage
    run_dir = Path(transcript_path).parent
    detected_lang = _load_detected_language(run_dir)
    print(f"[Process] Detected language: {detected_lang}")

    text = Path(transcript_path).read_text(encoding="utf-8")

    # Stage 1: Cleaning (language-specific)
    print("Cleaning transcript...")
    if detected_lang == "ar":
        cleaned = _clean_source_text(model, text, prompts)
    else:
        cleaned = _clean_english_transcript(model, text, prompts)
    
    if not cleaned:
        return None

    # Stage 2: Translation (skip for English!)
    if detected_lang == "ar":
        print("Translating to English...")
        english = _translate_to_english(model, cleaned, prompts)
        if not english:
            return None
    else:
        print("⏭️  Skipping translation (source is already in English)")
        english = cleaned  # Already clean English text

    # Optional third stage: YouTube Scriptify
    enable_scriptify = True
    try:
        cfg_path = Path(config_dir) / "settings.json"
        if cfg_path.exists():
            cfg2 = json.loads(cfg_path.read_text(encoding="utf-8"))
            v = cfg2.get("enable_scriptify")
            if isinstance(v, bool):
                enable_scriptify = v
    except Exception:
        pass

    scriptified: Optional[str] = None
    if enable_scriptify:
        print("Scriptifying for YouTube style...")
        scriptified = _scriptify_youtube(model, english, prompts)
        if not scriptified:
            # if model didn't return, fall back to english
            scriptified = english

    print("Extracting official book name...")
    # Check if book metadata already exists in output.titles.json (from Stage 0)
    existing_book_name = None
    existing_author_name = None
    if output_titles and Path(output_titles).exists():
        try:
            existing_data = json.loads(Path(output_titles).read_text(encoding="utf-8"))
            existing_book_name = existing_data.get("main_title")
            existing_author_name = existing_data.get("author_name")
            if existing_book_name:
                print(f"✅ Using existing book metadata from output.titles.json")
                print(f"   Book: {existing_book_name}")
                print(f"   Author: {existing_author_name or 'Unknown'}")
        except Exception:
            pass

    # If not found in existing file, extract from transcript
    if not existing_book_name:
        book_name, author_name = _get_official_book_name(model, text, prompts)
        if not book_name:
            return None
    else:
        book_name = existing_book_name
        author_name = existing_author_name

    print("Generating titles...")
    titles = _generate_titles(model, book_name, prompts)
    if not titles:
        return None

    # Ensure author_name is stored in output.titles.json right after main_title
    try:
        new_titles = {}
        # main_title first (fallback to detected book_name if missing)
        mt = titles.get("main_title") or book_name
        if mt is not None:
            new_titles["main_title"] = mt
        # then author_name if available
        if author_name:
            new_titles["author_name"] = author_name
        # then the common fields in desired order
        for k in ("subtitle", "footer"):
            v = titles.get(k)
            if v is not None:
                new_titles[k] = v
        # finally, preserve any extra keys returned by the model that weren't added yet
        for k, v in titles.items():
            if k not in new_titles:
                new_titles[k] = v
        titles = new_titles
    except Exception:
        # if anything goes wrong, proceed with original titles dict
        pass


    print("Fetching cover image...")
    # Prefer names from the titles JSON (output.titles.json) for cover lookup
    cover_title = titles.get("main_title") or book_name
    cover_author = titles.get("author_name") or author_name
    cover_url = _get_book_cover(cover_title, cover_author, model=model)

    # Read optional preference from settings.json
    prefer_local = True
    try:
        cfg_path = Path(config_dir) / "settings.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            val = cfg.get("prefer_local_cover")
            if isinstance(val, bool):
                prefer_local = val
    except Exception:
        pass

    # Optionally download to local to avoid network flakiness during render
    cover_local: Optional[str] = None
    if cover_url and prefer_local:
        try:
            # infer run root from output paths (flattened): parent directory of output files
            run_root = Path(output_titles).resolve().parent
            # Download cover image directly into the run root (no subfolders) under standardized name 'bookcover'
            downloaded = _download_cover_to_local(cover_url, run_root, name_hint=cover_title, force_name="bookcover")
            if downloaded and downloaded.exists():
                cover_local = str(downloaded)
        except Exception as e:
            print("Local cover preparation failed:", e)

    _update_settings(config_dir, titles, cover_local or cover_url)

    output_titles.parent.mkdir(parents=True, exist_ok=True)
    output_text.parent.mkdir(parents=True, exist_ok=True)
    output_titles.write_text(json.dumps(titles, ensure_ascii=False), encoding="utf-8")
    # Standardize processed English text filename to translate.txt
    try:
        run_root = Path(output_titles).resolve().parent
        std_translate = run_root / "translate.txt"
        std_translate.write_text(english, encoding="utf-8")
        output_text_path = std_translate
    except Exception:
        # Fallback to provided output_text path
        output_text.write_text(english, encoding="utf-8")
        output_text_path = output_text
    # If scriptify is enabled, also write script.txt and return it as the main artifact for TTS
    if enable_scriptify:
        try:
            run_root = Path(output_titles).resolve().parent
            std_script = run_root / "script.txt"
            std_script.write_text(scriptified or english, encoding="utf-8")
            output_text_path = std_script
        except Exception:
            pass

    return str(output_text_path)
