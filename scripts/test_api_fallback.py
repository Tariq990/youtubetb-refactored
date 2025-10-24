from pathlib import Path

print('\n=== Testing API Key Fallback System ===\n')

keys_file = Path('secrets/api_keys.txt')
print(f'📄 File: {keys_file}')
print(f'   Exists: {keys_file.exists()}')

if keys_file.exists():
    lines = [l.strip() for l in keys_file.read_text().splitlines() 
             if l.strip() and not l.strip().startswith('#')]
    print(f'   Keys loaded: {len(lines)}')
    for i, k in enumerate(lines, 1):
        print(f'   Key {i}: {k[:15]}...')
    
    print('\n✅ System ready for fallback!')
else:
    print('\n❌ api_keys.txt not found!')
