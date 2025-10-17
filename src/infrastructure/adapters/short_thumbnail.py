"""
Generate vertical thumbnail for YouTube Shorts (1080x1920)
Part of the pipeline for YouTube book video generation
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import json


def _draw_text_with_outline(draw, position, text, font, fill_color, outline_color, outline_width=8):
    """Draw text with strong outline and shadow for maximum visibility"""
    x, y = position

    # Draw shadow first (offset down-right)
    shadow_offset = 4
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0), anchor="mm")

    # Draw outline
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x == 0 and offset_y == 0:
                continue
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=outline_color, anchor="mm")

    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color, anchor="mm")


def main(run_dir, debug=False):
    """
    Generate Short thumbnail (1080x1920) for YouTube Shorts

    Args:
        run_dir: Path to run directory containing output.titles.json and bookcover.jpg
        debug: Print debug messages

    Returns:
        Path to short_thumbnail.jpg or None if failed
    """
    run_dir = Path(run_dir)

    # ==========================================
    # STEP 1: Load Hook from output.titles.json
    # ==========================================
    output_titles_json = run_dir / "output.titles.json"
    hook_text = None

    if output_titles_json.exists():
        try:
            output_titles = json.loads(output_titles_json.read_text(encoding="utf-8"))
            hook_text = output_titles.get("subtitle", "")  # Get hook from main video
            if debug and hook_text:
                print(f"📝 Hook text: {hook_text}")
        except Exception as e:
            if debug:
                print(f"⚠️ Failed to load hook: {e}")

    if not hook_text:
        print("❌ No hook text found in output.titles.json")
        return None

    # ==========================================
    # STEP 2: Find Book Cover
    # ==========================================
    cover_path = None
    for name in ["bookcover.jpg", "bookcover.jpeg", "bookcover.png"]:
        p = run_dir / name
        if p.exists():
            cover_path = p
            break

    if not cover_path:
        print("❌ No book cover found")
        return None

    if debug:
        print(f"📷 Using cover: {cover_path.name}")

    # ==========================================
    # STEP 3: Create Canvas with Blurred Background
    # ==========================================
    W, H = 1080, 1920

    # Load original cover
    cover_original = Image.open(cover_path).convert("RGB")

    # ==========================================
    # LAYER 1: Blurred background (full size)
    # ==========================================
    # Resize to fill entire canvas
    aspect = cover_original.width / cover_original.height
    bg_h = H
    bg_w = int(bg_h * aspect)

    if bg_w < W:
        bg_w = W
        bg_h = int(bg_w / aspect)

    blurred_bg = cover_original.resize((bg_w, bg_h), Image.Resampling.LANCZOS)

    # Center crop
    left = (bg_w - W) // 2
    top = (bg_h - H) // 2
    blurred_bg = blurred_bg.crop((left, top, left + W, top + H))

    # Apply strong Gaussian blur
    blurred_bg = blurred_bg.filter(ImageFilter.GaussianBlur(radius=25))

    if debug:
        print("✓ Created blurred background")

    # ==========================================
    # LAYER 2: Smaller sharp cover (40% size)
    # ==========================================
    # Resize to 40% of canvas
    target_scale = 0.4
    new_h = int(H * target_scale)
    new_w = int(new_h * aspect)

    if new_w < W * target_scale:
        new_w = int(W * target_scale)
        new_h = int(new_w / aspect)

    cover_small = cover_original.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Position lower (shifted down by 150px)
    left = (W - new_w) // 2  # Horizontal center
    top = ((H // 4) - (new_h // 2)) + 150  # Moved down 150px
    blurred_bg.paste(cover_small, (left, top))

    # Store cover position for lighter darkening area
    cover_position = (left, top, left + new_w, top + new_h)

    cover = blurred_bg

    # ==========================================
    # STEP 4: Apply Darkening Layer (75% black with lighter area over cover)
    # ==========================================
    # Create semi-transparent black overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Full darkening (75% = 191 alpha)
    overlay_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 191))

    # Lighter area over book cover (20% = 51 alpha)
    cover_left, cover_top, cover_right, cover_bottom = cover_position
    padding = 50  # Add padding around cover
    overlay_draw.rectangle(
        [cover_left - padding, cover_top - padding,
         cover_right + padding, cover_bottom + padding],
        fill=(0, 0, 0, 51)  # 20% darkening
    )

    # Convert cover to RGBA and apply overlay
    base = cover.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    canvas = base.convert("RGB")

    if debug:
        print("✓ Applied darkening overlay")

    # ==========================================
    # STEP 5: Add Hook Text (Vertical Layout)
    # ==========================================
    draw = ImageDraw.Draw(canvas)

    # Load font (Bebas Neue or Arial Bold)
    font_main = None
    font_paths = [
        Path("C:/Windows/Fonts/BebasNeue-Regular.ttf"),
        Path("assets/fonts/BebasNeue-Regular.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]

    for fp in font_paths:
        if fp.exists():
            try:
                font_main = ImageFont.truetype(str(fp), 180)
                if debug:
                    print(f"✓ Font: {fp.name}")
                break
            except:
                pass

    if not font_main:
        if debug:
            print("⚠️ Using default font")
        font_main = ImageFont.load_default()

    # Split hook into words - one word per line (vertical)
    words = hook_text.split()
    lines = [word.upper() for word in words]

    # Pick random word to highlight in yellow
    import random
    highlight_index = random.randint(0, len(lines) - 1)

    # Draw text centered in bottom 50%
    total_height = len(lines) * 200
    bottom_half_center = H * 0.75  # 75% from top
    start_y = int(bottom_half_center - (total_height // 2)) + 150

    for i, line in enumerate(lines):
        y_pos = start_y + (i * 200)

        # Yellow for highlighted word, white for others
        text_color = (255, 215, 0) if i == highlight_index else (255, 255, 255)

        _draw_text_with_outline(
            draw,
            (W // 2, y_pos),
            line,
            font_main,
            text_color,
            (0, 0, 0),  # Black outline
            outline_width=6
        )

    if debug:
        print(f"✓ Drew {len(lines)} text lines (highlighted: #{highlight_index + 1})")

    # ==========================================
    # STEP 6: Save Thumbnail
    # ==========================================
    output_path = run_dir / "short_thumbnail.jpg"
    canvas.save(output_path, "JPEG", quality=95)

    print(f"✅ Short thumbnail saved: {output_path.name}")

    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline.short_thumbnail <run_directory>")
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        print(f"❌ Run directory not found: {run_dir}")
        sys.exit(1)

    result = main(run_dir, debug=True)

    if result:
        print(f"\n✅ Success: {result}")
    else:
        print("\n❌ Failed to create thumbnail")
        sys.exit(1)
