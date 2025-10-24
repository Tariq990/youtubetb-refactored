"""
Test database.py NoneType fix - Verify defensive None checks work correctly
"""

import json
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.database import (
    check_book_exists,
    update_book_status,
    _load_database,
    _save_database
)

def test_none_handling():
    """Test that functions handle None values gracefully"""
    
    # Create test database with problematic entries
    test_db = {
        "books": [
            {
                "main_title": "Good Book",
                "author_name": "Good Author",
                "status": "processing"
            },
            {
                "main_title": None,  # ⚠️ This would cause NoneType error before fix
                "author_name": "Author Without Title",
                "status": "processing"
            },
            {
                "main_title": "Book Without Author",
                "author_name": None,  # ⚠️ This would cause NoneType error before fix
                "status": "processing"
            },
            {
                "main_title": None,
                "author_name": None,  # ⚠️ Both None - worst case
                "status": "processing"
            }
        ]
    }
    
    # Save test database
    db_path = repo_root / "database.json"
    backup_path = repo_root / "database.json.backup"
    
    # Backup existing database
    if db_path.exists():
        import shutil
        shutil.copy(db_path, backup_path)
        print("✅ Backed up existing database.json")
    
    # Write test database
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(test_db, f, indent=2, ensure_ascii=False)
    print("✅ Created test database with None values")
    
    try:
        # Test 1: check_book_exists should not crash on None values
        print("\n🧪 Test 1: check_book_exists with None values...")
        result = check_book_exists("Good Book", "Good Author")
        assert result is not None, "Should find 'Good Book'"
        print("   ✅ Found book with valid title/author")
        
        result = check_book_exists(None, None)  # type: ignore
        print("   ✅ Handled None book_name gracefully (no crash)")
        
        # Test 2: update_book_status should not crash
        print("\n🧪 Test 2: update_book_status with None values...")
        success = update_book_status("Good Book", "Good Author", "uploaded")
        assert success, "Should update 'Good Book'"
        print("   ✅ Updated book with valid title/author")
        
        # This should NOT crash even though database has None entries
        success = update_book_status("Nonexistent", None, "uploaded")
        print("   ✅ Handled update on nonexistent book (no crash)")
        
        print("\n✅✅✅ ALL TESTS PASSED - NoneType fix is working!")
        
    except AttributeError as e:
        if "'NoneType' object has no attribute 'strip'" in str(e):
            print(f"\n❌ FAILED: NoneType.strip() error still occurring!")
            print(f"   Error: {e}")
            return False
        raise
    
    finally:
        # Restore original database
        if backup_path.exists():
            import shutil
            shutil.move(backup_path, db_path)
            print("\n✅ Restored original database.json")
        else:
            # Remove test database if there was no backup
            if db_path.exists():
                db_path.unlink()
                print("\n✅ Removed test database.json")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE NONETYPE FIX - VERIFICATION TEST")
    print("=" * 60)
    
    success = test_none_handling()
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: All defensive None checks are working correctly!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("FAILED: NoneType errors still present")
        print("=" * 60)
        sys.exit(1)
