from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail

run_dir = Path("runs/2025-10-23_23-38-22_The-Art-of-War")
titles_json = run_dir / "output.titles.json"

print("🔵 Testing Art of War book cover color extraction...\n")

result = generate_thumbnail(
    run_dir=run_dir,
    titles_json=titles_json,
    output_path=Path("thumbnail_artofwar_test.jpg"),
    title_font_name="Bebas Neue",
    debug=True
)

if result:
    print(f"\n✅ Generated: {result}")
else:
    print("\n❌ Failed to generate")
