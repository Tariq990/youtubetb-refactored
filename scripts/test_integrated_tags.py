"""
Test integrated Gemini tag generation in main system
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrastructure.adapters.youtube_metadata import (
    _configure_model,
    _generate_ai_tags
)

def test_integrated_tags():
    """Test the updated _generate_ai_tags function"""
    
    print("=" * 70)
    print("🧪 Testing Integrated Gemini Tag Generation")
    print("=" * 70)
    print()
    
    # Configure model
    config_dir = Path(__file__).resolve().parents[1] / "config"
    model = _configure_model(config_dir)
    
    if not model:
        print("❌ Failed to configure Gemini model")
        return
    
    print("✅ Gemini model configured\n")
    
    # Test with Atomic Habits
    book_title = "Atomic Habits"
    author_name = "James Clear"
    
    print(f"📚 Book: {book_title}")
    print(f"✍️  Author: {author_name}\n")
    print("🔄 Generating tags...")
    print("-" * 70)
    
    # Generate tags
    tags = _generate_ai_tags(
        model=model,
        book_title=book_title,
        author_name=author_name,
        prompts={},
        target_count=60
    )
    
    if not tags:
        print("❌ No tags generated")
        return
    
    # Calculate statistics
    total_raw = sum(len(t) for t in tags)
    total_api = sum(len(t) + (2 if " " in t else 0) for t in tags)
    spaced = sum(1 for t in tags if " " in t)
    density = len(tags) - spaced
    max_len = max(len(t) for t in tags) if tags else 0
    avg_len = total_raw / len(tags) if tags else 0
    
    print()
    print("=" * 70)
    print("✅ TAG GENERATION RESULTS")
    print("=" * 70)
    print()
    print(f"📊 Statistics:")
    print(f"  • Total tags: {len(tags)}")
    print(f"  • Raw chars: {total_raw}")
    print(f"  • API chars: {total_api}/499")
    print(f"  • Max tag length: {max_len} chars")
    print(f"  • Avg tag length: {avg_len:.1f} chars")
    print(f"  • Spaced tags: {spaced} ({spaced*100//len(tags) if tags else 0}%)")
    print(f"  • Density tags: {density} ({density*100//len(tags) if tags else 0}%)")
    
    if total_raw < 450:
        print(f"  ⚠️  Below 450 chars target by {450 - total_raw} chars")
    elif total_raw > 495:
        print(f"  ⚠️  Above 495 chars target by {total_raw - 495} chars")
    else:
        print(f"  ✅ Within target range (450-495 chars)")
    
    if total_api > 499:
        print(f"  ❌ Exceeds API limit by {total_api - 499} chars!")
    else:
        print(f"  ✅ API chars within limit ({499 - total_api} chars remaining)")
    
    if max_len > 26:
        print(f"  ❌ Has tags exceeding 26 chars!")
    else:
        print(f"  ✅ All tags ≤26 chars")
    
    print()
    print("📋 Tags list:")
    for i, tag in enumerate(tags, 1):
        icon = "📝" if " " in tag else "⚡"
        print(f"  {i:2d}. {icon} {tag:30s} (len={len(tag):2d})")
    
    print()
    print("=" * 70)
    print("✅ Test complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_integrated_tags()
