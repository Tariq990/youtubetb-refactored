"""
Test tag generation with OPTIMIZED settings:
- Max 26 chars per tag (YouTube safe limit)
- Total raw chars: 470-499 (maximize usage)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrastructure.adapters.youtube_metadata import (
    _generate_tags,
    _build_density_tags,
    _merge_tags,
)
import re


def sanitize_tag(tag: str, max_len: int = 26) -> str:
    """Sanitize tag for YouTube API compliance."""
    tag = re.sub(r"[^A-Za-z0-9\s]", "", tag)
    tag = re.sub(r"\s+", " ", tag).strip()
    if len(tag) > max_len:
        tag = tag[:max_len].rstrip()
    return tag


def optimize_tags_for_youtube(book_title: str, author_name: str, target_min: int = 470, target_max: int = 499, max_tag_len: int = 26, api_limit: int = 499):
    """
    Generate optimized tags that:
    1. Each tag ≤26 chars
    2. Total raw chars between 470-499
    3. API chars ≤499 (accounting for +2 per spaced tag)
    4. Maximize number of tags
    """
    
    print(f"📚 Book: {book_title}")
    print(f"✍️  Author: {author_name}")
    print(f"🎯 Target: {target_min}-{target_max} raw chars, max {max_tag_len} chars/tag\n")
    
    # Generate all possible tags
    basic_tags = _generate_tags(book_title, author_name)
    density_tags = _build_density_tags(book_title, author_name)
    
    # Expanded AI tags simulation (more 20-26 char tags to fill quota)
    ai_tags = [
        "habit formation mastery",  # 24
        "behavior change science",  # 23
        "productivity systems",  # 20
        "self improvement guide",  # 23
        "identity based habits",  # 21
        "compound growth mindset",  # 23
        "habit stacking guide",  # 21
        "atomic improvements",  # 19
        "small habits big results",  # 24
        "habit building strategy",  # 24
        "personal transformation",  # 23
        "success mindset mastery",  # 24
        "daily routines guide",  # 21
        "habit tracking methods",  # 23
        "behavior psychology",  # 19
        "lifestyle design tips",  # 22
        "goal achievement guide",  # 23
        "mindset shift guide",  # 20
        "continuous improvement",  # 22
        "habit science explained",  # 24
        "performance habits tips",  # 24
        "habit loops explained",  # 22
        "cue routine reward loop",  # 23
        "habit automation guide",  # 23
        "keystone habits power",  # 22
        "building better habits",  # 23
        "habit change strategy",  # 22
    ]
    
    # Merge with standard algorithm
    all_tags, raw_chars, api_chars = _merge_tags(
        primary=basic_tags,
        ai=ai_tags,
        density=density_tags,
        book_title=book_title,
        author_name=author_name,
    )
    
    print(f"🔵 Initial merge: {len(all_tags)} tags, {raw_chars} raw chars, {api_chars} API chars")
    
    # Sanitize to max 26 chars
    sanitized = []
    for tag in all_tags:
        clean = sanitize_tag(tag, max_tag_len)
        if clean and clean not in sanitized:
            sanitized.append(clean)
    
    print(f"🧹 After sanitization: {len(sanitized)} tags\n")
    
    # Build optimized list: keep tags ≤26 chars, aim for 470-499 raw, ≤499 API
    final_tags = []
    current_raw = 0
    current_api = 0
    
    # Sort by priority: must-have tags first, then by length (longer = better for filling quota)
    must_have_keywords = [book_title.lower(), author_name.lower(), "book summary", "inkecho", "audiobook"]
    
    def tag_priority(tag):
        # Must-have tags get highest priority
        if any(kw in tag.lower() for kw in must_have_keywords):
            return (0, -len(tag))  # 0 = highest priority, prefer longer
        # Prefer density tags (no spaces) for API efficiency
        if " " not in tag:
            return (1, -len(tag))
        # Spaced tags last
        return (2, -len(tag))
    
    sorted_tags = sorted(sanitized, key=tag_priority)
    
    for tag in sorted_tags:
        if len(tag) > max_tag_len:
            continue
        
        tag_api_cost = len(tag) + (2 if " " in tag else 0)
        new_raw = current_raw + len(tag)
        new_api = current_api + tag_api_cost
        
        # Check both raw and API limits
        if new_api > api_limit:
            continue
        
        if new_raw > target_max:
            continue
        
        final_tags.append(tag)
        current_raw = new_raw
        current_api = new_api
    
    # If still below target, add remaining tags that fit
    if current_raw < target_min:
        print(f"\n🔍 Below target ({current_raw}/{target_min}), adding more tags...")
        remaining = [t for t in sorted_tags if t not in final_tags and len(t) <= max_tag_len]
        
        # Also add AI tags that weren't merged
        for ai_tag in ai_tags:
            clean_ai = sanitize_tag(ai_tag, max_tag_len)
            if clean_ai and clean_ai not in final_tags and clean_ai not in remaining:
                remaining.append(clean_ai)
        
        print(f"   Available tags to add: {len(remaining)}")
        
        # Debug: show first 10 remaining
        print(f"   First 10 remaining tags:")
        for i, t in enumerate(remaining[:10], 1):
            marker = "📝" if " " in t else "⚡"
            api_cost = len(t) + (2 if " " in t else 0)
            print(f"      {i}. {marker} {t} ({len(t)} raw, {api_cost} API)")
        
        # Sort remaining: prefer density tags (no spaces) for API efficiency
        remaining.sort(key=lambda x: (" " in x, -len(x)))
        
        for tag in remaining:
            tag_api_cost = len(tag) + (2 if " " in tag else 0)
            new_raw = current_raw + len(tag)
            new_api = current_api + tag_api_cost
            
            if new_raw <= target_max and new_api <= api_limit:
                final_tags.append(tag)
                current_raw = new_raw
                current_api = new_api
                marker = "📝" if " " in tag else "⚡"
                print(f"   ✅ {marker} {tag} ({len(tag)} raw, +{tag_api_cost} API) → Raw: {current_raw}, API: {current_api}")
                if current_raw >= target_min and current_api <= api_limit:
                    print(f"   🎯 Hit target range!")
                    break
            elif current_raw >= target_min:
                # Already hit raw target, stop
                break
    
    # Calculate final stats
    final_raw = sum(len(t) for t in final_tags)
    final_api = sum(len(t) + (2 if " " in t else 0) for t in final_tags)
    
    print("=" * 70)
    print("✅ OPTIMIZED TAGS GENERATED")
    print("=" * 70)
    print(f"\n📊 Statistics:")
    print(f"  • Total tags: {len(final_tags)}")
    print(f"  • Raw chars: {final_raw} (target: {target_min}-{target_max})")
    print(f"  • API chars: {final_api}/500")
    print(f"  • Max tag length: {max(len(t) for t in final_tags)} chars")
    print(f"  • Avg tag length: {final_raw / len(final_tags):.1f} chars")
    
    # Check if we hit target
    if target_min <= final_raw <= target_max:
        print(f"  ✅ Hit target range! ({final_raw} chars)")
    elif final_raw < target_min:
        print(f"  ⚠️  Below target by {target_min - final_raw} chars")
    else:
        print(f"  ⚠️  Above target by {final_raw - target_max} chars")
    
    print(f"\n📋 Tags list:")
    for i, tag in enumerate(final_tags, 1):
        marker = "📝" if " " in tag else "⚡"
        print(f"  {i:2}. {marker} {tag:<30} (len={len(tag):2})")
    
    # Length distribution
    lengths = {}
    for t in final_tags:
        l = len(t)
        lengths[l] = lengths.get(l, 0) + 1
    
    print(f"\n📊 Length distribution:")
    for length in sorted(lengths.keys()):
        bar = "█" * lengths[length]
        print(f"  {length:2} chars: {bar} ({lengths[length]} tags)")
    
    return final_tags, final_raw, final_api


if __name__ == "__main__":
    print("\n🎯 OPTIMIZED TAG GENERATION TEST")
    print("=" * 70)
    print("Goal: Max 26 chars/tag, total 470-499 raw chars\n")
    
    # Test with Atomic Habits
    tags, raw, api = optimize_tags_for_youtube(
        book_title="Atomic Habits",
        author_name="James Clear",
        target_min=470,
        target_max=499,
        max_tag_len=26
    )
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print(f"Generated {len(tags)} tags, {raw} raw chars, {api} API chars")
