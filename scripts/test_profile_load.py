from pathlib import Path
import json

# Read settings
p = Path('config/settings.json')
data = json.loads(p.read_text(encoding='utf-8'))
bebas = data['thumbnail_font_profiles']['Bebas Neue']

print(f"✅ Bebas Neue profile in settings.json:")
print(f"   title_base_size: {bebas['title_base_size']}px")
print(f"   title_max_size: {bebas['title_max_size']}px")
print(f"   subtitle_base_size: {bebas['subtitle_base_size']}px")

# Test the function
from src.infrastructure.adapters.thumbnail import _load_font_profile

loaded = _load_font_profile("Bebas Neue", Path("config"))
print(f"\n✅ Loaded via _load_font_profile:")
print(f"   title_base_size: {loaded['title_base_size']}px")
print(f"   title_max_size: {loaded['title_max_size']}px")
print(f"   subtitle_base_size: {loaded['subtitle_base_size']}px")

if bebas['title_base_size'] == loaded['title_base_size']:
    print("\n✅ MATCH! Function loads correctly")
else:
    print(f"\n❌ MISMATCH! File={bebas['title_base_size']} vs Loaded={loaded['title_base_size']}")
