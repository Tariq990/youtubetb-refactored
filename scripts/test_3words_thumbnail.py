#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار thumbnail مع عناوين 3 كلمات
"""
from pathlib import Path
import sys
import json

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.thumbnail import generate_thumbnail

# مجلد للاختبارات
test_dir = repo_root / "tmp" / "test_3words_thumbnails"
test_dir.mkdir(parents=True, exist_ok=True)

# عناوين اختبارية 3 كلمات
test_titles = [
    ("Build Better Habits", "James Clear"),           # متوازن
    ("Zero To One", "Peter Thiel"),                   # قصير
    ("Extraordinary Life Principles", "Unknown"),      # طويل
    ("Make Good Choices", "Author Name"),             # متوسط
    ("Success Through Discipline", "Napoleon Hill"),  # متوازن
]

print("="*70)
print("  🧪 اختبار Thumbnail - عناوين 3 كلمات")
print("="*70)
print(f"  📂 المجلد: {test_dir}")
print("="*70)
print()

for i, (title, author) in enumerate(test_titles, 1):
    print(f"\n{'='*70}")
    print(f"  اختبار #{i}: {title}")
    print(f"  المؤلف: {author}")
    print(f"{'='*70}\n")
    
    # Create fake metadata
    metadata = {
        "youtube_title": f"{title} | Book Summary",
        "thumbnail_title": title,
        "thumbnail_subtitle": author,
        "main_title": title,
        "author_name": author
    }
    
    # Create temporary metadata file
    temp_meta_file = test_dir / f"test_{i}_meta.json"
    with open(temp_meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # Create temporary run dir structure
    temp_run = test_dir / f"run_{i}"
    temp_run.mkdir(exist_ok=True)
    
    # Copy metadata
    meta_file = temp_run / "output.titles.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # Create fake book cover (simple colored image)
    from PIL import Image
    cover = Image.new('RGB', (800, 1200), color=(100, 100, 150))
    cover_path = temp_run / "bookcover.jpg"
    cover.save(cover_path, 'JPEG')
    
    try:
        # Generate thumbnail
        print(f"[Thumbnail] إنشاء thumbnail...")
        thumb_path = generate_thumbnail(
            run_dir=temp_run,
            titles_json=meta_file,
            debug=True
        )
        
        if thumb_path and thumb_path.exists():
            print(f"✅ نجح!")
            print(f"📸 الموقع: {thumb_path}")
            
            # Read image to check size
            from PIL import Image
            img = Image.open(thumb_path)
            print(f"📐 الأبعاد: {img.size[0]}x{img.size[1]}")
        else:
            print(f"❌ فشل - لم يتم إنشاء الصورة")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

print(f"\n\n{'='*70}")
print("  📊 ملخص")
print(f"{'='*70}\n")
print(f"✅ تم إنشاء {len(test_titles)} thumbnails")
print(f"📂 افتح المجلد لرؤية النتائج:")
print(f"   {test_dir}")
print()

# Open folder
import subprocess
subprocess.run(['explorer', str(test_dir)], shell=True)
