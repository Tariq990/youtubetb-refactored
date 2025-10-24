from pathlib import Path
from src.infrastructure.adapters.thumbnail import generate_thumbnail

run_dir = Path("runs/2025-10-24_07-31-50_Rich-Dad-Poor-Dad")
titles_json = run_dir / "output.titles.json"
output = Path("thumbnail_bebas_xxl.jpg")

print("🔵 Generating thumbnail with Bebas Neue (160px base)...")
result = generate_thumbnail(
    run_dir=run_dir,
    titles_json=titles_json,
    output_path=output,
    title_font_name="Bebas Neue",
    debug=True
)

if result and result.exists():
    print(f"✅ Generated: {result}")
else:
    print("❌ Failed to generate")
