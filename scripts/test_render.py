#!/usr/bin/env python
"""Quick test script for rendering Think and Grow Rich"""

from pathlib import Path
from src.infrastructure.adapters.render import main

# Paths
run_dir = Path("runs/2025-10-23_20-05-27_Think-and-Grow-Rich_Think-and-Grow-Rich")
config_dir = Path("config")

# Files
titles_json = run_dir / "output.titles.json"
settings_json = config_dir / "settings.json"
template_html = config_dir / "template.html"
narration_mp3 = run_dir / "narration.mp3"
output_mp4 = run_dir / "video_snap.mp4"

print("🎬 Starting render for Think and Grow Rich...")
print(f"📂 Run directory: {run_dir}")
print(f"📄 Titles: {titles_json.name}")
print(f"⚙️  Settings: {settings_json.name}")
print(f"🎨 Template: {template_html.name}")
print(f"📹 Output: {output_mp4.name}")
print()

# Render
try:
    result = main(
        titles_json=titles_json,
        settings_json=settings_json,
        template_html=template_html,
        narration_mp3=narration_mp3,
        output_mp4=output_mp4,
    )
    
    if result:
        print(f"✅ SUCCESS! Video rendered: {result}")
        print(f"📊 File size: {result.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print("❌ FAILED! Render returned None")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
