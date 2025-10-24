#!/usr/bin/env python3
"""
Fix all parents[2] to parents[3] in src/infrastructure/adapters/*.py files
"""
from pathlib import Path
import re

repo_root = Path(__file__).resolve().parent
adapters_dir = repo_root / "src" / "infrastructure" / "adapters"

files_to_fix = [
    "shorts_generator.py",
    "search.py",
    "process_backup.py",
    "database.py"
]

for filename in files_to_fix:
    filepath = adapters_dir / filename
    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        continue
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Replace parents[2] with parents[3] and add comment
    content = re.sub(
        r'Path\(__file__\)\.resolve\(\)\.parents\[2\]',
        r'Path(__file__).resolve().parents[3]  # Fixed: parents[3] to reach repo root',
        content
    )
    
    if content != original_content:
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Fixed: {filename}")
    else:
        print(f"⏭️  No changes needed: {filename}")

print("\n✅ Done! All files fixed.")
