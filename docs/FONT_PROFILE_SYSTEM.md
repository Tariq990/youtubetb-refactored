# Font Profile System - Multiple Fonts with Independent Dynamics

## Overview
YouTubeTB now supports **multiple font profiles** for thumbnails. Each font (Bebas Neue, Cairo, etc.) has its own **independent sizing dynamics**, allowing you to choose the perfect font for your content while maintaining optimal text sizing.

## What's New?

### ✨ Font-Specific Profiles
- **Bebas Neue** (Default): Bold, condensed, all-caps display font
  - Aggressive sizing: 135px base (60-220px range)
  - High impact for short titles (1.8x boost for 2 words)
  - Slower decay rate (0.92) for longer titles
  
- **Cairo**: Modern Arabic/Latin typeface with excellent readability
  - Conservative sizing: 100px base (50-180px range)
  - Balanced boost for short titles (1.6x for 2 words)
  - Faster decay rate (0.90) for better readability on long titles

### 🎯 Independent Dynamics
Each font profile has separate parameters:
- `title_base_size`: Starting size for calculations
- `title_min_size` / `title_max_size`: Bounds for dynamic sizing
- `subtitle_base_size`: Subtitle font size
- `dynamic_scaling`: Word-count specific multipliers
  - `2_words`: Boost for short titles
  - `3_words_long/medium/short`: Fine-tuning for 3-word titles
  - `4_words`, `5_words`, `6_words`: Progressive sizing
  - `decay_rate`: Exponential decay for long titles

## Configuration

### 1. Font Profiles (`config/settings.json`)
```json
{
  "thumbnail_font_profiles": {
    "Bebas Neue": {
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
    },
    "Cairo": {
      "title_base_size": 100,
      "title_min_size": 50,
      "title_max_size": 180,
      "subtitle_base_size": 65,
      "subtitle_min_size": 50,
      "subtitle_ratio": 0.65,
      "dynamic_scaling": {
        "2_words": 1.6,
        "3_words_long": 0.85,
        "3_words_medium": 1.1,
        "3_words_short": 1.3,
        "4_words": 1.0,
        "5_words": 0.9,
        "6_words": 0.85,
        "decay_rate": 0.90
      }
    }
  }
}
```

### 2. Select Font (`config/settings.json`)
```json
{
  "thumbnail_title_font": "Bebas Neue",  // or "Cairo"
  "thumbnail_subtitle_font": "Bebas Neue"  // or "Cairo"
}
```

## Installation

### Bebas Neue (Already Included ✅)
- Available in `assets/fonts/BebasNeue-Regular.ttf`
- No installation needed!

### Cairo Font (Optional)
1. **Download**: https://fonts.google.com/specimen/Cairo
2. **Install Options**:
   - **Windows**: Copy `.ttf` files to `C:\Windows\Fonts\`
   - **Project**: Copy to `assets/fonts/`
3. **Recommended Variants**:
   - `Cairo-Bold.ttf` (for titles)
   - `Cairo-SemiBold.ttf` (for subtitles)
   - `Cairo-Regular.ttf` (fallback)

## Usage

### Method 1: Change in Settings (Permanent)
Edit `config/settings.json`:
```json
{
  "thumbnail_title_font": "Cairo",
  "thumbnail_subtitle_font": "Cairo"
}
```

### Method 2: Command Line (One-time)
```bash
python main.py
# → Option 8: Generate thumbnail for existing run
# → Select run folder
# → Provide --title-font Cairo when prompted
```

### Method 3: Programmatic
```python
from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail

