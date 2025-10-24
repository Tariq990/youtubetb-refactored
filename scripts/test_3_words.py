from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail
import json

# Load the original titles
run_dir = Path("runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad")
titles_json = run_dir / "output.titles.json"

# Read and modify to 3 words
with open(titles_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create test versions with different word counts
test_cases = [
    {
        "name": "3_words_short",
        "title": "Think And Grow",  # 3 words, short (4 chars avg)
        "output": "thumbnail_3words_short.jpg"
    },
    {
        "name": "3_words_medium", 
        "title": "Escape The System",  # 3 words, medium (6 chars avg)
        "output": "thumbnail_3words_medium.jpg"
    },
    {
        "name": "3_words_long",
        "title": "Revolutionary Financial Freedom",  # 3 words, long (10 chars avg)
        "output": "thumbnail_3words_long.jpg"
    },
    {
        "name": "4_words (original)",
        "title": "Escape The Rat Race",  # 4 words for comparison
        "output": "thumbnail_4words.jpg"
    }
]

print("🔵 Testing different word counts with Bebas Neue (180px base)...\n")

temp_json = Path("temp_titles.json")

for test in test_cases:
    # Create temp titles file
    temp_data = data.copy()
    temp_data['thumbnail_title'] = test['title']  # Fixed: was 'title', should be 'thumbnail_title'
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 Testing: {test['name']}")
    print(f"   Title: '{test['title']}'")
    
    result = generate_thumbnail(
        run_dir=run_dir,
        titles_json=temp_json,
        output_path=Path(test['output']),
        title_font_name="Bebas Neue",
        debug=True
    )
    
    print()

# Cleanup
temp_json.unlink()

print("✅ All test thumbnails generated!")
print("\nFiles created:")
for test in test_cases:
    print(f"  - {test['output']}")
