"""
Test main tag generation system from youtube_metadata.py
Demonstrates the full tag generation pipeline used in production.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrastructure.adapters.youtube_metadata import (
    _generate_tags,
    _build_density_tags,
    _merge_tags,
)


def test_book(book_title: str, author_name: str):
    """Test tag generation for a specific book."""
    print("\n" + "=" * 70)
    print(f"📚 Book: {book_title}")
    print(f"✍️  Author: {author_name}")
    print("=" * 70)

    # Step 1: Generate basic tags (book + author combinations + fixed tags)
    basic_tags = _generate_tags(book_title, author_name)
    print(f"\n🔵 BASIC TAGS (_generate_tags): {len(basic_tags)} tags")
    print("-" * 70)
    for i, tag in enumerate(basic_tags, 1):
        print(f"  {i:2}. {tag:<50} (len={len(tag):2})")

    # Step 2: Generate density tags (compressed, no spaces)
    density_tags = _build_density_tags(book_title, author_name)
    print(f"\n🟢 DENSITY TAGS (_build_density_tags): {len(density_tags)} tags")
    print("-" * 70)
    for i, tag in enumerate(density_tags, 1):
        print(f"  {i:2}. {tag:<50} (len={len(tag):2})")

    # Step 3: Simulate AI tags (in real pipeline, these come from Gemini)
    ai_tags_simulation = [
        "habit formation",
        "behavior change",
        "productivity systems",
        "self improvement strategies",
        "identity based habits",
        "compound growth mindset",
        "habit stacking techniques",
        "atomic improvements",
        "small habits big results",
    ]
    print(f"\n🟣 AI TAGS (simulated): {len(ai_tags_simulation)} tags")
    print("-" * 70)
    for i, tag in enumerate(ai_tags_simulation, 1):
        print(f"  {i:2}. {tag:<50} (len={len(tag):2})")

    # Step 4: Merge all tags (deduplication, prioritization, character limits)
    final_tags, raw_chars, api_chars = _merge_tags(
        primary=basic_tags,
        ai=ai_tags_simulation,
        density=density_tags,
        book_title=book_title,
        author_name=author_name,
    )

    print(f"\n🔴 FINAL MERGED TAGS: {len(final_tags)} tags")
    print(f"📊 Raw chars: {raw_chars} | API chars: {api_chars}/500")
    print("-" * 70)
    for i, tag in enumerate(final_tags, 1):
        has_space = " " in tag
        space_marker = "📝" if has_space else "⚡"
        print(f"  {i:2}. {space_marker} {tag:<48} (len={len(tag):2})")

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"  • Total tags: {len(final_tags)}/30 (max)")
    print(f"  • Raw characters: {raw_chars}")
    print(f"  • API characters: {api_chars}/500 (includes +2 for spaced tags)")
    print(f"  • Tags with spaces: {sum(1 for t in final_tags if ' ' in t)}")
    print(f"  • Density tags: {sum(1 for t in final_tags if ' ' not in t)}")
    print("=" * 70)


if __name__ == "__main__":
    # Test with different books
    test_book("Atomic Habits", "James Clear")
    test_book("Rich Dad Poor Dad", "Robert Kiyosaki")
    test_book("The 7 Habits of Highly Effective People", "Stephen Covey")
    
    print("\n✅ Tag generation test complete!")
    print("\n💡 KEY INSIGHTS:")
    print("  1. Basic tags: Book + Author combinations + fixed SEO tags")
    print("  2. Density tags: Compressed versions (no spaces) for char efficiency")
    print("  3. AI tags: Topic-based tags from Gemini (simulated here)")
    print("  4. Merge: Deduplicates, prioritizes, and enforces 30 tags / 500 char limit")
    print("  5. 📝 = spaced tag (+2 API chars), ⚡ = density tag (efficient)")