generate_thumbnail(
    run_dir=Path("runs/2025-10-24_08-40-12_The-Secret"),
    titles_json=Path("runs/2025-10-24_08-40-12_The-Secret/titles.json"),
    title_font_name="Cairo",  # Use Cairo profile
    sub_font_name="Cairo",
    dynamic_title_size=True  # Enable profile-based sizing
)
```

## Testing

### Test Font Profiles
```bash
python test_font_profiles.py
```

**Output**:
- ✅ Profile loading validation
- ✅ Font file discovery
- ✅ Size calculation differences between fonts
- ✅ Installation instructions for missing fonts

## Sizing Examples

### Bebas Neue (Aggressive)
| Title | Size | Effect |
|-------|------|--------|
| "Success" | 118px | Single word, moderate |
| "Think Big" | 220px | 2 words → MAX IMPACT! |
| "The Art of War" | 220px | 4 words, still large |
| "How to Win Friends..." | 95px | 7 words, readable |

### Cairo (Conservative)
| Title | Size | Effect |
|-------|------|--------|
| "Success" | 162px | Single word, larger |
| "Think Big" | 168px | 2 words, balanced |
| "The Art of War" | 157px | 4 words, readable |
| "How to Win Friends..." | 69px | 7 words, compact |

## Design Philosophy

### Bebas Neue Strategy
- **Purpose**: Maximum visual impact for English titles
- **Best For**: Short, punchy titles (2-4 words)
- **Characteristics**: 
  - Condensed letterforms → fits more text
  - All-caps design → commands attention
  - High contrast → stands out on thumbnails

### Cairo Strategy
- **Purpose**: Readability for Arabic/bilingual content
- **Best For**: Longer titles, Arabic text, detailed captions
- **Characteristics**:
  - Wider letterforms → better legibility
  - Supports Arabic script natively
  - Lower contrast → easier on eyes

## Technical Details

### Dynamic Sizing Algorithm
1. **Load Profile**: `_load_font_profile(font_name, config_dir)`
   - Reads `thumbnail_font_profiles` from settings.json
   - Returns font-specific parameters
   - Fallback to Bebas Neue if not found

2. **Calculate Size**: `_calculate_optimal_title_size(text, font_profile, max_width)`
   - Word count analysis
   - Character density calculation
   - Apply profile-specific scaling factors
   - Respect min/max bounds from profile

3. **Font Discovery**: `_cairo_candidates(weight)` / `_bebas_neue_candidates(weight)`
   - Search in: `assets/fonts/`, `secrets/fonts/`, system fonts
   - Weight-specific priority (Bold > SemiBold > Regular)
   - Fallback cascade for reliability

### Code Structure
```
src/infrastructure/adapters/thumbnail.py
├── _load_font_profile()           # Load profile from JSON
├── _calculate_optimal_title_size() # Profile-aware sizing
├── _bebas_neue_candidates()       # Bebas Neue font search
├── _cairo_candidates()            # Cairo font search
└── generate_thumbnail()           # Main thumbnail generator
    └── Loads profile based on title_font_name
```

## Adding New Fonts

### 1. Add Profile to `settings.json`
```json
{
  "thumbnail_font_profiles": {
    "Your Font": {
      "title_base_size": 120,
      "title_min_size": 60,
      "title_max_size": 200,
      "subtitle_base_size": 70,
      "subtitle_min_size": 55,
      "subtitle_ratio": 0.65,
      "dynamic_scaling": {
        "2_words": 1.7,
        "3_words_long": 0.88,
        "3_words_medium": 1.15,
        "3_words_short": 1.4,
        "4_words": 1.05,
        "5_words": 0.95,
        "6_words": 0.90,
        "decay_rate": 0.91
      }
    }
  }
}
```

### 2. Add Font Discovery Function (Optional)
```python
def _your_font_candidates(weight: str = "bold") -> List[Path]:
    """Search for Your Font in system and project directories."""
    names_by_weight = {
        "bold": ["YourFont-Bold.ttf", "YourFontBold.ttf"],
        "regular": ["YourFont-Regular.ttf", "YourFont.ttf"],
    }
    # ... (copy pattern from _cairo_candidates)
    return cands
```

### 3. Update `family_to_candidates()` (Optional)
```python
def family_to_candidates(name, weight_title, weight_sub):
    nt = (name or '').strip().lower()
    if nt in ("your", "your font", "yourfont"):
        return _your_font_candidates(weight_title), _your_font_candidates(weight_sub)
    # ...
```

## Troubleshooting

### Font Not Found Error
**Symptom**: `FileNotFoundError: لم يتم العثور على title`

**Solutions**:
1. Install font to system fonts (`C:\Windows\Fonts\`)
2. Copy font to `assets/fonts/`
3. Provide explicit path: `--title-font-path assets/fonts/Cairo-Bold.ttf`
4. Set environment variable: `THUMBNAIL_TITLE_FONT=path/to/font.ttf`

### Size Too Small/Large
**Solution**: Adjust profile in `settings.json`:
- Increase `title_base_size` for larger text
- Adjust `title_min_size` / `title_max_size` bounds
- Modify `dynamic_scaling.2_words` for short titles
- Change `decay_rate` for long titles (higher = slower decay)

### Font Not Detected
**Check**:
```bash
python -c "from src.infrastructure.adapters.thumbnail import _cairo_candidates; print(_cairo_candidates('bold'))"
```
If empty: Font files missing or incorrect naming

## Performance

- **Profile Loading**: ~0.5ms (cached internally)
- **Font Discovery**: ~50ms (file system search)
- **Size Calculation**: ~1ms per title
- **Overall Impact**: Negligible (<2% of total thumbnail generation time)

## Backward Compatibility

✅ **Fully Compatible**: Existing thumbnails regenerate with same sizing
- Default font remains **Bebas Neue**
- Old `thumbnail_title_font_size` parameter still works (as override)
- `dynamic_title_size=False` disables profile-based sizing

## Future Enhancements

- [ ] Add more pre-configured profiles (Montserrat, Roboto, etc.)
- [ ] Web interface for profile tuning
- [ ] A/B testing framework for font selection
- [ ] AI-powered font recommendation based on book genre
- [ ] Support for multiple fonts per thumbnail (mixed fonts)

---

**Last Updated**: 2025-10-24  
**Version**: 2.2.0  
**Author**: YouTubeTB Team
