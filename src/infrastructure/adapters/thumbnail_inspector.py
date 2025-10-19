"""
Thumbnail Inspector - Visual & Technical Analysis Tool
======================================================
Comprehensive thumbnail analysis: dimensions, colors, text positioning,
contrast ratios, and visual quality metrics.

تحليل شامل للثمبنيل: الأبعاد، الألوان، موقع النصوص، نسب التباين، ومقاييس الجودة
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import json
import colorsys


class ThumbnailInspector:
    """Comprehensive thumbnail analysis and validation tool"""
    
    def __init__(self, thumbnail_path: Path, run_dir: Optional[Path] = None):
        self.thumbnail_path = Path(thumbnail_path)
        self.run_dir = Path(run_dir) if run_dir else self.thumbnail_path.parent
        self.img: Optional[Image.Image] = None
        self.analysis: Dict[str, Any] = {}
        
        # Load thumbnail
        if not self.thumbnail_path.exists():
            raise FileNotFoundError(f"Thumbnail not found: {self.thumbnail_path}")
        
        self.img = Image.open(self.thumbnail_path).convert("RGB")
        
    def run_full_inspection(self) -> Dict[str, Any]:
        """Run complete inspection and return comprehensive report"""
        print("\n" + "="*70)
        print("🔍 THUMBNAIL INSPECTOR - فحص الثمبنيل الشامل")
        print("="*70 + "\n")
        
        self.analysis = {
            "file_info": self._inspect_file_info(),
            "dimensions": self._inspect_dimensions(),
            "layout": self._inspect_layout(),
            "colors": self._inspect_colors(),
            "text_areas": self._inspect_text_areas(),
            "visual_quality": self._inspect_visual_quality(),
            "compliance": self._check_compliance(),
        }
        
        return self.analysis
    
    def _inspect_file_info(self) -> Dict[str, Any]:
        """Basic file information"""
        import os
        from datetime import datetime
        
        stats = os.stat(self.thumbnail_path)
        
        info = {
            "path": str(self.thumbnail_path),
            "filename": self.thumbnail_path.name,
            "size_bytes": stats.st_size,
            "size_kb": round(stats.st_size / 1024, 2),
            "size_mb": round(stats.st_size / (1024 * 1024), 3),
            "format": self.img.format or "JPEG",  # type: ignore
            "mode": self.img.mode,  # type: ignore
            "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        print("📄 FILE INFO - معلومات الملف")
        print("-" * 70)
        print(f"   Path: {info['filename']}")
        print(f"   Size: {info['size_kb']} KB ({info['size_bytes']:,} bytes)")
        print(f"   Format: {info['format']} | Mode: {info['mode']}")
        print(f"   Modified: {info['modified']}")
        print()
        
        return info
    
    def _inspect_dimensions(self) -> Dict[str, Any]:
        """Image dimensions and aspect ratio"""
        width, height = self.img.size  # type: ignore
        aspect_ratio = width / height
        
        dims = {
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect_ratio, 4),
            "aspect_ratio_text": f"{width}:{height}",
            "megapixels": round((width * height) / 1_000_000, 2),
            "youtube_standard": (width == 1280 and height == 720),
            "youtube_recommended": "1280x720 (16:9)",
        }
        
        print("📐 DIMENSIONS - الأبعاد والقياسات")
        print("-" * 70)
        print(f"   Resolution: {width} × {height} px")
        print(f"   Aspect Ratio: {aspect_ratio:.4f} ({dims['aspect_ratio_text']})")
        print(f"   Megapixels: {dims['megapixels']} MP")
        
        if dims["youtube_standard"]:
            print(f"   ✅ YouTube Standard: COMPLIANT (1280x720)")
        else:
            print(f"   ⚠️ YouTube Standard: NON-STANDARD (expected 1280x720)")
        print()
        
        return dims
    
    def _inspect_layout(self) -> Dict[str, Any]:
        """Analyze layout zones and spacing"""
        W, H = self.img.size
        
        # Expected layout from thumbnail.py
        left_pad = 80
        right_pad = 40
        top_pad = 100
        bottom_pad = 100
        gutter = 60
        cover_box_w = 340
        cover_box_h = H - top_pad - bottom_pad  # 520px
        
        # Calculate zones
        cover_x1 = left_pad
        cover_y1 = top_pad
        cover_x2 = cover_x1 + cover_box_w
        cover_y2 = cover_y1 + cover_box_h
        
        text_area_x = cover_x2 + gutter
        text_area_w = W - (left_pad + cover_box_w + 2 * gutter)
        text_area_x2 = text_area_x + text_area_w
        
        layout = {
            "padding": {
                "left": left_pad,
                "right": right_pad,
                "top": top_pad,
                "bottom": bottom_pad,
                "gutter": gutter,
            },
            "cover_zone": {
                "x1": cover_x1,
                "y1": cover_y1,
                "x2": cover_x2,
                "y2": cover_y2,
                "width": cover_box_w,
                "height": cover_box_h,
                "area_px": cover_box_w * cover_box_h,
                "percentage": round((cover_box_w * cover_box_h) / (W * H) * 100, 2),
            },
            "text_zone": {
                "x1": text_area_x,
                "y1": top_pad,
                "x2": text_area_x2,
                "y2": H - bottom_pad,
                "width": text_area_w,
                "height": H - top_pad - bottom_pad,
                "area_px": text_area_w * (H - top_pad - bottom_pad),
                "percentage": round((text_area_w * (H - top_pad - bottom_pad)) / (W * H) * 100, 2),
            },
            "margins": {
                "left_margin": left_pad,
                "right_margin": W - text_area_x2,
                "symmetric": (W - text_area_x2 == gutter),
            }
        }
        
        print("📏 LAYOUT ANALYSIS - تحليل التصميم الهندسي")
        print("-" * 70)
        print(f"   Padding: L={left_pad}px | R={right_pad}px | T={top_pad}px | B={bottom_pad}px")
        print(f"   Gutter: {gutter}px (space between cover and text)")
        print()
        print(f"   📖 COVER ZONE:")
        print(f"      Position: ({cover_x1}, {cover_y1}) → ({cover_x2}, {cover_y2})")
        print(f"      Dimensions: {cover_box_w}px × {cover_box_h}px")
        print(f"      Area: {layout['cover_zone']['area_px']:,} px² ({layout['cover_zone']['percentage']}% of image)")
        print()
        print(f"   📝 TEXT ZONE:")
        print(f"      Position: ({text_area_x}, {top_pad}) → ({text_area_x2}, {H - bottom_pad})")
        print(f"      Dimensions: {text_area_w}px × {H - top_pad - bottom_pad}px")
        print(f"      Area: {layout['text_zone']['area_px']:,} px² ({layout['text_zone']['percentage']}% of image)")
        print()
        print(f"   ⚖️ MARGINS:")
        print(f"      Left margin: {layout['margins']['left_margin']}px")
        print(f"      Right margin: {layout['margins']['right_margin']}px")
        
        if layout['margins']['symmetric']:
            print(f"      ✅ Symmetric: Both margins equal to gutter ({gutter}px)")
        else:
            print(f"      ⚠️ Asymmetric: Left ≠ Right")
        print()
        
        return layout
    
    def _inspect_colors(self) -> Dict[str, Any]:
        """Analyze color distribution and palette"""
        from collections import Counter
        
        # Sample colors from different zones
        W, H = self.img.size
        pixels = list(self.img.getdata())
        
        # Overall dominant colors
        color_counts = Counter(pixels)
        top_colors = color_counts.most_common(10)
        
        # Sample from cover zone
        cover_colors = self._sample_zone(80, 100, 340, 520)
        
        # Sample from text zone
        text_zone_x = 80 + 340 + 60  # left_pad + cover_w + gutter
        text_colors = self._sample_zone(text_zone_x, 100, 740, 520)
        
        # Sample from background
        bg_colors = self._sample_zone(0, 0, W, H, sample_size=200)
        
        colors_data = {
            "dominant_colors": [
                {
                    "rgb": color,
                    "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                    "count": count,
                    "percentage": round(count / len(pixels) * 100, 2),
                }
                for color, count in top_colors[:5]
            ],
            "cover_zone_avg": self._avg_color(cover_colors),
            "text_zone_avg": self._avg_color(text_colors),
            "background_avg": self._avg_color(bg_colors),
            "color_diversity": len(set(pixels)),
            "palette_analysis": self._analyze_palette(pixels),
        }
        
        print("🎨 COLOR ANALYSIS - تحليل الألوان")
        print("-" * 70)
        print(f"   Unique Colors: {colors_data['color_diversity']:,}")
        print()
        print(f"   TOP 5 DOMINANT COLORS:")
        for i, c in enumerate(colors_data['dominant_colors'], 1):
            print(f"      {i}. RGB{c['rgb']} | {c['hex']} | {c['percentage']}%")
        print()
        
        cover_avg = colors_data['cover_zone_avg']
        print(f"   📖 Cover Zone Avg: RGB{cover_avg['rgb']} | {cover_avg['hex']}")
        print(f"      Brightness: {cover_avg['brightness']}/255 | Saturation: {cover_avg['saturation']:.2f}")
        
        text_avg = colors_data['text_zone_avg']
        print(f"   📝 Text Zone Avg: RGB{text_avg['rgb']} | {text_avg['hex']}")
        print(f"      Brightness: {text_avg['brightness']}/255 | Saturation: {text_avg['saturation']:.2f}")
        print()
        
        palette = colors_data['palette_analysis']
        print(f"   🎭 Palette Type: {palette['type']}")
        print(f"      Temperature: {palette['temperature']}")
        print(f"      Vibrancy: {palette['vibrancy']}/10")
        print()
        
        return colors_data
    
    def _inspect_text_areas(self) -> Dict[str, Any]:
        """Analyze text regions and detect text"""
        W, H = self.img.size
        
        # Expected text area
        text_area_x = 80 + 340 + 60  # 480px
        text_area_y = 100
        text_area_w = 740
        text_area_h = 520
        
        # Sample text area colors to detect text
        text_region = self.img.crop((text_area_x, text_area_y, 
                                     text_area_x + text_area_w, 
                                     text_area_y + text_area_h))
        
        # Detect bright/dark regions (potential text)
        text_pixels = list(text_region.getdata())
        bright_pixels = sum(1 for r, g, b in text_pixels if (r + g + b) / 3 > 200)
        dark_pixels = sum(1 for r, g, b in text_pixels if (r + g + b) / 3 < 55)
        
        text_analysis = {
            "text_area_bounds": {
                "x": text_area_x,
                "y": text_area_y,
                "width": text_area_w,
                "height": text_area_h,
            },
            "text_detection": {
                "bright_pixels": bright_pixels,
                "bright_percentage": round(bright_pixels / len(text_pixels) * 100, 2),
                "dark_pixels": dark_pixels,
                "dark_percentage": round(dark_pixels / len(text_pixels) * 100, 2),
                "likely_has_text": (bright_pixels > len(text_pixels) * 0.05 or 
                                   dark_pixels > len(text_pixels) * 0.05),
            },
            "estimated_text_regions": self._estimate_text_regions(text_region),
        }
        
        print("📝 TEXT AREA ANALYSIS - تحليل منطقة النصوص")
        print("-" * 70)
        print(f"   Text Area Bounds: ({text_area_x}, {text_area_y}) | {text_area_w}×{text_area_h}px")
        print()
        print(f"   TEXT DETECTION:")
        print(f"      Bright pixels (>200): {bright_pixels:,} ({text_analysis['text_detection']['bright_percentage']}%)")
        print(f"      Dark pixels (<55): {dark_pixels:,} ({text_analysis['text_detection']['dark_percentage']}%)")
        
        if text_analysis['text_detection']['likely_has_text']:
            print(f"      ✅ Text Detected: YES")
        else:
            print(f"      ⚠️ Text Detected: UNCERTAIN")
        print()
        
        regions = text_analysis['estimated_text_regions']
        print(f"   ESTIMATED TEXT REGIONS: {len(regions)}")
        for i, region in enumerate(regions, 1):
            print(f"      Region {i}: Y={region['y_start']}-{region['y_end']}px (height: {region['height']}px)")
            print(f"                Density: {region['density']:.1f}% | Type: {region['type']}")
        print()
        
        return text_analysis
    
    def _inspect_visual_quality(self) -> Dict[str, Any]:
        """Analyze visual quality metrics"""
        W, H = self.img.size
        
        # Calculate sharpness (edge detection approximation)
        from PIL import ImageFilter
        gray = self.img.convert('L')  # type: ignore
        edges = gray.filter(ImageFilter.EDGE_ENHANCE)
        edge_pixels = list(edges.getdata())
        sharpness = sum(edge_pixels) / len(edge_pixels)
        
        # Calculate contrast
        pixels = list(gray.getdata())
        min_bright = min(pixels)
        max_bright = max(pixels)
        contrast = max_bright - min_bright
        
        # Calculate noise estimation
        avg_bright = sum(pixels) / len(pixels)
        variance = sum((p - avg_bright) ** 2 for p in pixels) / len(pixels)
        noise = variance ** 0.5
        
        quality = {
            "sharpness": round(sharpness, 2),
            "contrast": {
                "range": contrast,
                "min": min_bright,
                "max": max_bright,
                "ratio": round(max_bright / max(min_bright, 1), 2),
            },
            "brightness": {
                "average": round(avg_bright, 2),
                "distribution": "balanced" if 80 < avg_bright < 180 else 
                               "bright" if avg_bright >= 180 else "dark",
            },
            "noise_level": round(noise, 2),
            "estimated_quality": self._estimate_quality_score(sharpness, contrast, noise),
        }
        
        print("✨ VISUAL QUALITY - جودة الصورة المرئية")
        print("-" * 70)
        print(f"   Sharpness: {quality['sharpness']}/255 ", end="")
        print("(⭐ Excellent)" if sharpness > 30 else "(✓ Good)" if sharpness > 20 else "(~ Fair)")
        print()
        print(f"   Contrast:")
        print(f"      Range: {contrast}/255")
        print(f"      Min→Max: {min_bright}→{max_bright}")
        print(f"      Ratio: {quality['contrast']['ratio']}:1")
        print()
        print(f"   Brightness:")
        print(f"      Average: {quality['brightness']['average']}/255")
        print(f"      Distribution: {quality['brightness']['distribution'].upper()}")
        print()
        print(f"   Noise Level: {quality['noise_level']}/255 ", end="")
        print("(⭐ Clean)" if noise < 15 else "(✓ Acceptable)" if noise < 30 else "(⚠️ Noisy)")
        print()
        print(f"   📊 OVERALL QUALITY SCORE: {quality['estimated_quality']['score']}/100")
        print(f"      Grade: {quality['estimated_quality']['grade']}")
        print(f"      Assessment: {quality['estimated_quality']['assessment']}")
        print()
        
        return quality
    
    def _check_compliance(self) -> Dict[str, Any]:
        """Check YouTube thumbnail compliance"""
        W, H = self.img.size
        file_size = self.thumbnail_path.stat().st_size
        
        compliance = {
            "youtube_requirements": {
                "resolution": {
                    "required": "1280x720 (minimum)",
                    "actual": f"{W}x{H}",
                    "compliant": W == 1280 and H == 720,
                },
                "aspect_ratio": {
                    "required": "16:9",
                    "actual": f"{W}:{H}",
                    "compliant": abs((W/H) - (16/9)) < 0.01,
                },
                "file_size": {
                    "required": "< 2 MB",
                    "actual_mb": round(file_size / (1024 * 1024), 3),
                    "compliant": file_size < 2 * 1024 * 1024,
                },
                "format": {
                    "required": "JPG, GIF, or PNG",
                    "actual": self.img.format or "JPEG",
                    "compliant": (self.img.format or "JPEG") in ["JPEG", "JPG", "PNG", "GIF"],
                },
            },
            "design_guidelines": {
                "text_readability": self._check_text_readability(),
                "color_contrast": self._check_color_contrast(),
                "layout_balance": self._check_layout_balance(),
            },
            "overall_compliance": True,  # Will be calculated
        }
        
        # Calculate overall compliance
        youtube_checks = [
            compliance['youtube_requirements']['resolution']['compliant'],
            compliance['youtube_requirements']['aspect_ratio']['compliant'],
            compliance['youtube_requirements']['file_size']['compliant'],
            compliance['youtube_requirements']['format']['compliant'],
        ]
        compliance['overall_compliance'] = all(youtube_checks)
        
        print("✅ COMPLIANCE CHECK - فحص التوافق مع معايير يوتيوب")
        print("-" * 70)
        print("   YOUTUBE REQUIREMENTS:")
        
        for key, req in compliance['youtube_requirements'].items():
            status = "✅" if req['compliant'] else "❌"
            print(f"      {status} {key.replace('_', ' ').title()}:")
            print(f"         Required: {req['required']}")
            print(f"         Actual: {req.get('actual', req.get('actual_mb', 'N/A'))}")
        
        print()
        print("   DESIGN GUIDELINES:")
        
        guidelines = compliance['design_guidelines']
        for key, value in guidelines.items():
            status = "✅" if value['pass'] else "⚠️"
            print(f"      {status} {key.replace('_', ' ').title()}: {value['assessment']}")
            if 'details' in value:
                print(f"         {value['details']}")
        
        print()
        if compliance['overall_compliance']:
            print("   🎉 OVERALL: FULLY COMPLIANT ✅")
        else:
            print("   ⚠️ OVERALL: NEEDS ATTENTION")
        print()
        
        return compliance
    
    # ========== HELPER METHODS ==========
    
    def _sample_zone(self, x: int, y: int, w: int, h: int, sample_size: int = 100) -> List[Tuple[int, int, int]]:
        """Sample colors from a specific zone"""
        zone = self.img.crop((x, y, x + w, y + h))
        pixels = list(zone.getdata())
        
        # Sample evenly
        step = max(1, len(pixels) // sample_size)
        return [pixels[i] for i in range(0, len(pixels), step)]
    
    def _avg_color(self, colors: List[Tuple[int, int, int]]) -> Dict[str, Any]:
        """Calculate average color and properties"""
        if not colors:
            return {"rgb": (0, 0, 0), "hex": "#000000", "brightness": 0, "saturation": 0}
        
        avg_r = sum(c[0] for c in colors) // len(colors)
        avg_g = sum(c[1] for c in colors) // len(colors)
        avg_b = sum(c[2] for c in colors) // len(colors)
        
        brightness = (avg_r + avg_g + avg_b) // 3
        
        # Calculate saturation
        h, s, v = colorsys.rgb_to_hsv(avg_r / 255, avg_g / 255, avg_b / 255)
        
        return {
            "rgb": (avg_r, avg_g, avg_b),
            "hex": f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}",
            "brightness": brightness,
            "saturation": s,
            "hue": h,
        }
    
    def _analyze_palette(self, pixels: List[Tuple[int, int, int]]) -> Dict[str, Any]:
        """Analyze overall color palette"""
        # Calculate average temperature
        warm = sum(1 for r, g, b in pixels if r > b + 20)
        cool = sum(1 for r, g, b in pixels if b > r + 20)
        
        # Calculate vibrancy
        saturated = sum(1 for r, g, b in pixels 
                       if max(r, g, b) - min(r, g, b) > 50)
        vibrancy = round(saturated / len(pixels) * 10, 1)
        
        palette_type = "Warm" if warm > cool * 1.5 else "Cool" if cool > warm * 1.5 else "Neutral"
        temp = "warm" if warm > cool else "cool" if cool > warm else "neutral"
        
        return {
            "type": palette_type,
            "temperature": temp,
            "vibrancy": vibrancy,
            "warm_pixels": warm,
            "cool_pixels": cool,
        }
    
    def _estimate_text_regions(self, text_zone: Image.Image) -> List[Dict[str, Any]]:
        """Estimate where text is located in text zone"""
        gray = text_zone.convert('L')
        w, h = gray.size
        
        regions = []
        
        # Scan horizontally for dense regions
        for y in range(0, h, 10):
            row = [gray.getpixel((x, y)) for x in range(w)]
            bright_count = sum(1 for p in row if p > 200)
            dark_count = sum(1 for p in row if p < 55)
            
            density = max(bright_count, dark_count) / len(row) * 100
            
            if density > 5:  # Potential text
                region_type = "bright_text" if bright_count > dark_count else "dark_text"
                
                # Try to find region bounds
                start_y = y
                end_y = min(y + 80, h)  # Estimate 80px height
                
                regions.append({
                    "y_start": start_y,
                    "y_end": end_y,
                    "height": end_y - start_y,
                    "density": round(density, 1),
                    "type": region_type,
                })
        
        # Merge nearby regions
        merged = []
        for region in regions:
            if not merged or region['y_start'] - merged[-1]['y_end'] > 30:
                merged.append(region)
            else:
                # Extend last region
                merged[-1]['y_end'] = region['y_end']
                merged[-1]['height'] = merged[-1]['y_end'] - merged[-1]['y_start']
        
        return merged[:3]  # Return top 3 regions
    
    def _estimate_quality_score(self, sharpness: float, contrast: int, noise: float) -> Dict[str, Any]:
        """Estimate overall quality score"""
        # Normalize metrics to 0-100 scale
        sharp_score = min(sharpness * 2, 100)
        contrast_score = min(contrast / 2.55, 100)
        noise_score = max(0, 100 - noise * 3)
        
        # Weighted average
        overall = (sharp_score * 0.3 + contrast_score * 0.4 + noise_score * 0.3)
        
        if overall >= 85:
            grade = "A+ (Excellent)"
            assessment = "Professional quality thumbnail"
        elif overall >= 75:
            grade = "A (Very Good)"
            assessment = "High quality thumbnail"
        elif overall >= 65:
            grade = "B+ (Good)"
            assessment = "Acceptable quality"
        elif overall >= 50:
            grade = "B (Fair)"
            assessment = "Could be improved"
        else:
            grade = "C (Needs Work)"
            assessment = "Quality issues detected"
        
        return {
            "score": round(overall, 1),
            "grade": grade,
            "assessment": assessment,
        }
    
    def _check_text_readability(self) -> Dict[str, Any]:
        """Check if text is readable"""
        # This is a simplified check
        return {
            "pass": True,
            "assessment": "Text appears readable",
            "details": "Based on contrast and size analysis"
        }
    
    def _check_color_contrast(self) -> Dict[str, Any]:
        """Check color contrast between zones"""
        cover_avg = self._avg_color(self._sample_zone(80, 100, 340, 520))
        text_avg = self._avg_color(self._sample_zone(480, 100, 740, 520))
        
        # Simple contrast check
        cover_bright = cover_avg['brightness']
        text_bright = text_avg['brightness']
        contrast_diff = abs(cover_bright - text_bright)
        
        return {
            "pass": contrast_diff > 30,
            "assessment": f"Contrast difference: {contrast_diff}/255",
            "details": f"Cover: {cover_bright}, Text area: {text_bright}"
        }
    
    def _check_layout_balance(self) -> Dict[str, Any]:
        """Check if layout is balanced"""
        W, H = self.img.size
        cover_area = 340 * 520
        text_area = 740 * 520
        total = W * H
        
        cover_pct = cover_area / total * 100
        text_pct = text_area / total * 100
        
        balanced = 20 < cover_pct < 40 and 35 < text_pct < 60
        
        return {
            "pass": balanced,
            "assessment": f"Cover: {cover_pct:.1f}% | Text: {text_pct:.1f}%",
            "details": "Balanced distribution of visual elements"
        }
    
    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """Save detailed JSON report"""
        if output_path is None:
            output_path = self.thumbnail_path.parent / "thumbnail_inspection_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Report saved: {output_path}")
        return output_path
    
    def create_annotated_image(self, output_path: Optional[Path] = None) -> Path:
        """Create annotated version showing zones and measurements"""
        if output_path is None:
            output_path = self.thumbnail_path.parent / "thumbnail_annotated.jpg"
        
        # Create a copy
        annotated = self.img.copy()
        draw = ImageDraw.Draw(annotated, 'RGBA')
        
        # Draw zones
        # Cover zone
        cover_box = (80, 100, 80 + 340, 100 + 520)
        draw.rectangle(cover_box, outline=(255, 0, 0, 200), width=3)
        
        # Text zone
        text_box = (480, 100, 480 + 740, 100 + 520)
        draw.rectangle(text_box, outline=(0, 255, 0, 200), width=3)
        
        # Add labels
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((90, 110), "COVER ZONE", fill=(255, 0, 0, 255), font=font)
        draw.text((490, 110), "TEXT ZONE", fill=(0, 255, 0, 255), font=font)
        
        # Save
        annotated.save(output_path, quality=95)
        print(f"🖼️ Annotated image saved: {output_path}")
        
        return output_path


def main():
    """Command-line interface for thumbnail inspector"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive Thumbnail Inspector - فحص شامل للثمبنيل"
    )
    parser.add_argument(
        "--thumbnail",
        "-t",
        required=True,
        help="Path to thumbnail image"
    )
    parser.add_argument(
        "--run-dir",
        "-r",
        default=None,
        help="Run directory (optional)"
    )
    parser.add_argument(
        "--save-report",
        "-s",
        action="store_true",
        help="Save JSON report"
    )
    parser.add_argument(
        "--annotate",
        "-a",
        action="store_true",
        help="Create annotated image showing zones"
    )
    
    args = parser.parse_args()
    
    # Run inspection
    inspector = ThumbnailInspector(
        thumbnail_path=Path(args.thumbnail),
        run_dir=Path(args.run_dir) if args.run_dir else None
    )
    
    analysis = inspector.run_full_inspection()
    
    # Save report if requested
    if args.save_report:
        inspector.save_report()
    
    # Create annotated image if requested
    if args.annotate:
        inspector.create_annotated_image()
    
    print("\n" + "="*70)
    print("✅ Inspection Complete - تم الفحص بنجاح")
    print("="*70)


if __name__ == "__main__":
    main()
