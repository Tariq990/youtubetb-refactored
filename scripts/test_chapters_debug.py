#!/usr/bin/env python3
"""
Test chapter generation with debug logging
Shows exactly why only 1 chapter is generated
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.youtube_metadata import _group_segments_into_chapters


def test_chapter_generation():
    """Test with realistic segment data"""
    
    print("="*70)
    print("🧪 TESTING CHAPTER GENERATION - Debug Mode")
    print("="*70)
    
    # Scenario 1: Normal case (47 segments, 15 minutes total)
    print("\n📊 Test 1: Normal Case (15-minute video)")
    print("-"*70)
    
    normal_segments = []
    for i in range(47):
        normal_segments.append({
            "text": f"Segment {i+1} content here...",
            "start": i * 19.0,  # Each segment ~19 seconds
            "duration": 19.0
        })
    
    total_duration_normal = 15 * 60  # 15 minutes = 900 seconds
    
    print(f"\nInput:")
    print(f"  • Segments: {len(normal_segments)}")
    print(f"  • Total duration: {total_duration_normal}s ({total_duration_normal//60}min)")
    print(f"  • Last segment start: {normal_segments[-1]['start']}s")
    print(f"  • Expected chapters: ~8")
    
    chapters_normal = _group_segments_into_chapters(
        normal_segments, 
        total_duration_normal, 
        target_chapters=8
    )
    
    print(f"\n✅ Result: {len(chapters_normal)} chapters")
    for i, ch in enumerate(chapters_normal[:3]):  # Show first 3
        print(f"   Chapter {i+1}: starts at {ch['start']:.1f}s, {len(ch['segments'])} segments")
    
    # Scenario 2: BUG CASE (total_duration too small)
    print("\n\n📊 Test 2: BUG CASE (total_duration = 0)")
    print("-"*70)
    
    bug_segments = normal_segments.copy()
    total_duration_bug = 0.0  # ← THIS IS THE BUG!
    
    print(f"\nInput:")
    print(f"  • Segments: {len(bug_segments)}")
    print(f"  • Total duration: {total_duration_bug}s ← WRONG!")
    print(f"  • Last segment start: {bug_segments[-1]['start']}s")
    print(f"  • Expected chapters: ~8")
    
    chapters_bug = _group_segments_into_chapters(
        bug_segments,
        total_duration_bug,
        target_chapters=8
    )
    
    print(f"\n❌ Result: {len(chapters_bug)} chapters (PROBLEM!)")
    if chapters_bug:
        for i, ch in enumerate(chapters_bug):
            print(f"   Chapter {i+1}: starts at {ch['start']:.1f}s, {len(ch['segments'])} segments")
    
    # Scenario 3: BUG CASE (total_duration very small)
    print("\n\n📊 Test 3: BUG CASE (total_duration = 50s, but segments go to 893s)")
    print("-"*70)
    
    total_duration_small = 50.0  # Only 50 seconds
    
    print(f"\nInput:")
    print(f"  • Segments: {len(bug_segments)}")
    print(f"  • Total duration: {total_duration_small}s ← TOO SMALL!")
    print(f"  • Last segment start: {bug_segments[-1]['start']}s")
    print(f"  • Expected chapters: ~8")
    
    chapters_small = _group_segments_into_chapters(
        bug_segments,
        total_duration_small,
        target_chapters=8
    )
    
    print(f"\n❌ Result: {len(chapters_small)} chapters")
    if chapters_small:
        for i, ch in enumerate(chapters_small):
            print(f"   Chapter {i+1}: starts at {ch['start']:.1f}s, {len(ch['segments'])} segments")
    
    # Summary
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    print(f"✅ Normal case: {len(chapters_normal)} chapters")
    print(f"❌ Bug case (duration=0): {len(chapters_bug)} chapters")
    print(f"❌ Bug case (duration=50): {len(chapters_small)} chapters")
    
    print("\n🔍 DIAGNOSIS:")
    if len(chapters_bug) <= 1 or len(chapters_small) <= 1:
        print("   ⚠️  CONFIRMED: Low total_duration causes chapter skip!")
        print("   ⚠️  Segments with start >= total_duration are SKIPPED")
        print("   ⚠️  This leaves only 1-2 chapters instead of 8-10")
        print("\n💡 SOLUTION:")
        print("   → Check TTS stage: How is total_duration calculated?")
        print("   → Verify timestamps.json has correct total_duration value")
        print("   → May need to fix _save_timestamps_with_whisper() in tts.py")
    else:
        print("   ✅ No bug detected - all scenarios worked correctly")


if __name__ == "__main__":
    test_chapter_generation()
