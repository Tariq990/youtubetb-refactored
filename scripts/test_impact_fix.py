"""Test Impact font with adjusted profile"""
from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail

print("🎨 Generating thumbnail with adjusted Impact profile...")
print("=" * 60)

result = generate_thumbnail(
    run_dir=Path('runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad'),
    titles_json=Path('runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad/output.titles.json'),
    output_path=Path('runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad/thumbnail_impact_fixed.jpg'),
    title_font_name='Impact',
    sub_font_name='Impact',
    debug=True
)

print("\n" + "=" * 60)
print(f"✅ Generated: {result}")
print("=" * 60)
