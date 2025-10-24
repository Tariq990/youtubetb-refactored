"""
Quick Thumbnail Generator
Generate a simple thumbnail with 3-word main title and 4-word subtitle
"""
from pathlib import Path
import sys
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrastructure.adapters.thumbnail import generate_thumbnail
import json
import tempfile

# Create temporary data
temp_data = {
    "main_title": "Atomic Habits",
    "author_name": "James Clear",
    "thumbnail_title": "Understanding Personal Development Today",  # 4 words, long (avg 9 chars)
    "thumbnail_subtitle": "Tiny Changes Big Results"  # 4 words
}

# Create temporary run directory with cover
temp_run_dir = Path("temp_run")
temp_run_dir.mkdir(exist_ok=True)

# Copy book cover if exists
cover_path = Path("bookcover.jpg")
if cover_path.exists():
    import shutil
    shutil.copy(cover_path, temp_run_dir / "bookcover.jpg")
    print(f"📚 Using book cover: bookcover.jpg")

# Save to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
    json.dump(temp_data, f, ensure_ascii=False, indent=2)
    temp_json = Path(f.name)

print("🎨 Generating quick thumbnail...")
print(f"   Main: {temp_data['thumbnail_title']}")
print(f"   Sub:  {temp_data['thumbnail_subtitle']}")

# Generate thumbnail
result = generate_thumbnail(
    run_dir=temp_run_dir,
    titles_json=temp_json,
    output_path=Path("quick_thumbnail.jpg"),
    debug=True
)

# Cleanup
temp_json.unlink()
import shutil
shutil.rmtree(temp_run_dir)

if result:
    print(f"\n✅ Thumbnail saved: quick_thumbnail.jpg")
else:
    print(f"\n❌ Failed to generate thumbnail")
