from pathlib import Path
import sys
sys.path.append(str(Path.cwd()))
from src.infrastructure.adapters import database as db
print('module loaded')
# Ensure a safe database.json exists
repo_root = Path.cwd()
db_path = repo_root / 'database.json'
if not db_path.exists():
    db_path.write_text('{"books": []}', encoding='utf-8')
print('db exists at', db_path)
# Call some functions
try:
    print('check_book_exists with None author:', db.check_book_exists('Some Book', None))
except Exception as e:
    print('check_book_exists error:', e)

try:
    # Pass empty string instead of None to match function signature (str)
    print('update_book_youtube_url with empty book:', db.update_book_youtube_url('', 'https://youtube.com/watch?v=abc123'))
except Exception as e:
    print('update_book_youtube_url error:', e)

try:
    # Pass empty string instead of None to satisfy static typing
    print('update_book_short_url with empty book:', db.update_book_short_url('', 'https://youtube.com/watch?v=abc123'))
except Exception as e:
    print('update_book_short_url error:', e)

try:
    print('update_book_status with None author:', db.update_book_status('Some Book', None, 'done', youtube_url='https://youtube.com/watch?v=abc123'))
except Exception as e:
    print('update_book_status error:', e)
