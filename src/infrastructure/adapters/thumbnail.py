from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import json
import os
import re


SIZE = (1920, 1080)  # Full HD 16:9 thumbnail (YouTube max recommended)


def _load_titles(titles_json: Path, debug: bool = False) -> dict:
    """
    Load titles from JSON file with validation and fallback.

    CRITICAL FIX: Validates required fields with smart fallbacks.
    """
    try:
        data = json.loads(Path(titles_json).read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("titles.json is not a dictionary")

        # Check for thumbnail-specific fields first
        has_thumbnail_title = data.get("thumbnail_title") and data["thumbnail_title"].strip()
        has_thumbnail_subtitle = data.get("thumbnail_subtitle") and data["thumbnail_subtitle"].strip()

        # Fallback logic for missing thumbnail fields
        if not has_thumbnail_title:
            # Try legacy keys first
            if data.get("hook thumbanil"):
                data["thumbnail_title"] = data["hook thumbanil"]
                has_thumbnail_title = True
            # Fallback to main_title or youtube_title
            elif data.get("main_title"):
                data["thumbnail_title"] = data["main_title"]
                has_thumbnail_title = True
                if debug:
                    print(f"[thumb] ⚠️ Using main_title as thumbnail_title fallback")
            elif data.get("youtube_title"):
                # Extract first 5-6 words from YouTube title as hook
                title_words = data["youtube_title"].split()[:6]
                data["thumbnail_title"] = " ".join(title_words)
                has_thumbnail_title = True
                if debug:
                    print(f"[thumb] ⚠️ Using youtube_title as thumbnail_title fallback")

        if not has_thumbnail_subtitle:
            # Try legacy keys first
            if data.get("sub hook thumbanil"):
                data["thumbnail_subtitle"] = data["sub hook thumbanil"]
                has_thumbnail_subtitle = True
            # Fallback to subtitle or author_name
            elif data.get("subtitle"):
                data["thumbnail_subtitle"] = data["subtitle"]
                has_thumbnail_subtitle = True
                if debug:
                    print(f"[thumb] ⚠️ Using subtitle as thumbnail_subtitle fallback")
            elif data.get("author_name"):
                data["thumbnail_subtitle"] = f"by {data['author_name']}"
                has_thumbnail_subtitle = True
                if debug:
                    print(f"[thumb] ⚠️ Using author_name as thumbnail_subtitle fallback")
            else:
                # Last resort: use generic subtitle
                data["thumbnail_subtitle"] = "Book Summary"
                has_thumbnail_subtitle = True
                if debug:
                    print(f"[thumb] ⚠️ Using generic 'Book Summary' as thumbnail_subtitle fallback")

        # Final validation after fallbacks
        if not has_thumbnail_title or not has_thumbnail_subtitle:
            missing = []
            if not has_thumbnail_title:
                missing.append("thumbnail_title")
            if not has_thumbnail_subtitle:
                missing.append("thumbnail_subtitle")
            raise ValueError(f"Missing required fields in titles.json even after fallbacks: {missing}")

        if debug:
            print(f"[thumb] ✅ Loaded titles with all required fields")
            print(f"[thumb]   Title: {data.get('thumbnail_title')}")
            print(f"[thumb]   Subtitle: {data.get('thumbnail_subtitle')}")

        return data

    except Exception as e:
        error_msg = f"[thumb] ❌ Failed to load/validate titles.json: {e}"
        if debug:
            print(error_msg)
        # CRITICAL: Raise exception instead of returning empty dict
        # This ensures thumbnail generation fails loudly instead of silently
        raise RuntimeError(error_msg) from e


def _find_cover(run_dir: Path, debug: bool = False) -> Optional[Path]:
    candidates = [
        run_dir / "cover_processed.jpg",
        run_dir / "bookcover.jpg",
        run_dir / "bookcover.jpeg",
        run_dir / "bookcover.png",
    ]
    for p in candidates:
        try:
            if p.exists() and p.stat().st_size > 0:
                if debug:
                    print("[thumb] using cover:", p.name)
                return p
        except Exception:
            pass
    if debug:
        print("[thumb] no cover image found; using gradient background")
    return None


def _try_fonts() -> List[Path]:
    # Common Windows fonts (bolds first)
    win_fonts = [
        Path("C:/Windows/Fonts/Impact.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf"),  # Segoe UI Semibold
        Path("C:/Windows/Fonts/seguiemj.ttf"),
        Path("C:/Windows/Fonts/SegoeUI-Bold.ttf"),
        Path("C:/Windows/Fonts/Tahoma.ttf"),
    ]
    # Fallbacks (Linux/Mac paths just in case)
    fallbacks = [
        Path("/System/Library/Fonts/Supplemental/Impact.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    return [p for p in (win_fonts + fallbacks) if p.exists()]

def _bebas_neue_candidates(weight: str = "bold") -> List[Path]:
    """
    Search for Bebas Neue font - modern, condensed, all-caps display font.
    Perfect for bold, impactful thumbnail titles.
    FORCED: Always use BebasNeue-Regular.ttf as first priority.
    """
    # Always prioritize BebasNeue-Regular.ttf first
    names_by_weight = {
        "bold": [
            "BebasNeue-Regular.ttf",  # FORCED: Primary choice
            "BebasNeue-Bold.ttf",
            "BebasNeueBold.ttf",
            "Bebas-Neue-Bold.ttf",
            "BebasNeue.ttf",
        ],
        "regular": [
            "BebasNeue-Regular.ttf",  # FORCED: Primary choice
            "BebasNeue.ttf",
            "Bebas-Neue.ttf",
            "BebasNeue-Bold.ttf",
        ],
        "light": [
            "BebasNeue-Regular.ttf",  # FORCED: Primary choice
            "BebasNeue-Light.ttf",
            "BebasNeueLight.ttf",
        ],
    }
    weight = weight.lower()
    if weight == "bold":
        order = names_by_weight.get("bold", []) + names_by_weight.get("regular", [])
    elif weight == "light":
        order = names_by_weight.get("light", []) + names_by_weight.get("regular", [])
    else:
        order = names_by_weight.get("regular", []) + names_by_weight.get("bold", [])

    roots = [
        Path("assets/fonts"),
        Path("secrets/fonts"),
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
    ]
    cands: List[Path] = []
    for r in roots:
        for nm in order:
            p = r / nm
            try:
                if p.exists():
                    cands.append(p)
            except Exception:
                pass
    return cands


def _cairo_candidates(weight: str = "bold") -> List[Path]:
    """
    Search for Cairo font - Modern Arabic/Latin typeface with excellent readability.
    Perfect for bilingual thumbnails and Arabic-friendly designs.
    """
    names_by_weight = {
        "bold": [
            "Cairo-Bold.ttf",
            "CairoBold.ttf",
            "Cairo-ExtraBold.ttf",
            "CairoExtraBold.ttf",
            "Cairo-SemiBold.ttf",
            "CairoSemiBold.ttf",
            "Cairo-Regular.ttf",
        ],
        "semibold": [
            "Cairo-SemiBold.ttf",
            "CairoSemiBold.ttf",
            "Cairo-Bold.ttf",
            "Cairo-Regular.ttf",
        ],
        "regular": [
            "Cairo-Regular.ttf",
            "Cairo.ttf",
            "Cairo-SemiBold.ttf",
        ],
        "light": [
            "Cairo-Light.ttf",
            "CairoLight.ttf",
            "Cairo-Regular.ttf",
        ],
    }
    weight = weight.lower()
    if weight == "bold":
        order = names_by_weight.get("bold", []) + names_by_weight.get("semibold", [])
    elif weight == "semibold":
        order = names_by_weight.get("semibold", []) + names_by_weight.get("bold", [])
    elif weight == "light":
        order = names_by_weight.get("light", []) + names_by_weight.get("regular", [])
    else:
        order = names_by_weight.get("regular", []) + names_by_weight.get("semibold", [])

    roots = [
        Path("assets/fonts"),
        Path("secrets/fonts"),
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
    ]
    cands: List[Path] = []
    for r in roots:
        try:
            if not r.exists():
                continue
            for name in order:
                p = r / name
                if p.exists() and p not in cands:
                    cands.append(p)
            # Generic search for any Cairo variant
            for p in r.glob("Cairo*.ttf"):
                if p not in cands:
                    cands.append(p)
            for p in r.glob("cairo*.ttf"):
                if p not in cands:
                    cands.append(p)
        except Exception:
            pass
    return cands


def _impact_candidates(weight: str = "bold") -> List[Path]:
    """
    Search for Impact font - Bold, condensed display font.
    Perfect for powerful, attention-grabbing thumbnail titles.
    """
    # Impact typically comes in one weight (bold by default)
    names = [
        "Impact.ttf",
        "impact.ttf",
        "IMPACT.TTF",
    ]
    
    roots = [
        Path("assets/fonts"),
        Path("secrets/fonts"),
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
    ]
    cands: List[Path] = []
    for r in roots:
        try:
            if not r.exists():
                continue
            for name in names:
                p = r / name
                if p.exists() and p not in cands:
                    cands.append(p)
            # Generic search for any Impact variant
            for p in r.glob("*mpact*.ttf"):
                if p not in cands:
                    cands.append(p)
        except Exception:
            pass
    return cands

def _get_smart_text_color(background_rgb: Tuple[int, int, int], debug: bool = False) -> Tuple[int, int, int]:
    """
    Advanced text color selection with wide range of colors.
    Analyzes background and returns best contrasting color from palette.

    Args:
        background_rgb: Background color as (R, G, B)
        debug: Print analysis if True

    Returns:
        Optimal text color from expanded palette
    """
    r, g, b = background_rgb

    # Calculate luminance
    def get_luminance(rgb):
        def linearize(c):
            c = c / 255.0
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    bg_luminance = get_luminance(background_rgb)

    # Expanded color palette with more options
    color_palette = {
        # Neutrals
        "pure_white": (255, 255, 255),
        "off_white": (245, 245, 245),
        "light_gray": (220, 220, 220),
        "medium_gray": (180, 180, 180),
        "dark_gray": (80, 80, 80),
        "charcoal": (40, 40, 40),
        "pure_black": (0, 0, 0),

        # Warm lights
        "cream": (255, 253, 240),
        "light_gold": (255, 240, 200),
        "soft_peach": (255, 220, 200),

        # Cool lights
        "ice_blue": (230, 240, 255),
        "mint": (240, 255, 245),
        "lavender": (240, 230, 255),

        # Vibrant lights (for dark backgrounds)
        "bright_cyan": (100, 255, 255),
        "bright_yellow": (255, 255, 100),
        "bright_lime": (200, 255, 100),

        # Deep darks (for light backgrounds)
        "deep_navy": (0, 20, 50),
        "deep_purple": (40, 0, 60),
        "deep_brown": (50, 25, 0),
    }

    # Calculate contrast for each color
    def calc_contrast(color1, color2):
        l1 = get_luminance(color1)
        l2 = get_luminance(color2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    best_color = (255, 255, 255)
    best_contrast = 0
    best_name = "white"

    # Find color with best contrast
    for name, color in color_palette.items():
        contrast = calc_contrast(background_rgb, color)
        if contrast > best_contrast:
            best_contrast = contrast
            best_color = color
            best_name = name

    if debug:
        print(f"[thumb] background luminance: {bg_luminance:.3f}")
        print(f"[thumb] → {best_name.upper()} RGB{best_color} (contrast: {best_contrast:.2f}:1)")

    return best_color


def _calculate_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Args:
        color1: First color as (R, G, B)
        color2: Second color as (R, G, B)

    Returns:
        Contrast ratio from 1:1 (no contrast) to 21:1 (maximum contrast)
        WCAG standards: AA normal ≥4.5:1, AA large ≥3:1, AAA normal ≥7:1
    """
    def get_luminance(rgb):
        def linearize(c):
            c = c / 255.0
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4

        r, g, b = rgb
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    l1 = get_luminance(color1)
    l2 = get_luminance(color2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def _load_font(size: int, candidates: Optional[List[Path]] = None, strict: bool = False, role: str = "font", debug: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    search_list: List[Path] = []
    if candidates:
        search_list.extend(candidates)
    if not strict:
        # fallback to general fonts list in non-strict mode
        search_list.extend(_try_fonts())
    last_err: Optional[Exception] = None
    for p in search_list:
        try:
            font = ImageFont.truetype(str(p), size=size)
            if debug:
                print(f"[thumb] loaded {role}: {p.name} (size={size}px)")
            return font
        except Exception as e:
            last_err = e
            continue
    if strict:
        # Build a helpful error message in Arabic indicating how to fix
        details = f"لم يتم العثور على {role}. الرجاء تثبيت الخط المطلوب على Windows (C:/Windows/Fonts) أو تمرير المسار عبر --{ 'title-font' if role=='title' else 'sub-font' } أو المتغيرات البيئية THUMBNAIL_TITLE_FONT/THUMBNAIL_SUB_FONT."
        raise FileNotFoundError(details) from last_err
    if debug:
        print(f"[thumb] {role}: falling back to default font")
    return ImageFont.load_default()


def _wrap_text(text: str, font: Any, max_width: int, max_lines: int = 3) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    cur = []
    for w in words:
        test = (" ".join(cur + [w])).strip()
        wlen = font.getlength(test) if hasattr(font, "getlength") else font.getbbox(test)[2]
        if wlen <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            if len(lines) >= max_lines - 1:
                break
    if cur and len(lines) < max_lines:
        lines.append(" ".join(cur))
    # Ellipsis if overflow
    if len(lines) >= max_lines and (len(words) > len(" ".join(lines).split())):
        last = lines[-1]
        while last and (font.getlength(last + "…") if hasattr(font, "getlength") else font.getbbox(last + "…")[2]) > max_width:
            last = last[:-1]
        lines[-1] = (last.strip() + "…") if last else "…"
    return lines


def _word_count(text: str) -> int:
    try:
        # Split on whitespace; filter out empty tokens
        return len([w for w in str(text).strip().split() if w])
    except Exception:
        return 0


def _avg_word_length(text: str) -> float:
    try:
        words = [w for w in str(text).strip().split() if w]
        if not words:
            return 0.0
        return sum(len(w) for w in words) / len(words)
    except Exception:
        return 0.0


def _total_char_count(text: str) -> int:
    try:
        # Count non-space characters
        return len([c for c in str(text) if not c.isspace()])
    except Exception:
        return 0


def _load_font_profile(font_name: str, config_dir: Path = Path("config")) -> dict:
    """
    Load font-specific sizing profile from settings.json.
    Each font can have its own dynamic sizing parameters.
    
    Returns default Bebas Neue profile if font not found or error occurs.
    """
    default_profile = {
        "title_base_size": 135,
        "title_min_size": 60,
        "title_max_size": 220,
        "subtitle_base_size": 80,
        "subtitle_min_size": 65,
        "subtitle_ratio": 0.70,
        "dynamic_scaling": {
            "2_words": 1.8,
            "3_words_long": 0.9,
            "3_words_medium": 1.2,
            "3_words_short": 1.5,
            "4_words": 1.1,
            "5_words": 1.0,
            "6_words": 0.95,
            "decay_rate": 0.92
        }
    }
    
    try:
        settings_path = config_dir / "settings.json"
        if not settings_path.exists():
            return default_profile
        
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        profiles = settings.get("thumbnail_font_profiles", {})
        
        # Return profile for requested font, or default
        return profiles.get(font_name, default_profile)
    except Exception:
        return default_profile


def _calculate_optimal_title_size(
    text: str, 
    font_profile: dict,
    max_width: int = 700
) -> int:
    """
    Advanced geometric calculation for optimal title size with maximum dynamics.
    Uses text density, word distribution, and golden ratio for perfect balance.
    
    NOW FONT-SPECIFIC: Each font (Bebas Neue, Cairo, etc.) has its own sizing logic!
    """
    base_size = font_profile.get("title_base_size", 135)
    min_size = font_profile.get("title_min_size", 60)
    max_size = font_profile.get("title_max_size", 220)
    scaling = font_profile.get("dynamic_scaling", {})
    
    word_count = _word_count(text)
    char_count = _total_char_count(text)
    avg_word_len = _avg_word_length(text)

    if word_count == 0 or char_count == 0:
        return base_size

    # Calculate text density (characters per word)
    density = char_count / word_count

    # Golden ratio for aesthetic scaling
    golden_ratio = 1.618

    # Base size using geometric scaling
    # Size inversely proportional to density and word count
    geometric_factor = max_width / (density * avg_word_len * word_count ** 0.5)
    size = base_size * geometric_factor * 0.075  # Increased from 0.070 to 0.075 for slightly bigger sizes

    # Word count adjustments with exponential decay - FONT-SPECIFIC!
    if word_count <= 2:
        size *= scaling.get("2_words", 1.6)
    elif word_count == 3:
        if avg_word_len > 7:
            size *= scaling.get("3_words_long", 2.0)  # Increased from 1.8 to 2.0
        elif avg_word_len > 5:
            size *= scaling.get("3_words_medium", 1.9)  # Increased from 1.7 to 1.9
        else:
            size *= scaling.get("3_words_short", 1.1)  # Keep small for short words
    elif word_count == 4:
        size *= scaling.get("4_words", 1.7)
    elif word_count == 5:
        size *= scaling.get("5_words", 1.0)
    elif word_count == 6:
        size *= scaling.get("6_words", 0.95)
    else:
        # Exponential decay for long titles - FONT-SPECIFIC decay rate!
        decay_rate = scaling.get("decay_rate", 0.92)
        decay = decay_rate ** (word_count - 6)
        size *= decay

    # Character count fine-tuning with logarithmic scaling
    if char_count > 60:
        size *= 0.85
    elif char_count > 50:
        size *= 0.9
    elif char_count > 40:
        size *= 0.95
    elif char_count < 20:
        size *= 1.1

    # Apply golden ratio for final aesthetic touch - MODIFIED to favor longer words
    # Don't divide by golden_ratio for already moderate sizes (allow bigger text)
    size = size / golden_ratio if size > 250 else size * golden_ratio * 0.8  # Changed threshold from 200 to 250

    # Ensure size is within FONT-SPECIFIC dynamic range
    return int(max(min_size, min(max_size, size)))


def _wrap_text_balanced(text: str, font: Any, max_width: int, max_lines: int = 3) -> List[str]:
    # Distribute words across up to max_lines to balance line widths by minimizing slack.
    words = [w for w in str(text).strip().split() if w]
    n = len(words)
    if n == 0:
        return []
    if n == 1:
        return [words[0]]
    # Cache segment width measurements
    width_cache: dict[tuple[int, int], int] = {}

    def segment_width(i: int, j: int) -> int:
        # width of words[i:j] joined by spaces; 0-indexed, j exclusive
        key = (i, j)
        if key in width_cache:
            return width_cache[key]
        s = " ".join(words[i:j])
        try:
            w = int(font.getlength(s)) if hasattr(font, "getlength") else int(font.getbbox(s)[2] - font.getbbox(s)[0])
        except Exception:
            w = len(s) * 20
        width_cache[key] = w
        return w

    INF = float('inf')
    # dp[i][k] = best cost to layout first i words into k lines (float cost)
    dp = [[INF] * (max_lines + 1) for _ in range(n + 1)]
    brk = [[-1] * (max_lines + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        for k in range(1, max_lines + 1):
            # try previous break at j
            jmin = max(0, k - 1)  # at least one word per line
            for j in range(jmin, i):
                w = segment_width(j, i)
                if w > max_width:
                    continue
                slack = max_width - w
                # Lower penalty for the last line to allow some raggedness
                is_last_line = (i == n)
                cost_line = (slack * slack) * (0.5 if is_last_line else 1.0)
                prev = dp[j][k - 1]
                if prev + cost_line < dp[i][k]:
                    dp[i][k] = prev + cost_line
                    brk[i][k] = j
    # Choose best k
    best_k = -1
    best_cost = INF
    for k in range(1, max_lines + 1):
        if dp[n][k] < best_cost:
            best_cost = dp[n][k]
            best_k = k
    if best_k == -1 or best_cost >= INF:
        # Fallback to greedy wrap (with built-in ellipsis behavior)
        return _wrap_text(text, font, max_width, max_lines=max_lines)
    # Reconstruct lines
    lines: List[str] = []
    i = n
    k = best_k
    while k > 0 and i > 0:
        j = brk[i][k]
        if j < 0:
            # Safety fallback
            return _wrap_text(text, font, max_width, max_lines=max_lines)
        lines.append(" ".join(words[j:i]))
        i = j
        k -= 1
    lines.reverse()
    return lines


def _draw_text_with_outline(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, font: Any, fill=(255, 255, 255), outline=(0, 0, 0), outline_width: int = 4):
    x, y = xy
    # Draw outline only if requested
    if outline_width and outline_width > 0:
        # Smooth outline using semi-transparent layers for softer anti-aliased effect
        outline_color = outline if isinstance(outline, tuple) and len(outline) >= 3 else (0, 0, 0)
        
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                # Use semi-transparent outline for smoother appearance
                if len(outline_color) == 4:
                    # Already has alpha
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
                else:
                    # Add alpha for smoothness (180 = ~70% opacity)
                    smooth_outline = (outline_color[0], outline_color[1], outline_color[2], 180)
                    draw.text((x + dx, y + dy), text, font=font, fill=smooth_outline)
    draw.text((x, y), text, font=font, fill=fill)


def _text_width(font: Any, text: str) -> int:
    try:
        if hasattr(font, "getlength"):
            return int(font.getlength(text))
        bbox = font.getbbox(text)
        return int(bbox[2] - bbox[0])
    except Exception:
        return int(len(text) * 20)


def _text_height(font: Any, text: str, fallback: int = 72) -> int:
    try:
        bbox = font.getbbox(text)
        return int(bbox[3] - bbox[1])
    except Exception:
        try:
            return int(getattr(font, "size", fallback))
        except Exception:
            return fallback


def _clean_thumbnail_text(text: str) -> str:
    """
    Clean thumbnail text by removing unwanted punctuation.
    Removes: commas, periods, semicolons, colons from the end of words/lines
    Preserves: question marks, exclamation marks, apostrophes, hyphens
    """
    if not text:
        return text

    # Remove trailing punctuation from the entire text
    text = text.strip()

    # Remove commas, periods, semicolons, colons
    # But keep question marks, exclamation marks
    unwanted_chars = [',', '.', ';', ':']

    # Remove these characters from anywhere in the text
    for char in unwanted_chars:
        text = text.replace(char, '')

    # Clean up multiple spaces
    import re
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def _get_average_color_in_area(image: Image.Image, x: int, y: int, width: int, height: int, sample_size: int = 50) -> Tuple[int, int, int]:
    """
    Calculate average color in a specific area of the image.
    Uses sampling for performance.

    Args:
        image: PIL Image
        x, y: Top-left corner of the area
        width, height: Dimensions of the area
        sample_size: Number of pixels to sample (higher = more accurate but slower)

    Returns:
        Average RGB color as (R, G, B)
    """
    try:
        # Ensure we're in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Crop to the area
        area = image.crop((x, y, x + width, y + height))

        # Sample pixels evenly across the area
        pixels = []
        step_x = max(1, area.width // int(sample_size ** 0.5))
        step_y = max(1, area.height // int(sample_size ** 0.5))

        for py in range(0, area.height, step_y):
            for px in range(0, area.width, step_x):
                try:
                    pixel = area.getpixel((px, py))
                    if isinstance(pixel, tuple) and len(pixel) >= 3:
                        pixels.append(pixel[:3])
                except Exception:
                    continue

        if not pixels:
            return (128, 128, 128)  # Default gray

        # Calculate average
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)

        return (avg_r, avg_g, avg_b)

    except Exception:
        return (128, 128, 128)  # Default gray on error


def _extract_accent_color_from_cover(cover_path: Path, debug: bool = False) -> Optional[Tuple[int, int, int]]:
    """
    Extract a vibrant accent color from the book cover image.
    Uses color clustering to find the most saturated, vibrant color.
    Returns RGB tuple or None if extraction fails.
    """
    try:
        from collections import Counter
        import colorsys

        # Open and resize cover for faster processing
        img = Image.open(cover_path).convert("RGB")
        img.thumbnail((200, 200))  # Reduce size for performance

        # Get all pixels
        pixels = list(img.getdata())

        # Filter out very dark, very light, gray colors, and whites
        vibrant_pixels = []
        for r, g, b in pixels:
            # Skip very dark (too close to black)
            if r < 30 and g < 30 and b < 30:
                continue
            # Skip whites and very light colors (more strict)
            # White = RGB(255,255,255), so reject anything close
            if r > 220 and g > 220 and b > 220:
                continue
            # Additional check: reject if average > 200 (catches off-whites)
            avg = (r + g + b) / 3
            if avg > 200:
                continue
            # Skip grays (low saturation)
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if s < 0.3:  # Low saturation = grayish
                continue
            # Keep vibrant colors
            vibrant_pixels.append((r, g, b))

        if not vibrant_pixels:
            if debug:
                print("[thumb] no vibrant colors found in cover, using default gold")
            return None

        # Find most common vibrant color
        color_counts = Counter(vibrant_pixels)
        most_common = color_counts.most_common(10)  # Top 10 colors

        # Pick the most saturated one from top candidates
        best_color = None
        best_saturation = 0
        for color, count in most_common:
            r, g, b = color
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            # Prefer colors with high saturation and reasonable brightness
            score = s * (0.3 + v * 0.7)  # Weight both saturation and brightness
            if score > best_saturation:
                best_saturation = score
                best_color = color

        if best_color and debug:
            print(f"[thumb] extracted accent color from cover: RGB{best_color}")

        return best_color

    except Exception as e:
        if debug:
            print(f"[thumb] failed to extract color from cover: {e}")
        return None


def generate_thumbnail(
    run_dir: Path,
    titles_json: Path,
    output_path: Optional[Path] = None,
    subtitle_gap: int = 110,  # Spacing between title and subtitle (reduced to 110px)
    title_line_gap: int = 40,
    background_dim: float = 0.45,
    title_font_size: int = 250,
    subtitle_font_size: int = 160,  # Doubled from 80
    icons_size: int = 28,
    icons_gap: int = 24,
    icons_row_gap: int = 36,
    title_font_path: Optional[Path] = None,
    sub_font_path: Optional[Path] = None,
    title_font_name: Optional[str] = "Bebas Neue",
    sub_font_name: Optional[str] = "Bebas Neue",
    strict_fonts: bool = True,
    dynamic_title_size: bool = True,
    subtitle_overlay: bool = False,
    subtitle_overlay_alpha: int = 170,
    subtitle_overlay_pad_x: int = 22,
    subtitle_overlay_pad_y: int = 12,
    subtitle_overlay_radius: int = 14,
    title_alpha: int = 255,
    subtitle_alpha: int = 255,
    title_color: Tuple[int, int, int] = (255, 255, 255),
    subtitle_color: Tuple[int, int, int] = (255, 215, 0),
    debug: bool = False,
    force_title_text: Optional[str] = None,
    force_subtitle_text: Optional[str] = None,
) -> Optional[Path]:
    output_path = output_path or (run_dir / "thumbnail.jpg")

    # Delete old thumbnail if exists (for re-runs)
    if output_path.exists():
        try:
            print(f"🗑️ Deleting old thumbnail: {output_path.name}")
            output_path.unlink()
        except Exception as e:
            print(f"⚠️ Could not delete old thumbnail: {e}")

    meta = _load_titles(titles_json, debug=debug)
    # Prefer new thumbnail-specific fields if present
    title = (
        meta.get("thumbnail_title")  # NEW: Correct field name
        or meta.get("hook thumbanil")  # Legacy fallback (typo kept for compatibility)
        or meta.get("youtube_title")
        or meta.get("main_title")
        or meta.get("top_title")
        or "Book Summary"
    )
    subtitle = (
        meta.get("thumbnail_subtitle")  # NEW: Correct field name
        or meta.get("sub hook thumbanil")  # Legacy fallback (typo kept for compatibility)
        or meta.get("subtitle")
        or ""
    )

    # Clean texts before using them
    title = _clean_thumbnail_text(title)
    subtitle = _clean_thumbnail_text(subtitle)

    if isinstance(force_title_text, str) and force_title_text.strip():
        title = _clean_thumbnail_text(force_title_text.strip())
    if isinstance(force_subtitle_text, str) and force_subtitle_text.strip():
        subtitle = _clean_thumbnail_text(force_subtitle_text.strip())

    # Base canvas
    W, H = SIZE
    base = Image.new("RGB", SIZE, (20, 24, 28))

    # Background: blur/scale cover or gradient
    cover_path = _find_cover(run_dir, debug=debug)

    # Auto-extract subtitle color from cover if available
    if cover_path:
        extracted_color = _extract_accent_color_from_cover(cover_path, debug=debug)
        if extracted_color:
            subtitle_color = extracted_color
            if debug:
                print(f"[thumb] using auto-extracted subtitle color: {subtitle_color}")

    # Define resampling filter once for all image operations
    RESAMPLING = getattr(Image, "Resampling", None)
    lanczos = getattr(RESAMPLING, "LANCZOS", None) if RESAMPLING else getattr(Image, "LANCZOS", 1)

    if cover_path:
        try:
            bg = Image.open(cover_path).convert("RGB")
            # Fill background with blurred cover
            bg_ratio = bg.width / bg.height
            target_ratio = W / H
            if bg_ratio > target_ratio:
                # too wide -> fit height
                nh = H
                nw = int(nh * bg_ratio)
            else:
                nw = W
                nh = int(nw / bg_ratio)
            bg = bg.resize((nw, nh), lanczos)
            bx = (nw - W) // 2
            by = (nh - H) // 2
            bg = bg.crop((bx, by, bx + W, by + H))
            bg = bg.filter(ImageFilter.GaussianBlur(radius=22))
            # Darken
            overlay = Image.new("RGB", SIZE, (0, 0, 0))
            bg = Image.blend(bg, overlay, alpha=0.35)
            base.paste(bg, (0, 0))
        except Exception as e:
            if debug:
                print("[thumb] background from cover failed:", e)
    else:
        # simple diagonal gradient
        grad = Image.new("RGB", SIZE)
        for yy in range(H):
            for xx in range(W):
                t = (xx + yy) / (W + H)
                r = int(30 + 70 * t)
                g = int(35 + 60 * t)
                b = int(45 + 50 * t)
                grad.putpixel((xx, yy), (r, g, b))
        base.paste(grad, (0, 0))

    # Optional global dim layer over the background (behind cover and text)
    try:
        dim = float(background_dim)
    except Exception:
        dim = 0.0
    dim = max(0.0, min(0.95, dim))
    if dim > 0:
        base = Image.blend(base, Image.new("RGB", SIZE, (0, 0, 0)), alpha=dim)
        if debug:
            try:
                print(f"[thumb] applied background dim: {dim}")
            except Exception:
                pass

    draw = ImageDraw.Draw(base)

    # Layout: left cover box, right text with balanced spacing
    left_pad = 125  # Shift everything 45px right total (was 80px) - more visible shift
    right_pad = 0   # Removed to give more space (was 40px)
    top_pad = 100   # Smaller cover: 520px height
    bottom_pad = 100  # Smaller cover: 520px height
    gutter = 60  # Equal to side padding for perfect symmetry (increased from 50px)

    cover_box_w = 500  # LARGER cover: 500px width for better visibility (was 370px)
    cover_box_h = H - top_pad - bottom_pad  # 720 - 100 - 100 = 520px
    cover_box = (left_pad, top_pad, left_pad + cover_box_w, top_pad + cover_box_h)

    # Text area starts to the right of the cover box
    # Important: keep equal spacing on both sides for visual balance
    panel_x0 = cover_box[2] + gutter

    # Calculate text area with symmetric padding
    # Left side: gutter after cover
    # Right side: should match the gutter for symmetry
    text_padding_left = gutter  # Space from cover edge to text start
    text_padding_right = gutter  # Space from text end to screen edge
    # (Removed semi-transparent panel to keep clean design)

    # Paste cover (FIT) with an elegant double-border frame (outer gold, inner dark)
    if cover_path:
        try:
            cover = Image.open(cover_path).convert("RGB")
            # FIT: use MIN ratio to fit entire cover in box without cropping
            cb_w = cover_box_w
            cb_h = cover_box_h
            ratio = min(cb_w / cover.width, cb_h / cover.height)  # MIN fits the box
            nw, nh = int(cover.width * ratio), int(cover.height * ratio)
            
            # Parameters for frame
            outer_thickness = max(6, int(min(nw, nh) * 0.03))  # responsive thickness
            inner_thickness = max(3, int(outer_thickness * 0.55))
            radius = max(12, int(min(nw, nh) * 0.05))
            
            # Total size including borders
            total_w = nw + outer_thickness * 2 + inner_thickness * 2
            total_h = nh + outer_thickness * 2 + inner_thickness * 2
            
            # Create framed image with transparent background
            framed = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
            fd = ImageDraw.Draw(framed)
            
            # Draw outer border (using subtitle color) with fill
            outer_color = (subtitle_color[0], subtitle_color[1], subtitle_color[2], 255)
            fd.rounded_rectangle([0, 0, total_w, total_h], radius=radius + outer_thickness + inner_thickness, fill=outer_color)
            
            # Draw inner gold rim with fill (remove dark layer to avoid lines)
            inset2 = outer_thickness
            rim_color = (245, 222, 179, 255)
            fd.rounded_rectangle([inset2, inset2, total_w - inset2, total_h - inset2], radius=radius, fill=rim_color)
            
            # Resize cover to inner area (nw x nh) and apply rounded mask
            cover_resized = cover.resize((nw, nh), lanczos)
            mask = Image.new("L", (nw, nh), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle([0, 0, nw, nh], radius=radius - 4 if radius > 8 else radius, fill=255)
            
            # Paste cover into framed image
            cover_pos = (inset2, inset2)
            framed.paste(cover_resized, cover_pos, mask)
            
            # Center the framed cover in the cover_box
            cx = cover_box[0] + (cb_w - total_w) // 2
            cy = cover_box[1] + (cb_h - total_h) // 2
            
            # Create mask for the entire framed image to avoid background
            frame_mask = Image.new("L", (total_w, total_h), 0)
            fm_draw = ImageDraw.Draw(frame_mask)
            fm_draw.rounded_rectangle([0, 0, total_w, total_h], radius=radius + outer_thickness + inner_thickness, fill=255)
            
            base.paste(framed, (cx, cy), frame_mask)
        except Exception as e:
            if debug:
                print("[thumb] paste framed cover failed:", e)

    # Title and subtitle on right side
    # Fonts: prefer Cairo (Bold for title, SemiBold/Regular for subtitle). Allow overriding via env paths as well.
    env_title_font = os.environ.get("THUMBNAIL_TITLE_FONT")
    env_sub_font = os.environ.get("THUMBNAIL_SUB_FONT")
    # Start with explicit paths and env vars
    title_explicit: List[Path] = []
    sub_explicit: List[Path] = []
    if title_font_path and Path(title_font_path).exists():
        title_explicit.append(Path(title_font_path))
    if sub_font_path and Path(sub_font_path).exists():
        sub_explicit.append(Path(sub_font_path))
    if env_title_font and Path(env_title_font).exists():
        title_explicit.append(Path(env_title_font))
    if env_sub_font and Path(env_sub_font).exists():
        sub_explicit.append(Path(env_sub_font))
    # 3) Family name requests (Bebas Neue, Cairo, and Impact supported)
    def family_to_candidates(name: Optional[str], weight_title: str, weight_sub: str) -> Tuple[List[Path], List[Path]]:
        nt = (name or '').strip().lower()
        if not nt:
            return [], []
        if nt in ("bebas", "bebas neue", "bebas-neue", "bebasneue"):
            return _bebas_neue_candidates(weight_title), _bebas_neue_candidates(weight_sub)
        if nt in ("cairo",):
            return _cairo_candidates(weight_title), _cairo_candidates(weight_sub)
        if nt in ("impact",):
            return _impact_candidates(weight_title), _impact_candidates(weight_sub)
        # Generic search by family substring
        roots = [
            Path("assets/fonts"), Path("secrets/fonts"), Path("C:/Windows/Fonts"),
            Path("/usr/share/fonts"), Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
        ]
        pat = re.compile(re.escape(nt), re.IGNORECASE)
        t_c: List[Path] = []
        s_c: List[Path] = []
        for r in roots:
            try:
                for p in r.glob("*.ttf"):
                    if pat.search(p.name):
                        t_c.append(p)
                        s_c.append(p)
                for p in r.glob("*.otf"):
                    if pat.search(p.name):
                        t_c.append(p)
                        s_c.append(p)
            except Exception:
                pass
        return t_c, s_c

    fam_t_c_title, _ = family_to_candidates(title_font_name, "bold", "bold")
    _, fam_s_c_sub = family_to_candidates(sub_font_name, "semibold", "semibold")

    if strict_fonts:
        # Strict: only explicit paths and the requested family are allowed
        # Fallback within same family across weights: if one is empty, reuse the other
        if not fam_t_c_title and fam_s_c_sub:
            fam_t_c_title = fam_s_c_sub
        if not fam_s_c_sub and fam_t_c_title:
            fam_s_c_sub = fam_t_c_title
        title_font_cands: List[Path] = title_explicit + fam_t_c_title
        sub_font_cands: List[Path] = sub_explicit + fam_s_c_sub
        # If family name requested but not found (and no explicit path), raise a clear error
        if title_font_name and not fam_t_c_title and not title_explicit:
            raise FileNotFoundError(
                f"لم يتم العثور على خط العنوان المطلوب '{title_font_name}'. ثبّت الخط في C:/Windows/Fonts أو مرّر مساره عبر --title-font أو THUMBNAIL_TITLE_FONT."
            )
        if sub_font_name and not fam_s_c_sub and not sub_explicit:
            raise FileNotFoundError(
                f"لم يتم العثور على خط العنوان الفرعي المطلوب '{sub_font_name}'. ثبّت الخط في C:/Windows/Fonts أو مرّر مساره عبر --sub-font أو THUMBNAIL_SUB_FONT."
            )
    else:
        # Non-strict: Use only Bebas Neue (all other fonts removed)
        title_font_cands = title_explicit + fam_t_c_title
        sub_font_cands = sub_explicit + fam_s_c_sub
        # SIMPLIFIED: Only Bebas Neue supported
        if not fam_t_c_title:
            title_font_cands.extend(_bebas_neue_candidates("bold"))
        if not fam_s_c_sub:
            sub_font_cands.extend(_bebas_neue_candidates("regular"))

    # Calculate text area dimensions with BALANCED spacing
    # The text area should have equal margins from both the cover (left) and screen edge (right)
    #
    # Layout breakdown:
    # |<-left_pad->|<-cover_box_w->|<-gutter->|<-TEXT AREA->|<-gutter->|
    #
    # Total available for text: W - (left_pad + cover_box_w + 2*gutter)
    available_for_text = W - (left_pad + cover_box_w + 2 * gutter)

    # Text area starts after: left_pad + cover_box_w + gutter
    text_area_x = left_pad + cover_box_w + gutter
    text_area_y = top_pad  # Perfect alignment with cover zone top
    text_area_w = available_for_text

    # Load font-specific profile for dynamic sizing
    # Each font (Bebas Neue, Cairo, etc.) has its own sizing dynamics!
    repo_root = Path(__file__).resolve().parents[3]  # Fixed: was parents[2], should be parents[3]!
    config_dir = repo_root / "config"
    font_profile = _load_font_profile(title_font_name or "Bebas Neue", config_dir)
    
    if debug:
        print(f"[thumb] DEBUG: config_dir = {config_dir}")
        print(f"[thumb] DEBUG: title_base_size = {font_profile['title_base_size']}")
        print(f"[thumb] loaded font profile for '{title_font_name}': base={font_profile['title_base_size']}px")

    # Load fonts (bigger main title size and smaller subtitle size)
    try:
        tsize = max(40, int(title_font_size))
    except Exception:
        tsize = font_profile["title_base_size"]  # Use profile default

    # REMOVED: Short title boost - now ALL titles use dynamic sizing
    title_word_count = _word_count(title)
    title_char_count = len(title.replace(" ", ""))  # Count chars without spaces
    is_short_title = title_word_count <= 3 or title_char_count <= 15

    # Apply dynamic title sizing for ALL titles (removed short_title exception)
    if dynamic_title_size:
        tsize = _calculate_optimal_title_size(title, font_profile=font_profile, max_width=text_area_w)
        if debug:
            try:
                print(f"[thumb] calculated title size: {tsize}px (word_count={_word_count(title)}, avg_len={_avg_word_length(title):.1f})")
                print(f"[thumb] text area: x={text_area_x}, w={text_area_w}px (balanced {gutter}px margins)")
            except Exception:
                pass
    elif is_short_title and debug:
        print(f"[thumb] KEEPING LARGE SIZE for short title: {tsize}px (dynamic sizing skipped)")

    try:
        ssize = max(38, int(subtitle_font_size))
    except Exception:
        ssize = font_profile["subtitle_base_size"]  # Use profile default
    subtitle_font = _load_font(ssize, sub_font_cands, strict=strict_fonts, role="sub", debug=debug)
    title_font = _load_font(tsize, title_font_cands, strict=strict_fonts, role="title", debug=debug)

    # Force main title to uppercase (Latin scripts). Arabic unaffected.
    render_title = str(title).upper()

    # Determine optimal number of lines for title
    # ENHANCED: Smart line distribution for all word counts
    word_count = _word_count(render_title)
    words = render_title.split()
    
    if word_count <= 2:
        target_lines = 1
        title_lines = [render_title]
    elif word_count == 3:
        target_lines = 2
        # Split as 1+2 or 2+1 based on word length for better balance
        # Check if first word is significantly longer
        if len(words[0]) >= len(words[1]) + len(words[2]):
            # First word long: 1 + 2
            title_lines = [words[0], " ".join(words[1:])]
        else:
            # Default: 2 + 1 (better visual balance)
            title_lines = [" ".join(words[:2]), words[2]]
    elif word_count == 4:
        # Check if words are long (average > 8 chars) → use 3 lines
        avg_word_len = sum(len(w) for w in words) / len(words)
        
        if avg_word_len > 8:
            # Long words: use 3 lines with balanced distribution
            target_lines = 3
            
            # Try different 3-line splits to find most balanced
            splits = [
                (2, 1, 1),  # 2+1+1
                (1, 2, 1),  # 1+2+1
                (1, 1, 2),  # 1+1+2
            ]
            
            best_split = (1, 2, 1)  # default
            min_variance = float('inf')
            
            for split in splits:
                # Calculate character count for each line
                line1_len = sum(len(words[i]) for i in range(split[0])) + (split[0] - 1)
                line2_len = sum(len(words[i]) for i in range(split[0], split[0] + split[1])) + (split[1] - 1)
                line3_len = sum(len(words[i]) for i in range(split[0] + split[1], 4)) + (split[2] - 1)
                
                # Calculate variance (lower is more balanced)
                avg_len = (line1_len + line2_len + line3_len) / 3
                variance = ((line1_len - avg_len)**2 + (line2_len - avg_len)**2 + (line3_len - avg_len)**2)
                
                if variance < min_variance:
                    min_variance = variance
                    best_split = split
            
            # Apply best split
            title_lines = [
                " ".join(words[:best_split[0]]),
                " ".join(words[best_split[0]:best_split[0] + best_split[1]]),
                " ".join(words[best_split[0] + best_split[1]:])
            ]
        else:
            # Short/normal words: use 2 lines (2+2)
            target_lines = 2
            title_lines = [" ".join(words[:2]), " ".join(words[2:])]
    elif word_count == 5:
        target_lines = 3
        # Split as 2+2+1 for balanced distribution
        title_lines = [" ".join(words[:2]), " ".join(words[2:4]), words[4]]
    elif word_count == 6:
        target_lines = 3
        # Split as 2+2+2 for perfect 3-line balance
        title_lines = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:])]
    elif word_count == 7:
        target_lines = 3
        # Split as 3+2+2 or 2+3+2 (use balanced wrapper)
        title_lines = _wrap_text_balanced(render_title, title_font, text_area_w, max_lines=3)
    else:
        # 8+ words: use balanced line breaking with max 3 lines
        target_lines = 3
        title_lines = _wrap_text_balanced(render_title, title_font, text_area_w, max_lines=3)

    # CRITICAL FIX: If any line is still too wide, iteratively reduce font size
    max_attempts = 30  # Increased from 15 to allow more reductions
    for attempt in range(max_attempts):
        max_line_width = max(_text_width(title_font, line) for line in title_lines) if title_lines else 0
        if max_line_width <= text_area_w:
            break  # All lines fit!
        # Reduce font size by 2px for finer control (changed from 5px)
        tsize = max(40, tsize - 2)  # LOWERED minimum from 50 to 40px for even smaller text
        title_font = _load_font(tsize, title_font_cands, strict=strict_fonts, role="title", debug=debug)
        # Re-apply the same smart splitting logic
        words = render_title.split()
        if word_count <= 2:
            title_lines = [render_title]
        elif word_count == 3:
            # Same smart logic as above
            if len(words[0]) >= len(words[1]) + len(words[2]):
                title_lines = [words[0], " ".join(words[1:])]
            else:
                title_lines = [" ".join(words[:2]), words[2]]
        elif word_count == 4:
            # Check if words are long (average > 8 chars) → use 3 lines
            avg_word_len = sum(len(w) for w in words) / len(words)
            
            if avg_word_len > 8:
                # Long words: use 3 lines with balanced distribution
                splits = [(2, 1, 1), (1, 2, 1), (1, 1, 2)]
                
                best_split = (1, 2, 1)
                min_variance = float('inf')
                
                for split in splits:
                    line1_len = sum(len(words[i]) for i in range(split[0])) + (split[0] - 1)
                    line2_len = sum(len(words[i]) for i in range(split[0], split[0] + split[1])) + (split[1] - 1)
                    line3_len = sum(len(words[i]) for i in range(split[0] + split[1], 4)) + (split[2] - 1)
                    
                    avg_len = (line1_len + line2_len + line3_len) / 3
                    variance = ((line1_len - avg_len)**2 + (line2_len - avg_len)**2 + (line3_len - avg_len)**2)
                    
                    if variance < min_variance:
                        min_variance = variance
                        best_split = split
                
                title_lines = [
                    " ".join(words[:best_split[0]]),
                    " ".join(words[best_split[0]:best_split[0] + best_split[1]]),
                    " ".join(words[best_split[0] + best_split[1]:])
                ]
            else:
                # Short/normal words: use 2 lines (2+2)
                title_lines = [" ".join(words[:2]), " ".join(words[2:])]
        elif word_count == 5:
            title_lines = [" ".join(words[:2]), " ".join(words[2:4]), words[4]]
        elif word_count == 6:
            title_lines = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:])]
        else:
            # 7+ words: use balanced wrapper
            title_lines = _wrap_text_balanced(render_title, title_font, text_area_w, max_lines=3)
        if debug and attempt < max_attempts - 1:
            try:
                print(f"[thumb] text too wide ({max_line_width}px > {text_area_w}px), reducing to {tsize}px")
            except Exception:
                pass

    # SUBTITLE AUTO-SCALING: Ensure subtitle fits and is always smaller than main title
    if subtitle:
        # First, ensure subtitle is never bigger than 70% of final title size
        # BUT never smaller than 100px for readability (reduced from 240px)
        max_subtitle_size = int(tsize * 0.70)  # 70% of main title (was 50%)
        min_subtitle_size = 100  # Minimum size for readability (reduced from 240px)
        ssize = max(min_subtitle_size, min(ssize, max_subtitle_size))
        subtitle_font = _load_font(ssize, sub_font_cands, strict=strict_fonts, role="sub", debug=debug)

        # Then, auto-reduce if subtitle is too wide
        subtitle_text = str(subtitle)
        max_sub_attempts = 10
        for attempt in range(max_sub_attempts):
            sub_width = _text_width(subtitle_font, subtitle_text)
            if sub_width <= text_area_w:
                break  # Subtitle fits!
            # Reduce subtitle font size by 2px
            ssize = max(20, ssize - 2)
            subtitle_font = _load_font(ssize, sub_font_cands, strict=strict_fonts, role="sub", debug=debug)
            if debug and attempt < max_sub_attempts - 1:
                print(f"[thumb] subtitle too wide ({sub_width}px > {text_area_w}px), reducing to {ssize}px")

        if debug:
            try:
                final_sub_width = _text_width(subtitle_font, subtitle_text)
                print(f"[thumb] subtitle: {ssize}px ({final_sub_width}px wide) | title: {tsize}px | ratio: {(ssize/tsize)*100:.0f}% | min: {min_subtitle_size}px")
            except Exception:
                pass

    # Vertical spacing between multiple title lines
    line_gap = max(0, int(title_line_gap))
    if debug:
        try:
            print(f"[thumb] title lines: {len(title_lines)} | line_gap: {line_gap}px")
        except Exception:
            pass
    
    # Process subtitle: split into 2 lines if 3+ words (first line = 2 words, rest on second line)
    subtitle_lines = []
    if subtitle:
        subtitle_text = str(subtitle)
        subtitle_words = subtitle_text.split()
        if len(subtitle_words) >= 3:
            # Split into 2 lines - first line gets 2 words, rest on second line
            subtitle_lines = [
                " ".join(subtitle_words[:2]),  # First 2 words
                " ".join(subtitle_words[2:])   # Remaining words
            ]
            if debug:
                print(f"[thumb] subtitle split into 2 lines: '{subtitle_lines[0]}' / '{subtitle_lines[1]}' ({len(subtitle_words)} words)")
            
            # CRITICAL: Check if any subtitle line is too wide and reduce font size
            max_sub_line_attempts = 20
            for attempt in range(max_sub_line_attempts):
                max_sub_line_width = max(_text_width(subtitle_font, line) for line in subtitle_lines)
                if max_sub_line_width <= text_area_w:
                    break  # All subtitle lines fit!
                # Reduce subtitle font size by 2px
                ssize = max(40, ssize - 2)  # Lower minimum to 40px for very long text
                subtitle_font = _load_font(ssize, sub_font_cands, strict=strict_fonts, role="sub", debug=debug)
                if debug and attempt < max_sub_line_attempts - 1:
                    print(f"[thumb] subtitle line too wide ({max_sub_line_width}px > {text_area_w}px), reducing to {ssize}px")
        else:
            # 1-2 words: keep on single line
            subtitle_lines = [subtitle_text]
            if debug:
                print(f"[thumb] subtitle single line: '{subtitle_text}' ({len(subtitle_words)} words)")
    
    # UNIFIED SPACING: 110px for all subtitles (single-line and multi-line)
    sub_gap_before = int(max(0, subtitle_gap)) if subtitle else 0  # Use consistent 110px gap
    if debug and subtitle:
        print(f"[thumb] subtitle gap: {subtitle_gap}px (lines: {len(subtitle_lines)})")

    # Compute total block height: sum of title line heights + gaps + subtitle height (if any)
    title_heights = [
        _text_height(title_font, ln, fallback=72) for ln in title_lines
    ]
    total_title_height = sum(title_heights) + (len(title_heights) - 1) * line_gap if title_heights else 0

    # Calculate subtitle total height (all lines + gaps between them)
    subtitle_line_gap = 30  # Gap between subtitle lines (increased from 10)
    subtitle_heights = [_text_height(subtitle_font, line, fallback=56) for line in subtitle_lines] if subtitle_lines else []
    total_subtitle_height = sum(subtitle_heights) + (len(subtitle_heights) - 1) * subtitle_line_gap if subtitle_heights else 0

    # Center the text block inside the actual text area (text_area_y..text_area_y+text_area_h)
    text_area_h = H - bottom_pad - text_area_y
    # No player icons - clean professional design
    total_block_height = total_title_height + (sub_gap_before if subtitle else 0) + total_subtitle_height
    # Start y so the whole block is vertically centered in the TEXT AREA
    vertical_offset = -40  # Move text UP by 40px for better visual balance
    y = int(text_area_y + max(0, (text_area_h - total_block_height) / 2) + vertical_offset)

    # === AUTOMATIC TEXT COLOR ADJUSTMENT ===
    if debug:
        print("\n[thumb] === Calculating optimal text colors ===")

    # Calculate background color in title area
    title_y_start = max(0, int(y) - 20)  # Slightly above title position
    title_y_height = min(250, total_title_height + 40)
    title_bg_avg = _get_average_color_in_area(
        base,
        text_area_x,
        title_y_start,
        text_area_w,
        title_y_height,
        sample_size=100
    )

    # Determine optimal title color from expanded palette
    auto_title_color = _get_smart_text_color(title_bg_avg, debug=debug)
    title_color = auto_title_color  # Use auto color

    # Calculate background color in subtitle area
    if subtitle_lines:
        subtitle_y_start = max(0, int(y + total_title_height + sub_gap_before) - 10)
        subtitle_y_height = min(150, total_subtitle_height + 20)
        subtitle_bg_avg = _get_average_color_in_area(
            base,
            text_area_x,
            subtitle_y_start,
            text_area_w,
            subtitle_y_height,
            sample_size=100
        )

        # For subtitle: use professional fixed colors instead of extracted
        # Extracted colors are often unclear or ugly - use curated palette
        PROFESSIONAL_SUBTITLE_COLORS = [
            (255, 215, 0),    # Gold - classic, always readable
            (255, 140, 0),    # Dark Orange - warm and vibrant
            (255, 69, 0),     # Red-Orange - bold and eye-catching
            (50, 205, 50),    # Lime Green - fresh and energetic
            (0, 191, 255),    # Deep Sky Blue - modern and clean
            (147, 112, 219),  # Medium Purple - elegant
            (255, 20, 147),   # Deep Pink - attention-grabbing
            (255, 255, 100),  # Bright Yellow - high visibility
        ]
        
        # Choose color based on background to ensure contrast
        if cover_path:
            # Pick best contrasting color from palette
            best_color = PROFESSIONAL_SUBTITLE_COLORS[0]  # Default: Gold
            best_contrast = 0
            
            for color in PROFESSIONAL_SUBTITLE_COLORS:
                contrast = _calculate_contrast_ratio(color, subtitle_bg_avg)
                if contrast > best_contrast:
                    best_contrast = contrast
                    best_color = color
            
            subtitle_color = best_color
            if debug:
                print(f"[thumb] subtitle color: RGB{subtitle_color}, contrast: {best_contrast:.2f}:1")
                print(f"[thumb] ✅ using professional color palette (guaranteed readable)")
        else:
            subtitle_color = _get_smart_text_color(subtitle_bg_avg, debug=debug)

    # Prepare to draw semi-transparent text: switch to RGBA so alpha in fills is respected
    try:
        ta = max(0, min(255, int(title_alpha)))
    except Exception:
        ta = 200
    try:
        sa = max(0, min(255, int(subtitle_alpha)))
    except Exception:
        sa = 200
    base = base.convert("RGBA")
    draw = ImageDraw.Draw(base)

    # Draw title lines centered horizontally with semi-transparent fill
    for idx, line in enumerate(title_lines):
        lw = _text_width(title_font, line)
        cx = int(text_area_x + max(0, (text_area_w - lw) / 2))
        tc = (int(title_color[0]), int(title_color[1]), int(title_color[2]), ta)
        if debug:
            try:
                print(f"[thumb] line {idx+1}: '{line}' | width={lw}px | area_width={text_area_w}px | centered_x={cx}")
            except Exception:
                pass
        _draw_text_with_outline(draw, (cx, int(y)), line, title_font, fill=tc, outline=(0, 0, 0, 0), outline_width=0)
        y += title_heights[idx] + line_gap

    # Draw subtitle lines if present, also centered
    if subtitle_lines:
        y += sub_gap_before
        sc = (int(subtitle_color[0]), int(subtitle_color[1]), int(subtitle_color[2]), sa)

        for sub_idx, sub_line in enumerate(subtitle_lines):
            lw = _text_width(subtitle_font, sub_line)
            cx = int(text_area_x + max(0, (text_area_w - lw) / 2))

            # Draw semi-transparent overlay behind subtitle for readability if enabled
            if subtitle_overlay and lw > 0 and sub_idx == 0:  # Only overlay on first line
                try:
                    pad_x = max(0, int(subtitle_overlay_pad_x))
                    pad_y = max(0, int(subtitle_overlay_pad_y))
                    rad = max(0, int(subtitle_overlay_radius))
                    sh = total_subtitle_height
                    left = max(0, cx - pad_x)
                    top = max(0, int(y) - pad_y)
                    right = min(W, cx + lw + pad_x)
                    bottom = min(H, int(y) + sh + pad_y)
                    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    od = ImageDraw.Draw(ov)
                    fill = (0, 0, 0, max(0, min(255, int(subtitle_overlay_alpha))))
                    if hasattr(od, "rounded_rectangle") and rad > 0:
                        od.rounded_rectangle([left, top, right, bottom], radius=rad, fill=fill)
                    else:
                        od.rectangle([left, top, right, bottom], fill=fill)
                    base = base.convert("RGBA")
                    base.alpha_composite(ov)
                    draw = ImageDraw.Draw(base)
                    if debug:
                        print("[thumb] subtitle overlay drawn")
                except Exception as e:
                    if debug:
                        print("[thumb] subtitle overlay failed:", e)

            # Draw subtitle line with clean color (no outline)
            _draw_text_with_outline(draw, (cx, int(y)), sub_line, subtitle_font, fill=sc, outline=(0, 0, 0, 0), outline_width=0)

            if debug:
                print(f"[thumb] subtitle line {sub_idx+1}: '{sub_line}' | width={lw}px | centered_x={cx}")

            y += subtitle_heights[sub_idx] + (subtitle_line_gap if sub_idx < len(subtitle_lines) - 1 else 0)

    # Player icons removed for clean, professional design - focus on title and cover only

    # Save with MAXIMUM quality (convert back to RGB for JPEG)
    try:
        base = base.convert("RGB")
        base.save(str(output_path), quality=98, optimize=False, subsampling=0)
        if debug:
            print("[thumb] saved:", output_path)
        return output_path
    except Exception as e:
        if debug:
            print("[thumb] save failed:", e)
        return None


def main(
    titles_json: Path,
    run_dir: Path,
    output_path: Optional[Path] = None,
    subtitle_gap: int = 110,  # Fixed: Match generate_thumbnail() default (was 20)
    title_line_gap: int = 40,
    background_dim: float = 0.45,
    title_font_size: int = 250,
    subtitle_font_size: int = 80,
    icons_size: int = 28,
    icons_gap: int = 24,
    icons_row_gap: int = 36,
    title_font_path: Optional[Path] = None,
    sub_font_path: Optional[Path] = None,
    title_font_name: Optional[str] = "Bebas Neue",
    sub_font_name: Optional[str] = "Bebas Neue",
    strict_fonts: bool = True,
    dynamic_title_size: bool = True,
    subtitle_overlay: bool = False,
    subtitle_overlay_alpha: int = 170,
    subtitle_overlay_pad_x: int = 22,
    subtitle_overlay_pad_y: int = 12,
    subtitle_overlay_radius: int = 14,
    title_alpha: int = 200,
    subtitle_alpha: int = 255,
    title_color: Tuple[int, int, int] = (255, 255, 255),
    subtitle_color: Tuple[int, int, int] = (255, 230, 180),
    debug: bool = False,
    force_title_text: Optional[str] = None,
    force_subtitle_text: Optional[str] = None,
) -> Optional[Path]:
    return generate_thumbnail(
        run_dir=run_dir,
        titles_json=titles_json,
        output_path=output_path,
        subtitle_gap=subtitle_gap,
        title_line_gap=title_line_gap,
        background_dim=background_dim,
        title_font_size=title_font_size,
        subtitle_font_size=subtitle_font_size,
        icons_size=icons_size,
        icons_gap=icons_gap,
        icons_row_gap=icons_row_gap,
        title_font_path=title_font_path,
        sub_font_path=sub_font_path,
        title_font_name=title_font_name,
        sub_font_name=sub_font_name,
        strict_fonts=strict_fonts,
    dynamic_title_size=dynamic_title_size,
        subtitle_overlay=subtitle_overlay,
        subtitle_overlay_alpha=subtitle_overlay_alpha,
        subtitle_overlay_pad_x=subtitle_overlay_pad_x,
        subtitle_overlay_pad_y=subtitle_overlay_pad_y,
        subtitle_overlay_radius=subtitle_overlay_radius,
        title_alpha=title_alpha,
        subtitle_alpha=subtitle_alpha,
        title_color=title_color,
        subtitle_color=subtitle_color,
        debug=debug,
        force_title_text=force_title_text,
        force_subtitle_text=force_subtitle_text,
    )


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate YouTube thumbnail image for a run directory")
    p.add_argument("--run", dest="run_dir", default="runs/latest", help="Run directory")
    p.add_argument("--titles", dest="titles_json", default=None, help="Path to output.titles.json (defaults to <run>/output.titles.json)")
    p.add_argument("--out", dest="output_path", default=None, help="Output thumbnail path (defaults to <run>/thumbnail.jpg)")
    p.add_argument("--gap", dest="subtitle_gap", type=int, default=20, help="Vertical gap in pixels between title block and subtitle (default: 20)")
    p.add_argument("--title-line-gap", dest="title_line_gap", type=int, default=40, help="Vertical gap between lines of the main title (default: 40)")
    p.add_argument("--title-size", dest="title_font_size", type=int, default=250, help="Main title font size in pixels (default: 250)")
    p.add_argument("--auto-title-size", dest="dynamic_title_size", action="store_true", default=True, help="Dynamically size title based on word count and text length. Sizes range 100-220px. Use --no-auto-title-size to disable.")
    p.add_argument("--no-auto-title-size", dest="dynamic_title_size", action="store_false")
    p.add_argument("--sub-size", dest="subtitle_font_size", type=int, default=80, help="Subtitle font size in pixels (default: 80)")
    p.add_argument("--icons-size", dest="icons_size", type=int, default=28, help="Player icons size (height/width) in pixels (default: 28)")
    p.add_argument("--icons-gap", dest="icons_gap", type=int, default=24, help="Gap between icons in pixels (default: 24)")
    p.add_argument("--icons-row-gap", dest="icons_row_gap", type=int, default=36, help="Vertical gap between subtitle and icons row (default: 36)")
    p.add_argument("--dim", dest="background_dim", type=float, default=0.45, help="Global background dim (0..1) applied behind cover/text (default: 0.45)")
    p.add_argument("--title-font", dest="title_font_path", default=None, help="Path to a TTF/OTF font file for the title (e.g., Cairo-Bold.ttf or Times New Roman Bold.ttf)")
    p.add_argument("--sub-font", dest="sub_font_path", default=None, help="Path to a TTF/OTF font file for the subtitle (e.g., Cairo-SemiBold.ttf or Times New Roman.ttf)")
    p.add_argument("--title-font-name", dest="title_font_name", default="Bebas Neue", help="Required font family name for title (default: Bebas Neue). If not found, error.")
    p.add_argument("--sub-font-name", dest="sub_font_name", default="Bebas Neue", help="Required font family name for subtitle (default: Bebas Neue). If not found, error.")
    p.add_argument("--strict-fonts", dest="strict_fonts", action="store_true", default=True, help="Enforce required fonts strictly (error if missing). Use --no-strict-fonts to allow fallbacks.")
    p.add_argument("--no-strict-fonts", dest="strict_fonts", action="store_false")
    p.add_argument("--sub-overlay", dest="subtitle_overlay", action="store_true", default=False, help="Draw semi-transparent overlay behind subtitle (default: off)")
    p.add_argument("--no-sub-overlay", dest="subtitle_overlay", action="store_false")
    p.add_argument("--sub-overlay-alpha", dest="subtitle_overlay_alpha", type=int, default=170, help="Subtitle overlay alpha 0..255 (default: 170)")
    p.add_argument("--sub-overlay-pad-x", dest="subtitle_overlay_pad_x", type=int, default=22, help="Subtitle overlay horizontal padding in px (default: 22)")
    p.add_argument("--sub-overlay-pad-y", dest="subtitle_overlay_pad_y", type=int, default=12, help="Subtitle overlay vertical padding in px (default: 12)")
    p.add_argument("--sub-overlay-radius", dest="subtitle_overlay_radius", type=int, default=14, help="Subtitle overlay corner radius in px (default: 14)")
    p.add_argument("--title-alpha", dest="title_alpha", type=int, default=255, help="Title text alpha 0..255 (default: 255)")
    p.add_argument("--sub-alpha", dest="subtitle_alpha", type=int, default=255, help="Subtitle text alpha 0..255 (default: 255)")
    p.add_argument("--title-color", dest="title_color", default="#FFFFFF", help="Title color (#RRGGBB or name). Default: #FFFFFF")
    p.add_argument("--sub-color", dest="subtitle_color", default="#FFD700", help="Subtitle color (#RRGGBB or name). Default: #FFD700 (gold)")
    p.add_argument("--force-title-text", dest="force_title_text", default=None, help="Override detected title text")
    p.add_argument("--force-subtitle-text", dest="force_subtitle_text", default=None, help="Override detected subtitle text")
    p.add_argument("--debug", action="store_true", help="Print debug info")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    titles_json = Path(args.titles_json) if args.titles_json else (run_dir / "output.titles.json")
    out = Path(args.output_path) if args.output_path else None
    tfont = Path(args.title_font_path) if args.title_font_path else None
    sfont = Path(args.sub_font_path) if args.sub_font_path else None
    # Parse colors
    def parse_color(val: Optional[str], default: Tuple[int, int, int]) -> Tuple[int, int, int]:
        if not val:
            return default
        try:
            rgb = ImageColor.getrgb(val)
            if isinstance(rgb, tuple) and len(rgb) >= 3:
                return (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        except Exception:
            pass
        # Try comma-separated r,g,b
        try:
            parts = [int(x.strip()) for x in str(val).split(',')]
            if len(parts) >= 3:
                return (max(0, min(255, parts[0])), max(0, min(255, parts[1])), max(0, min(255, parts[2])))
        except Exception:
            pass
        return default

    tcol = parse_color(args.title_color, (255, 255, 255))
    scol = parse_color(args.subtitle_color, (255, 230, 180))

    res = main(
        titles_json,
        run_dir,
        output_path=out,
        subtitle_gap=int(args.subtitle_gap),
        title_line_gap=int(args.title_line_gap),
        background_dim=float(args.background_dim),
        title_font_size=int(args.title_font_size),
        subtitle_font_size=int(args.subtitle_font_size),
        icons_size=int(args.icons_size),
        icons_gap=int(args.icons_gap),
        icons_row_gap=int(args.icons_row_gap),
        title_font_path=tfont,
        sub_font_path=sfont,
        title_font_name=args.title_font_name,
        sub_font_name=args.sub_font_name,
        strict_fonts=bool(args.strict_fonts),
    dynamic_title_size=bool(args.dynamic_title_size),
        subtitle_overlay=bool(args.subtitle_overlay),
        subtitle_overlay_alpha=int(args.subtitle_overlay_alpha),
        subtitle_overlay_pad_x=int(args.subtitle_overlay_pad_x),
        subtitle_overlay_pad_y=int(args.subtitle_overlay_pad_y),
        subtitle_overlay_radius=int(args.subtitle_overlay_radius),
        title_alpha=int(args.title_alpha),
        subtitle_alpha=int(args.subtitle_alpha),
        title_color=tcol,
        subtitle_color=scol,
        force_title_text=args.force_title_text,
        force_subtitle_text=args.force_subtitle_text,
        debug=bool(args.debug),
    )
    print(str(res) if res else "thumbnail generation failed")
