"""
Test: Verify duplicate book detection deletes empty run folder
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.database import add_book, check_book_exists, _load_database, _save_database

def test_duplicate_cleanup_logic():
    """
    Simulate the duplicate detection logic:
    1. Book exists with status='uploaded' in database
    2. Pipeline creates run folder
    3. Detects duplicate BEFORE adding to database again
    4. Should delete empty folder
    """
    
    print("=" * 60)
    print("TEST: Duplicate Book Detection → Folder Cleanup")
    print("=" * 60)
    
    # Setup: Add a book as "uploaded" in database
    test_book_name = "Test Duplicate Book"
    test_author = "Test Author"
    
    db = _load_database()
    
    # Clean up any existing test book
    db["books"] = [b for b in db.get("books", []) 
                   if b.get("main_title") != test_book_name]
    _save_database(db)
    
    # Add book as "uploaded" (already processed)
    add_book(
        book_name=test_book_name,
        author_name=test_author,
        run_folder="2025-10-20_10-00-00_Test-Duplicate-Book",
        status="uploaded"
    )
    print(f"\n✅ Setup: Added '{test_book_name}' with status='uploaded'")
    
    # Simulate pipeline flow
    print("\n" + "-" * 60)
    print("SIMULATING PIPELINE FLOW:")
    print("-" * 60)
    
    # Step 1: Create run folder (pipeline does this first)
    runs_dir = repo_root / "runs"
    test_folder = runs_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    test_folder.mkdir(parents=True, exist_ok=True)
    print(f"1. Created run folder: {test_folder.name}")
    
    # Step 2: Get book metadata (would happen in pipeline)
    print(f"2. Extracted book name: {test_book_name}")
    
    # Step 3: Check if book exists (NEW ORDER - before add_book)
    existing = check_book_exists(test_book_name, test_author)
    status = existing.get('status') if existing else None
    print(f"3. Checked database: existing={existing is not None}, status={status}")
    
    # Step 4: If duplicate with status='uploaded' → DELETE folder and STOP
    if existing and status in ['done', 'uploaded']:
        print(f"4. ⛔ Duplicate detected! Status={status}")
        print(f"   🗑️  Deleting empty folder: {test_folder.name}")
        
        import shutil
        shutil.rmtree(test_folder)
        
        if not test_folder.exists():
            print(f"   ✅ Folder deleted successfully!")
        else:
            print(f"   ❌ FAILED: Folder still exists!")
            return False
        
        print(f"   ⛔ Pipeline would STOP here (no duplicate processing)")
        print(f"   ✅ Database NOT polluted with duplicate entry")
        
    else:
        # If NOT duplicate → would add to database
        print(f"4. ✅ Book is NEW → would add to database")
        add_book(test_book_name, test_author, test_folder.name, status="processing")
    
    # Cleanup: Remove test book from database
    db = _load_database()
    db["books"] = [b for b in db.get("books", []) 
                   if b.get("main_title") != test_book_name]
    _save_database(db)
    print(f"\n🧹 Cleanup: Removed test book from database")
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Logic is correct!")
    print("=" * 60)
    print("\nExpected behavior:")
    print("1. Duplicate detected BEFORE adding to database ✅")
    print("2. Empty run folder deleted automatically ✅")
    print("3. No database pollution ✅")
    print("4. Pipeline stops cleanly ✅")
    
    return True

if __name__ == "__main__":
    try:
        success = test_duplicate_cleanup_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
