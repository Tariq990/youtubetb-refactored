"""
Test YouTube tags_template (regular videos) with Gemini API
"""

import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

def load_api_key():
    """Load Gemini API key from secrets"""
    api_key_paths = [
        repo_root / "secrets" / "api_key.txt",
        repo_root / "secrets" / "api_keys.txt",
        repo_root / "api_key.txt"
    ]
    
    for path in api_key_paths:
        if path.exists():
            content = path.read_text(encoding='utf-8').strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if lines:
                return lines[0]
    
    raise FileNotFoundError("❌ No API key found!")

def load_tags_template():
    """Load tags_template from prompts.json"""
    prompts_path = repo_root / "config" / "prompts.json"
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    return prompts.get("tags_template", [])

def test_tags_generation():
    """Test tags generation with Gemini"""
    print("=" * 70)
    print("🧪 Testing YouTube tags_template (Regular Videos)")
    print("=" * 70)
    
    # Load template
    template = load_tags_template()
    print(f"\n✅ Loaded template ({len(template)} lines)")
    
    # Load API key
    try:
        api_key = load_api_key()
        print("✅ API key loaded")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    # Configure Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        print("✅ Gemini configured (gemini-2.5-flash)")
    except Exception as e:
        print(f"❌ Failed to configure Gemini: {e}")
        return
    
    # Test data
    book_name = "Atomic Habits"
    author_name = "James Clear"
    
    # Build prompt
    prompt_text = "\n".join(template)
    prompt_text = prompt_text.replace("{book_name}", book_name)
    prompt_text = prompt_text.replace("{author_name}", author_name)
    
    print(f"\n📝 Test Book: {book_name} by {author_name}")
    print(f"📤 Sending to Gemini...\n")
    
    # Call Gemini
    try:
        response = model.generate_content(prompt_text)
        tags_string = response.text.strip()
        
        print("=" * 70)
        print("🤖 GEMINI OUTPUT:")
        print("=" * 70)
        print(tags_string)
        print("=" * 70)
        
        # Parse tags
        tags = [tag.strip() for tag in tags_string.split(',')]
        
        # Calculate metrics
        tag_count = len(tags)
        total_length = len(tags_string)
        
        # Validation
        print(f"\n📊 VALIDATION RESULTS:")
        print(f"   Total tags: {tag_count}")
        print(f"   Total characters: {total_length}")
        print(f"   Target: 45-55 tags, ≤490 chars")
        
        # Check requirements
        checks = []
        
        # Tag count
        if 45 <= tag_count <= 55:
            checks.append(("✅", f"Tag count: {tag_count} (within 45-55)"))
        else:
            checks.append(("❌", f"Tag count: {tag_count} (outside 45-55)"))
        
        # Character limit
        if total_length <= 490:
            checks.append(("✅", f"Chars: {total_length}/490 ({490 - total_length} remaining)"))
        else:
            checks.append(("❌", f"Chars: {total_length}/490 (EXCEEDS by {total_length - 490})"))
        
        # Mandatory tags
        mandatory = ["book summary", "audiobook", book_name.lower(), author_name.lower()]
        missing = [tag for tag in mandatory if tag not in tags_string.lower()]
        if not missing:
            checks.append(("✅", f"Mandatory tags: All present"))
        else:
            checks.append(("❌", f"Missing: {', '.join(missing)}"))
        
        # All lowercase
        if tags_string == tags_string.lower():
            checks.append(("✅", "All lowercase"))
        else:
            checks.append(("⚠️", "Contains uppercase"))
        
        # Tag length (1-4 words)
        long_tags = [tag for tag in tags if len(tag.split()) > 4]
        if not long_tags:
            checks.append(("✅", "All tags ≤4 words"))
        else:
            checks.append(("⚠️", f"{len(long_tags)} tags >4 words"))
        
        # Duplicates
        unique_tags = set(tags)
        if len(tags) == len(unique_tags):
            checks.append(("✅", "No duplicates"))
        else:
            checks.append(("⚠️", f"{len(tags) - len(unique_tags)} duplicates"))
        
        # Print results
        print()
        for icon, msg in checks:
            print(f"   {icon} {msg}")
        
        # Tag breakdown
        print(f"\n📋 First 10 tags:")
        for i, tag in enumerate(tags[:10], 1):
            print(f"   {i}. {tag} ({len(tag)} chars)")
        
        # Summary
        passed = sum(1 for icon, _ in checks if icon == "✅")
        total_checks = len(checks)
        score = (passed / total_checks) * 100
        
        print(f"\n{'='*70}")
        print(f"🎯 FINAL SCORE: {passed}/{total_checks} ({score:.0f}%)")
        print(f"{'='*70}")
        
        if score >= 80:
            print("✅ EXCELLENT: Prompt works perfectly!")
        elif score >= 60:
            print("⚠️ ACCEPTABLE: Minor improvements needed")
        else:
            print("❌ NEEDS WORK: Significant improvements required")
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tags_generation()
