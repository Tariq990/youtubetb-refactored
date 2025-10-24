from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail
import json

run_dir = Path("runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad")
titles_json = run_dir / "output.titles.json"

with open(titles_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Test different 5-word titles
test_cases = [
    {
        "name": "5_words_medium (V2)",
        "title": "Build Your Dream Life Today",  # 5 words, avg 4.6 chars
        "output": "test_5words_v2.jpg"
    },
    {
        "name": "4_words_reference",
        "title": "Escape The Rat Race",  # For comparison
        "output": "test_4words_ref.jpg"
    }
]

print("🔵 Testing different 5-word titles:\n")

temp_json = Path("temp_titles.json")

for test in test_cases:
    temp_data = data.copy()
    temp_data['thumbnail_title'] = test['title']
    
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False, indent=2)
    
    word_count = len(test['title'].split())
    avg_len = sum(len(w) for w in test['title'].split()) / word_count
    
    print(f"📝 {test['name']}")
    print(f"   Title: '{test['title']}'")
    print(f"   Words: {word_count} | Avg length: {avg_len:.1f} chars")
    
    result = generate_thumbnail(
        run_dir=run_dir,
        titles_json=temp_json,
        output_path=Path(test['output']),
        title_font_name="Bebas Neue",
        debug=True
    )
    
    print()

temp_json.unlink()

print("✅ All 5-word tests generated!")
