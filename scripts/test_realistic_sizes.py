from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail
import json

# Test realistic book titles (not extreme long words)
run_dir = Path("runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad")
titles_json = run_dir / "output.titles.json"

with open(titles_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

test_cases = [
    {
        "name": "2_words",
        "title": "Think Rich",
        "output": "test_2words.jpg"
    },
    {
        "name": "3_words", 
        "title": "Master Your Money",
        "output": "test_3words.jpg"
    },
    {
        "name": "4_words",
        "title": "Escape The Rat Race",
        "output": "test_4words.jpg"
    },
    {
        "name": "5_words",
        "title": "Build Wealth Step By Step",
        "output": "test_5words.jpg"
    }
]

print("🔵 Testing REALISTIC word counts:\n")

temp_json = Path("temp_titles.json")
results = []

for test in test_cases:
    temp_data = data.copy()
    temp_data['thumbnail_title'] = test['title']
    
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 {test['name']}: '{test['title']}'")
    
    result = generate_thumbnail(
        run_dir=run_dir,
        titles_json=temp_json,
        output_path=Path(test['output']),
        title_font_name="Bebas Neue",
        debug=True
    )
    
    print()

temp_json.unlink()

print("✅ All realistic tests generated!")
