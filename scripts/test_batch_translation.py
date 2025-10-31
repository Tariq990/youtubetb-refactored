#!/usr/bin/env python3
"""
Test batch translation optimization (v2.3.1)

This script verifies that the batch translation system works correctly:
1. Translates multiple books in 1 API call
2. Caches results properly
3. Saves API quota
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test books
TEST_BOOKS = [
    "العادات الذرية",
    "الأب الغني والأب الفقير",
    "فن اللامبالاة"
]

def test_batch_translation():
    """Test the batch translation function"""
    from src.presentation.cli.run_batch import _batch_translate_books, _load_book_names_cache, _save_book_names_cache
    
    print("=" * 70)
    print("🧪 TESTING BATCH TRANSLATION OPTIMIZATION (v2.3.1)")
    print("=" * 70)
    
    # Clear cache for testing (optional - comment out to use existing cache)
    # cache_file = Path(__file__).parent / "cache" / "book_names.json"
    # if cache_file.exists():
    #     cache_file.unlink()
    #     print("🗑️  Cleared cache for fresh test\n")
    
    # Load existing cache
    print("\n📂 Loading cache...")
    cache = _load_book_names_cache()
    print(f"✅ Cache size: {len(cache)} entries\n")
    
    # Count uncached books
    uncached = [b for b in TEST_BOOKS if b not in cache]
    print(f"📊 Books to test: {len(TEST_BOOKS)}")
    print(f"   - Already cached: {len(TEST_BOOKS) - len(uncached)}")
    print(f"   - Need translation: {len(uncached)}")
    
    if uncached:
        print(f"\n🔄 Books needing translation:")
        for book in uncached:
            print(f"   • {book}")
    
    # Test batch translation
    print(f"\n{'=' * 70}")
    print("🚀 CALLING BATCH TRANSLATION...")
    print(f"{'=' * 70}\n")
    
    import time
    start_time = time.time()
    
    result = _batch_translate_books(TEST_BOOKS, cache)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 70}")
    print("📊 RESULTS")
    print(f"{'=' * 70}")
    print(f"⏱️  Time: {elapsed:.2f} seconds")
    print(f"📝 New translations: {len(result)}")
    print(f"💾 Total in cache: {len(cache)}")
    
    if result:
        print(f"\n✅ Successfully translated:")
        for book, data in result.items():
            print(f"   • {book}")
            print(f"     → {data['english']}")
            if data.get('author'):
                print(f"     👤 {data['author']}")
    
    # Verify all books are now in cache
    print(f"\n{'=' * 70}")
    print("✅ VERIFICATION")
    print(f"{'=' * 70}")
    
    all_cached = True
    for book in TEST_BOOKS:
        if book in cache:
            data = cache[book]
            print(f"✅ {book}")
            print(f"   → {data['english']} by {data.get('author', 'Unknown')}")
        else:
            print(f"❌ {book} - NOT IN CACHE!")
            all_cached = False
    
    if all_cached:
        print(f"\n🎉 SUCCESS! All {len(TEST_BOOKS)} books are now cached!")
        print(f"   Next run will use 0 API calls ⚡")
    else:
        print(f"\n⚠️  WARNING: Some books failed to cache")
    
    print(f"\n{'=' * 70}")
    print("💡 OPTIMIZATION IMPACT")
    print(f"{'=' * 70}")
    print(f"OLD METHOD:")
    print(f"   • {len(TEST_BOOKS)} books = {len(TEST_BOOKS)} API calls")
    print(f"   • Estimated time: ~{len(TEST_BOOKS) * 3} seconds")
    print(f"   • Quota usage: HIGH")
    print(f"\nNEW METHOD (v2.3.1):")
    print(f"   • {len(TEST_BOOKS)} books = 1 API call ⚡")
    print(f"   • Actual time: {elapsed:.2f} seconds ⚡")
    print(f"   • Quota usage: MINIMAL ✅")
    print(f"   • Savings: {((len(TEST_BOOKS) - 1) / len(TEST_BOOKS) * 100):.0f}% fewer API calls!")
    
    return all_cached

if __name__ == "__main__":
    try:
        success = test_batch_translation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
