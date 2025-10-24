import json
from pathlib import Path

db = json.loads(Path('src/database.json').read_text())

print('\n=== Database Status ===\n')

done = [b for b in db['books'] if b.get('status') == 'done']
processing = [b for b in db['books'] if b.get('status') == 'processing']
uploaded = [b for b in db['books'] if b.get('status') == 'uploaded']

print(f'✅ Done: {len(done)}')
print(f'🔄 Processing: {len(processing)}')
print(f'📤 Uploaded: {len(uploaded)}')
print(f'\nTotal: {len(db["books"])}')

print('\n--- Done Books ---')
for b in done:
    print(f'  ✅ {b["main_title"]}')
    
print('\n--- Processing Books ---')
for b in processing:
    print(f'  🔄 {b["main_title"]}')
