from __future__ import annotations

from pathlib import Path
from typing import Optional
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urlparse
from urllib.request import url2pathname

try:
    from PIL import Image, ImageEnhance  # type: ignore
except Exception:
    Image = None  # type: ignore
    ImageEnhance = None  # type: ignore


def _ensure_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _load_json_settings(json_path: Path) -> Optional[dict]:
    if not json_path.exists():
        return None
    try:
        with json_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)
        # normalize cover_image to file URI when local path
        img = settings.get("cover_image")
        if isinstance(img, str) and img and os.path.exists(img):
            settings["cover_image"] = Path(img).absolute().as_uri()
        return settings
    except Exception:
        return None


def _cinematic_classic(img):
    # If Pillow is not available, return image as-is
    if Image is None or ImageEnhance is None:
        return img
    img = img.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.2)
    r, g, b = img.split()
    r = r.point(lambda i: i * 1.1)
    b = b.point(lambda i: i * 1.2)
    img = Image.merge("RGB", (r, g, b))
    img = ImageEnhance.Brightness(img).enhance(0.95)
    return img


def _resolve_local_path(uri_or_path: str) -> Optional[Path]:
    try:
        if uri_or_path.startswith("file:"):
            p = urlparse(uri_or_path)
            local_path = url2pathname(p.path)
            if os.path.exists(local_path):
                return Path(local_path)
            # On Windows, path may start with /C:/
            if local_path.startswith("/") and os.path.exists(local_path[1:]):
                return Path(local_path[1:])
        else:
            if os.path.exists(uri_or_path):
                return Path(uri_or_path)
    except Exception:
        return None
    return None


def _maybe_apply_cinematic_to_cover(settings: dict, work_dir: Path) -> None:
    try:
        cover = settings.get("cover_image")
        if not isinstance(cover, str) or not cover:
            return
        src_path = _resolve_local_path(cover)
        if src_path is None:
            # Non-local (http/https) or not found → skip silently
            return
        if Image is None:
            # Pillow not installed → skip silently
            return
        # Open, apply effect, save to temp file
        with Image.open(src_path) as im:  # type: ignore[attr-defined]
            processed = _cinematic_classic(im)
            out_path = work_dir / "cover_processed.jpg"
            processed.save(out_path, format="JPEG", quality=90)
        settings["cover_image"] = out_path.absolute().as_uri()
    except Exception:
        # No hard failure if processing fails
        pass


async def _apply_json_to_page(page, settings: dict) -> None:
    async def set_input_value(element_id: str, value: str) -> None:
        try:
            await page.evaluate(
                """({id, val}) => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""",
                {"id": element_id, "val": value},
            )
        except Exception:
            pass

    # cover image
    if "cover_image" in settings:
        try:
            await page.evaluate(
                """(url) => {
                    const coverArt = document.getElementById('cover-art');
                    const blurredBg = document.getElementById('blurred-bg');
                    if (coverArt && blurredBg) {
                        coverArt.src = url;
                        blurredBg.style.backgroundImage = `url(${url})`;
                    }
                }""",
                settings["cover_image"],
            )
        except Exception:
            pass

    # text inputs
    text_map = [
        ("top-title-input", "top_title"),
        ("main-title-input", "main_title"),
        ("subtitle-input", "subtitle"),
        ("footer-input", "footer"),
    ]
    for input_id, key in text_map:
        if key in settings:
            await set_input_value(input_id, settings[key])

    # optional font size overrides (in px or CSS size string)
    try:
        font_map = [
            ("top-title-preview", "top_title_font_px"),
            ("footer-preview", "footer_font_px"),
        ]
        for el_id, key in font_map:
            if key in settings:
                size_val = settings.get(key)
                await page.evaluate(
                    """({id, size}) => {
                        const el = document.getElementById(id);
                        if (el) {
                            const s = (typeof size === 'number') ? `${size}px` : String(size);
                            el.style.fontSize = s;
                        }
                    }""",
                    {"id": el_id, "size": size_val},
                )
    except Exception:
        pass


