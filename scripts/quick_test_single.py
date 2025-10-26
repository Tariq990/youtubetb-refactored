#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع - thumbnail واحد 3 كلمات
"""
from pathlib import Path
import sys
import json

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.thumbnail import generate_thumbnail

# مجلد الاختبار
test_dir = repo_root / "tmp" / "quick_test"
test_dir.mkdir(parents=True, exist_ok=True)

# عنوان كتاب آخر
title = "RICH DAD POOR DAD"
author = "BY ROBERT T KIYOSAKI"

print("="*70)
print(f"  🧪 اختبار Thumbnail - {title}")
print("="*70)
print()

# Create metadata
metadata = {
    "youtube_title": f"{title} | Book Summary",
    "thumbnail_title": title,
    "thumbnail_subtitle": author,
    "main_title": title,
    "author_name": author
}

# Create run dir
temp_run = test_dir / "run_single"
temp_run.mkdir(exist_ok=True)

# Save metadata
meta_file = temp_run / "output.titles.json"
with open(meta_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

# Create fake book cover
from PIL import Image
cover = Image.new('RGB', (800, 1200), color=(60, 120, 200))
cover_path = temp_run / "bookcover.jpg"
cover.save(cover_path, 'JPEG')

# Generate thumbnail
print(f"[Thumbnail] إنشاء thumbnail...")
thumb_path = generate_thumbnail(
    run_dir=temp_run,
    titles_json=meta_file,
    debug=True
)

if thumb_path and thumb_path.exists():
    print(f"\n✅ نجح!")
    print(f"📸 الموقع: {thumb_path}")
    
    # Open image
    from PIL import Image
    img = Image.open(thumb_path)
    print(f"📐 الأبعاد: {img.size[0]}x{img.size[1]}")
    img.show()  # فتح الصورة مباشرة
else:
    print(f"\n❌ فشل")
