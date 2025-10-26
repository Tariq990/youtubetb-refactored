#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test subtitle 3-word split (2+1 pattern)
"""
from pathlib import Path
import sys
import json

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.thumbnail import generate_thumbnail

# Test directory
test_dir = repo_root / "tmp" / "test_3words_2_1"
test_dir.mkdir(parents=True, exist_ok=True)

# Test cases
test_cases = [
    ("1 word", "KIYOSAKI"),
    ("2 words", "ROBERT KIYOSAKI"),
    ("3 words", "BY ROBERT KIYOSAKI"),  # Should split: "BY ROBERT" / "KIYOSAKI"
    ("4 words", "BY ROBERT T KIYOSAKI"),  # Should split: "BY ROBERT" / "T KIYOSAKI"
    ("5 words", "WRITTEN BY ROBERT T KIYOSAKI"),  # Should split: "WRITTEN BY" / "ROBERT T KIYOSAKI"
]

for name, subtitle_text in test_cases:
    print("=" * 70)
    print(f"Testing: {name} → '{subtitle_text}'")
    print("=" * 70)
    
    # Create metadata
    metadata = {
        "youtube_title": "Test | Book Summary",
        "thumbnail_title": "RICH DAD POOR DAD",
        "thumbnail_subtitle": subtitle_text,
        "main_title": "RICH DAD POOR DAD",
        "author_name": subtitle_text
    }
    
    # Create run dir
    temp_run = test_dir / name.replace(" ", "_")
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
    print(f"\n[Testing] Generating thumbnail...")
    thumb_path = generate_thumbnail(
        run_dir=temp_run,
        titles_json=meta_file,
        debug=True
    )
    
    if thumb_path and thumb_path.exists():
        print(f"\n✅ Success: {thumb_path}")
    else:
        print(f"\n❌ Failed")
    
    print()

print("=" * 70)
print("All tests complete!")
print(f"Check results in: {test_dir}")
print("=" * 70)