async def _capture_cfr_frames(
    html_path: Path,
    out_dir: Path,
    selector: str,
    fps: int,
    duration: float,
    width: int,
    height: int,
    dpr: float,
    jpeg_quality: int,
    settings: Optional[dict],
):
    from playwright.async_api import async_playwright

    file_url = html_path.absolute().as_uri()
    out_dir.mkdir(parents=True, exist_ok=True)
    total_frames = int(round(duration * fps))

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=dpr,
        )

        await context.add_init_script(
            """
(() => {
  const pauseAll = () => {
    try {
      const anims = document.getAnimations ? document.getAnimations() : [];
      for (const a of anims) { try { a.pause(); a.currentTime = 0; } catch(e){} }
    } catch(e){}
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', pauseAll, {once:true});
  } else {
    pauseAll();
  }
  window.__advanceToTime = (ms) => {
    try {
      const anims = document.getAnimations ? document.getAnimations() : [];
      for (const a of anims) { try { a.currentTime = ms; } catch(e){} }
    } catch(e){}
  };
})();
            """
        )

        page = await context.new_page()
        await page.goto(file_url)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        await asyncio.sleep(0.3)

        if settings:
            await _apply_json_to_page(page, settings)

        # allow assets to load
        await asyncio.sleep(2)
        image_timeout = 4000
        strict_img = False
        if settings:
            try:
                image_timeout = int(settings.get("render_image_timeout_ms", image_timeout))
            except Exception:
                image_timeout = 4000
            try:
                strict_img = bool(settings.get("render_strict_image_load", strict_img))
            except Exception:
                strict_img = False
        try:
            await page.wait_for_function(
                """
                () => {
                    const img = document.getElementById('cover-art');
                    if (!img) return true;
                    return img.complete && typeof img.naturalWidth === 'number' && img.naturalWidth > 0;
                }
                """,
                timeout=image_timeout,
            )
        except Exception:
            if strict_img:
                await browser.close()
                raise RuntimeError("Cover image did not finish loading within timeout and strict mode is enabled.")
            # else: continue without hard failure

        # enforce element size
        await page.evaluate(
            f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.style.width = '{width}px';
                    el.style.height = '{height}px';
                    el.style.maxWidth = '{width}px';
                    el.style.maxHeight = '{height}px';
                    el.style.overflow = 'hidden';
                }}
            }}
            """
        )

        handle = await page.query_selector(selector)
        if not handle:
            await browser.close()
            raise RuntimeError(f"Element not found: {selector}")

        start = time.time()
        for i in range(total_frames):
            target_ms = (i / fps) * 1000.0
            await page.evaluate("ms => window.__advanceToTime(ms)", target_ms)
            frame_path = out_dir / f"frame_{i:06d}.jpg"
            await handle.screenshot(path=str(frame_path), type="jpeg", quality=jpeg_quality)
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start
                _ = (i + 1) / elapsed if elapsed > 0 else 0
            await asyncio.sleep(0)

        await browser.close()
    return total_frames


def _build_video_from_images(frames_dir: Path, fps: int, out_file: Path, width: int, height: int) -> None:
    pattern = frames_dir / "frame_%06d.jpg"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(pattern.as_posix()),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-tune", "film",
        "-movflags", "+faststart",
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-r", str(fps),
        str(out_file),
    ]
    subprocess.run(cmd, check=True)


def main(
    titles_json: Path,
    settings_json: Path,
    template_html: Path,
    narration_mp3: Path,
    output_mp4: Path,
) -> Optional[Path]:
    # narration_mp3 is currently unused (video-only rendering)
    if not _ensure_ffmpeg():
        return None
    if not template_html.exists():
        return None
    settings = _load_json_settings(settings_json)
    if settings is None:
        return None

    # fill defaults
    fps = int(settings.get("fps", 30))
    duration = float(settings.get("duration", 8.0))
    width = int(settings.get("width", 1920))
    height = int(settings.get("height", 1080))

    # Delete old render output if exists (for re-runs)
    if output_mp4.exists():
        try:
            print(f"🗑️ Deleting old render: {output_mp4.name}")
            output_mp4.unlink()
        except Exception as e:
            print(f"⚠️ Could not delete old render: {e}")

    tmp_dir = Path(tempfile.mkdtemp(prefix="html_frames_cfr_"))
    try:
        # Optionally apply cinematic effect to local cover image and point settings to processed copy
        _maybe_apply_cinematic_to_cover(settings, tmp_dir)
        asyncio.run(
            _capture_cfr_frames(
                template_html,
                tmp_dir,
                selector="#video-preview-container",
                fps=fps,
                duration=duration,
                width=width,
                height=height,
                dpr=1.0,
                jpeg_quality=90,
                settings=settings,
            )
        )
        _build_video_from_images(tmp_dir, fps, output_mp4, width, height)
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return output_mp4 if output_mp4.exists() else None
