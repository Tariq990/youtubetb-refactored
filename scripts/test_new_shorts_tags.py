"""
Test script for new short_tags_template prompt
Tests validation rules and output format
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

def test_prompt_format():
    """Test that the prompt template is properly formatted"""
    prompts_file = repo_root / "config" / "prompts.json"
    
    print("📂 Loading prompts.json...")
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    if "short_tags_template" not in prompts:
        print("❌ short_tags_template not found in prompts.json")
        return False
    
    template = prompts["short_tags_template"]
    prompt_text = "\n".join(template)
    
    print("✅ Prompt template loaded successfully\n")
    print("=" * 60)
    print("PROMPT PREVIEW:")
    print("=" * 60)
    print(prompt_text[:500] + "...\n")
    
    # Check key requirements
    checks = {
        "hashtags array": "hashtags" in prompt_text,
        "video_tags array": "video_tags" in prompt_text,
        "35-45 hashtags": "35-45" in prompt_text,
        "40-50 video_tags": "40-50" in prompt_text,
        "480 char limit": "480" in prompt_text,
        "No duplicates": "duplicate" in prompt_text.lower(),
        "Max 20 chars": "20 chars" in prompt_text,
        "JSON object format": "JSON object" in prompt_text,
    }
    
    print("=" * 60)
    print("VALIDATION CHECKS:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def test_with_gemini():
    """Test actual Gemini API call with new prompt"""
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        env_path = repo_root / "secrets" / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    
    if not api_key:
        print("\n⚠️ No GEMINI_API_KEY found - skipping live API test")
        print("💡 Set GEMINI_API_KEY in secrets/.env to test with real API")
        return None
    
    print("\n" + "=" * 60)
    print("LIVE GEMINI API TEST:")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Load prompt
        prompts_file = repo_root / "config" / "prompts.json"
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        prompt_template = "\n".join(prompts["short_tags_template"])
        
        # Test data
        test_book = "Atomic Habits"
        test_author = "James Clear"
        test_category = "Self-Development"
        test_script = "What if tiny changes could transform your entire life? In Atomic Habits, James Clear reveals the surprising power of small habits."
        
        prompt = prompt_template.format(
            book_name=test_book,
            author_name=test_author,
            category=test_category,
            script_preview=test_script
        )
        
        print(f"📖 Test Book: {test_book}")
        print(f"✍️ Test Author: {test_author}")
        print(f"📚 Test Category: {test_category}")
        print(f"\n🤖 Calling Gemini API...\n")
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        print("=" * 60)
        print("API RESPONSE:")
        print("=" * 60)
        
        video_tags = result.get("video_tags", [])
        
        print(f"\n📊 VIDEO_TAGS ({len(video_tags)} items):")
        print("-" * 60)
        for i, tag in enumerate(video_tags[:15], 1):  # Show first 15
            print(f"{i:2d}. {tag} ({len(tag)} chars)")
        if len(video_tags) > 15:
            print(f"... and {len(video_tags) - 15} more")
        
        # Validation
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS:")
        print("=" * 60)
        
        issues = []
        
        # Count check
        if not (40 <= len(video_tags) <= 50):
            issues.append(f"❌ Video tags count: {len(video_tags)} (expected: 40-50)")
        else:
            print(f"✅ Video tags count: {len(video_tags)} (valid: 40-50)")
        
        # Character length checks
        for tag in video_tags:
            if len(tag) > 20:
                issues.append(f"❌ Video tag too long: '{tag}' ({len(tag)} chars)")
        
        if not issues:
            print("✅ All video_tags ≤ 20 chars")
        
        # Total length check
        video_tags_str = ", ".join(video_tags)
        total_len = len(video_tags_str)
        
        if total_len > 480:
            issues.append(f"❌ Video tags total: {total_len} chars (limit: 480)")
        else:
            print(f"✅ Video tags total: {total_len} chars (limit: 480)")
        
        # Duplicate check
        if len(video_tags) != len(set(video_tags)):
            issues.append("❌ Duplicate tags found")
        else:
            print("✅ No duplicate tags")
        
        # Video tags format check (no #)
        invalid_video_tags = [t for t in video_tags if t.startswith('#')]
        if invalid_video_tags:
            issues.append(f"❌ Video tags with #: {invalid_video_tags[:3]}")
        else:
            print("✅ No video tags contain #")
        
        # Final result
        print("\n" + "=" * 60)
        if issues:
            print("❌ VALIDATION FAILED:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ ALL VALIDATIONS PASSED!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n❌ API Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("🧪 TESTING NEW SHORTS TAGS PROMPT")
    print("=" * 60 + "\n")
    
    # Test 1: Prompt format
    format_ok = test_prompt_format()
    
    if not format_ok:
        print("\n❌ Prompt format test FAILED")
        return 1
    
    # Test 2: Live API (if key available)
    api_result = test_with_gemini()
    
    if api_result is None:
        print("\n⚠️ Skipped live API test (no API key)")
        print("✅ Format validation PASSED")
        return 0
    elif api_result:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ API validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
