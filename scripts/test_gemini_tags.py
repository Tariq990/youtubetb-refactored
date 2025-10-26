"""
Test Gemini AI to generate optimized YouTube tags directly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import google.generativeai as genai
import json
import re


def configure_gemini():
    """Configure Gemini API"""
    repo_root = Path(__file__).resolve().parents[1]
    api_key_file = repo_root / "secrets" / "api_key.txt"
    
    if not api_key_file.exists():
        print(f"❌ API key not found: {api_key_file}")
        return None
    
    # Read and clean API key - take first line only (file may have multiple keys)
    content = api_key_file.read_text(encoding="utf-8").strip()
    api_key = content.split('\n')[0].strip()  # First key only
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print(f"✅ Gemini configured: gemini-2.0-flash-exp\n")
    return model


def generate_tags_with_gemini(book_title: str, author_name: str):
    """Generate tags using Gemini AI with specific constraints"""
    
    model = configure_gemini()
    if not model:
        return None
    
    print("=" * 70)
    print("🤖 GEMINI AI TAG GENERATOR")
    print("=" * 70)
    print(f"\n📚 Book: {book_title}")
    print(f"✍️  Author: {author_name}\n")
    
    prompt = f"""You are a YouTube SEO expert. Generate optimized tags for a book summary video.

**Book:** {book_title}
**Author:** {author_name}

**REQUIREMENTS:**
1. Generate EXACTLY 25-30 tags
2. Each tag MUST be ≤26 characters (STRICT LIMIT)
3. Target total: 470-499 characters (sum of all tag lengths)
4. Mix of tag types:
   - Book/Author combinations (5-7 tags)
   - SEO keywords (10-12 tags)
   - Topic tags (8-10 tags)

**TAG CATEGORIES:**

A) Must-have tags (include these):
   - Book title: "{book_title}"
   - Author name: "{author_name}"
   - Combined: "{book_title} {author_name}"
   - Main keyword: "book summary"
   - Combined with book: "{book_title} book summary"
   - Brand: "InkEcho"
   - Format: "audiobook"

B) SEO Keywords (popular search terms):
   - self improvement
   - personal development
   - productivity
   - motivational
   - educational
   - book review
   - self help

C) Topic-specific tags (related to book content):
   - Generate 10-15 tags about the book's topics
   - Each 15-26 characters
   - Use SPACES for readability (NOT camelCase)
   - Examples: "habit formation guide", "success mindset tips"

**OUTPUT FORMAT:**
Return ONLY a valid JSON array of tags. No explanations.

Example:
["tag1", "tag2", "tag3", ...]

**CRITICAL RULES:**
- NEVER exceed 26 characters per tag
- Prioritize spaced tags over density tags (better SEO)
- Total character count: 470-499
- Use natural language (spaces between words)
- Each tag should be searchable on YouTube

Generate the tags now:"""

    print("🔄 Generating tags with Gemini AI...")
    print("-" * 70)
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Extract JSON from response
        # Remove markdown code blocks if present
        if "```" in raw_text:
            # Extract content between ```json and ```
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1)
            else:
                # Try to find any JSON array
                match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(0)
        
        # Parse JSON
        tags = json.loads(raw_text)
        
        if not isinstance(tags, list):
            print(f"❌ Invalid response format (not a list)")
            return None
        
        # Sanitize and validate tags
        sanitized_tags = []
        for tag in tags:
            tag = str(tag).strip()
            # Remove quotes
            tag = tag.strip('"').strip("'")
            # Check length
            if len(tag) > 26:
                print(f"  ⚠️  Tag too long (trimming): {tag} ({len(tag)} chars)")
                tag = tag[:26].rstrip()
            if tag and tag not in sanitized_tags:
                sanitized_tags.append(tag)
        
        # Calculate stats
        total_tags = len(sanitized_tags)
        raw_chars = sum(len(t) for t in sanitized_tags)
        api_chars = sum(len(t) + (2 if " " in t else 0) for t in sanitized_tags)
        spaced = sum(1 for t in sanitized_tags if " " in t)
        density = total_tags - spaced
        
        print("\n" + "=" * 70)
        print("✅ GEMINI GENERATED TAGS")
        print("=" * 70)
        
        print(f"\n📊 Statistics:")
        print(f"  • Total tags: {total_tags}")
        print(f"  • Raw chars: {raw_chars} (target: 470-499)")
        print(f"  • API chars: {api_chars}/499")
        print(f"  • Max tag length: {max(len(t) for t in sanitized_tags)} chars")
        print(f"  • Avg tag length: {raw_chars / total_tags:.1f} chars")
        print(f"  • Spaced tags: {spaced} ({spaced/total_tags*100:.1f}%)")
        print(f"  • Density tags: {density} ({density/total_tags*100:.1f}%)")
        
        # Check targets
        if 470 <= raw_chars <= 499:
            print(f"  ✅ Hit target range! ({raw_chars} chars)")
        elif raw_chars < 470:
            print(f"  ⚠️  Below target by {470 - raw_chars} chars")
        else:
            print(f"  ⚠️  Above target by {raw_chars - 499} chars")
        
        if api_chars <= 499:
            print(f"  ✅ API chars within limit!")
        else:
            print(f"  ❌ API chars exceed limit by {api_chars - 499}")
        
        print(f"\n📋 Tags list:")
        for i, tag in enumerate(sanitized_tags, 1):
            marker = "📝" if " " in tag else "⚡"
            print(f"  {i:2}. {marker} {tag:<30} (len={len(tag):2})")
        
        # Length distribution
        lengths = {}
        for t in sanitized_tags:
            l = len(t)
            lengths[l] = lengths.get(l, 0) + 1
        
        print(f"\n📊 Length distribution:")
        for length in sorted(lengths.keys()):
            bar = "█" * lengths[length]
            print(f"  {length:2} chars: {bar} ({lengths[length]} tags)")
        
        return sanitized_tags
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response")
        print(f"Error: {e}")
        print(f"\nRaw response:\n{raw_text[:500]}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🤖 Testing Gemini AI Tag Generation")
    print("=" * 70)
    
    # Test with Atomic Habits
    tags = generate_tags_with_gemini(
        book_title="Atomic Habits",
        author_name="James Clear"
    )
    
    if tags:
        print("\n" + "=" * 70)
        print("✅ Test complete!")
        print(f"Generated {len(tags)} tags")
        
        # Check if it beats our manual approach
        manual_raw = 454  # Our best manual result
        gemini_raw = sum(len(t) for t in tags)
        
        print(f"\n📊 Comparison:")
        print(f"  Manual approach: {manual_raw} raw chars")
        print(f"  Gemini approach: {gemini_raw} raw chars")
        
        if gemini_raw > manual_raw:
            print(f"  🎉 Gemini wins by {gemini_raw - manual_raw} chars!")
        elif gemini_raw == manual_raw:
            print(f"  🤝 Tie!")
        else:
            print(f"  ⚠️  Manual wins by {manual_raw - gemini_raw} chars")
    else:
        print("\n❌ Test failed!")
