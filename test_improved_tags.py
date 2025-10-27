#!/usr/bin/env python3
"""Test improved AI tags generation on Think and Grow Rich"""

from pathlib import Path
from src.infrastructure.adapters.youtube_metadata import _configure_model, _generate_ai_tags

def main():
    print("🧪 Testing Improved AI Tags Prompt")
    print("=" * 60)
    print("📚 Book: Think and Grow Rich")
    print("✍️  Author: Napoleon Hill")
    print("=" * 60)
    
    # Load model
    config_dir = Path("config")
    model = _configure_model(config_dir)
    
    if not model:
        print("❌ Failed to load Gemini model")
        return
    
    # Generate tags
    print("\n🔄 Calling Gemini AI with improved prompt...")
    tags = _generate_ai_tags(
        model=model,
        book_title="Think and Grow Rich",
        author_name="Napoleon Hill",
        prompts={},
        target_count=60
    )
    
    if not tags:
        print("❌ No tags generated")
        return
    
    # Display results
    print(f"\n✅ Generated {len(tags)} tags:\n")
    
    # Categorize tags for analysis
    format_tags = []
    longtail_tags = []
    seo_tags = []
    topic_tags = []
    other_tags = []
    
    for tag in tags:
        tag_lower = tag.lower()
        if any(word in tag_lower for word in ['animated', 'audiobook', 'narrated', 'summary', 'explained']):
            format_tags.append(tag)
        elif any(word in tag_lower for word in ['how to', 'best', 'techniques', 'power of']):
            longtail_tags.append(tag)
        elif tag_lower in ['self improvement', 'personal development', 'motivational', 'educational', 'productivity', 'inspirational content', 'book review', 'mindset tips']:
            seo_tags.append(tag)
        elif 'Think and Grow Rich' in tag or 'Napoleon Hill' in tag or tag in ['InkEcho', 'book summary']:
            other_tags.append(tag)
        else:
            topic_tags.append(tag)
    
    # Display by category
    if format_tags:
        print("🎬 VIDEO FORMAT TAGS:")
        for tag in format_tags:
            print(f"   • {tag} ({len(tag)} chars)")
    
    if seo_tags:
        print(f"\n🔍 SEO KEYWORDS ({len(seo_tags)} tags - should be 6-8):")
        for tag in seo_tags:
            print(f"   • {tag} ({len(tag)} chars)")
    
    if longtail_tags:
        print(f"\n🎯 LONG-TAIL SEARCH TAGS ({len(longtail_tags)} tags):")
        for tag in longtail_tags:
            print(f"   • {tag} ({len(tag)} chars)")
    
    if topic_tags:
        print(f"\n📖 TOPIC-SPECIFIC TAGS ({len(topic_tags)} tags):")
        for tag in topic_tags:
            print(f"   • {tag} ({len(tag)} chars)")
    
    if other_tags:
        print(f"\n📌 MUST-HAVE TAGS ({len(other_tags)} tags):")
        for tag in other_tags:
            print(f"   • {tag} ({len(tag)} chars)")
    
    # Statistics
    raw_chars = sum(len(t) for t in tags)
    api_chars = sum(len(t) + (2 if " " in t else 0) for t in tags)
    spaced_tags = sum(1 for t in tags if " " in t)
    
    print("\n" + "=" * 60)
    print("📊 STATISTICS:")
    print(f"   • Total tags: {len(tags)}")
    print(f"   • Raw chars: {raw_chars} (target: 450-495)")
    print(f"   • API chars: {api_chars} (limit: 495)")
    print(f"   • Spaced tags: {spaced_tags}/{len(tags)} ({spaced_tags/len(tags)*100:.0f}%)")
    print(f"   • Max tag length: {max(len(t) for t in tags)} chars")
    print("=" * 60)
    
    # Check for improvements
    print("\n✅ QUALITY CHECKS:")
    
    # Check 1: No repetition in SEO keywords
    duplicates = []
    if 'self improvement' in seo_tags and 'personal development' in seo_tags:
        duplicates.append("❌ Both 'self improvement' AND 'personal development' present")
    if 'motivational' in seo_tags and 'inspirational content' in seo_tags:
        duplicates.append("❌ Both 'motivational' AND 'inspirational content' present")
    
    if duplicates:
        print("   ⚠️  Found duplicate SEO keywords:")
        for dup in duplicates:
            print(f"      {dup}")
    else:
        print("   ✅ No duplicate SEO keywords (good!)")
    
    # Check 2: Has format tags
    if format_tags:
        print(f"   ✅ Has {len(format_tags)} format tags")
    else:
        print("   ⚠️  No format tags found")
    
    # Check 3: Has long-tail tags
    if longtail_tags:
        print(f"   ✅ Has {len(longtail_tags)} long-tail search tags")
    else:
        print("   ⚠️  No long-tail tags found")
    
    # Check 4: Tag length compliance
    over_limit = [t for t in tags if len(t) > 26]
    if over_limit:
        print(f"   ❌ {len(over_limit)} tags exceed 26 chars:")
        for t in over_limit:
            print(f"      • {t} ({len(t)} chars)")
    else:
        print("   ✅ All tags ≤26 characters")
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    main()
