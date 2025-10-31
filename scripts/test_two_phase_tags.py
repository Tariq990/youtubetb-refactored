"""
Test Two-Phase Tag Generation System
Phase 1: Generate 60-80 comprehensive tags
Phase 2: Optimize to fit 480 chars
"""

import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

def load_api_key():
    """Load Gemini API key"""
    api_key_paths = [
        repo_root / "secrets" / "api_key.txt",
        repo_root / "secrets" / "api_keys.txt",
    ]
    
    for path in api_key_paths:
        if path.exists():
            content = path.read_text(encoding='utf-8').strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if lines:
                return lines[0]
    
    raise FileNotFoundError("❌ No API key found!")

def load_prompts():
    """Load both phase prompts"""
    prompts_path = repo_root / "config" / "prompts.json"
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    return (
        prompts.get("tags_generation_phase1", []),
        prompts.get("tags_optimization_phase2", [])
    )

def test_two_phase_system():
    """Test two-phase tag generation"""
    print("=" * 80)
    print("🎯 Two-Phase Tag Generation System Test")
    print("=" * 80)
    
    # Load prompts
    phase1_template, phase2_template = load_prompts()
    print(f"\n✅ Loaded Phase 1 template ({len(phase1_template)} lines)")
    print(f"✅ Loaded Phase 2 template ({len(phase2_template)} lines)")
    
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
        print("✅ Gemini configured (gemini-2.5-flash - Latest Stable)")
    except Exception as e:
        print(f"❌ Failed to configure Gemini: {e}")
        return
    
    # Test data
    book_name = "Atomic Habits"
    author_name = "James Clear"
    
    print(f"\n📝 Test Book: {book_name} by {author_name}")
    print("=" * 80)
    
    # === PHASE 1: Generate comprehensive tags ===
    print("\n🚀 PHASE 1: Generating comprehensive tags (60-80 tags)...")
    print("-" * 80)
    
    phase1_prompt = "\n".join(phase1_template)
    phase1_prompt = phase1_prompt.replace("{book_name}", book_name)
    phase1_prompt = phase1_prompt.replace("{author_name}", author_name)
    
    try:
        response1 = model.generate_content(phase1_prompt)
        raw_tags = response1.text.strip()
        
        print(f"\n📦 RAW TAGS (Phase 1):")
        print("-" * 80)
        print(raw_tags[:500] + "..." if len(raw_tags) > 500 else raw_tags)
        print("-" * 80)
        
        # Parse and analyze
        tags_list = [tag.strip() for tag in raw_tags.split(',')]
        raw_length = len(raw_tags)
        
        print(f"\n📊 Phase 1 Statistics:")
        print(f"   Total tags: {len(tags_list)}")
        print(f"   Total characters: {raw_length}")
        print(f"   Average tag length: {raw_length / len(tags_list):.1f} chars")
        
    except Exception as e:
        print(f"❌ Phase 1 failed: {e}")
        return
    
    # === PHASE 2: Optimize tags ===
    print("\n\n⚡ PHASE 2: Optimizing tags to fit 480 chars...")
    print("-" * 80)
    
    phase2_prompt = "\n".join(phase2_template)
    phase2_prompt = phase2_prompt.replace("{raw_tags}", raw_tags)
    phase2_prompt = phase2_prompt.replace("{book_name}", book_name)
    phase2_prompt = phase2_prompt.replace("{author_name}", author_name)
    
    try:
        response2 = model.generate_content(phase2_prompt)
        optimized_tags = response2.text.strip()
        
        print(f"\n✨ OPTIMIZED TAGS (Phase 2):")
        print("=" * 80)
        print(optimized_tags)
        print("=" * 80)
        
        # Parse and analyze
        final_tags = [tag.strip() for tag in optimized_tags.split(',')]
        final_length = len(optimized_tags)
        
        print(f"\n📊 Phase 2 Statistics:")
        print(f"   Total tags: {len(final_tags)}")
        print(f"   Total characters: {final_length}")
        print(f"   Average tag length: {final_length / len(final_tags):.1f} chars")
        
        # Validation
        print(f"\n✅ VALIDATION:")
        checks = []
        
        # Tag count
        if 40 <= len(final_tags) <= 50:
            checks.append(("✅", f"Tag count: {len(final_tags)} (within 40-50)"))
        else:
            checks.append(("⚠️", f"Tag count: {len(final_tags)} (target: 40-50)"))
        
        # Character limit
        if final_length <= 480:
            checks.append(("✅", f"Characters: {final_length}/480 ({480 - final_length} remaining)"))
        else:
            checks.append(("❌", f"Characters: {final_length}/480 (EXCEEDS by {final_length - 480})"))
        
        # Mandatory tags
        mandatory = ["book summary", "audiobook", book_name.lower(), author_name.lower()]
        missing = [tag for tag in mandatory if tag not in optimized_tags.lower()]
        if not missing:
            checks.append(("✅", "All mandatory tags present"))
        else:
            checks.append(("❌", f"Missing: {', '.join(missing)}"))
        
        # Unique tags check (from phase 1)
        unique_concepts = ["habit stacking", "identity based habits", "cue craving response", "4 laws"]
        found_unique = sum(1 for concept in unique_concepts if concept in optimized_tags.lower())
        checks.append(("✅" if found_unique >= 3 else "⚠️", 
                      f"Unique concepts: {found_unique}/4 found"))
        
        # Long-tail tags
        long_tail = [tag for tag in final_tags if len(tag.split()) >= 3]
        checks.append(("✅" if len(long_tail) >= 10 else "⚠️",
                      f"Long-tail tags (3+ words): {len(long_tail)} (target: 10+)"))
        
        for icon, msg in checks:
            print(f"   {icon} {msg}")
        
        # Calculate improvement
        print(f"\n📈 IMPROVEMENT:")
        print(f"   Reduction: {len(tags_list)} → {len(final_tags)} tags ({len(tags_list) - len(final_tags)} removed)")
        print(f"   Compression: {raw_length} → {final_length} chars ({100 - (final_length/raw_length*100):.1f}% reduction)")
        
        # Final score
        passed = sum(1 for icon, _ in checks if icon == "✅")
        total_checks = len(checks)
        score = (passed / total_checks) * 100
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL SCORE: {passed}/{total_checks} ({score:.0f}%)")
        print(f"{'='*80}")
        
        if score >= 80:
            print("✅ EXCELLENT: Two-phase system works perfectly!")
        elif score >= 60:
            print("⚠️ GOOD: Minor improvements needed")
        else:
            print("❌ NEEDS WORK: System needs adjustment")
        
        # Show first 10 final tags
        print(f"\n📋 First 10 Final Tags:")
        for i, tag in enumerate(final_tags[:10], 1):
            print(f"   {i}. {tag} ({len(tag)} chars)")
        
    except Exception as e:
        print(f"❌ Phase 2 failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_two_phase_system()
