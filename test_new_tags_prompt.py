"""Test new tags prompt to see what Gemini generates"""
import json
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "src"))

from infrastructure.adapters.youtube_metadata import _configure_model, _generate_ai_tags

# Setup
config_dir = repo_root / "config"
model = _configure_model(config_dir)

if not model:
    print("❌ Could not initialize model")
    sys.exit(1)

book_title = "Atomic Habits"
author_name = "James Clear"

print("🚀 Testing new prompt with _generate_ai_tags...")
print()

tags = _generate_ai_tags(model, book_title, author_name, {}, target_count=60)

print(f"✅ Generated {len(tags)} tags:")
print()
for i, tag in enumerate(tags, 1):
    print(f"{i:2d}. \"{tag}\" ({len(tag)} chars)")

print()
print("=" * 80)
print()

# Calculate stats
raw_chars = sum(len(t) for t in tags)
api_chars = sum(len(t) + (2 if " " in t else 0) for t in tags)
spaced_count = sum(1 for t in tags if " " in t)
spaced_percent = (spaced_count / len(tags)) * 100 if tags else 0

print(f"📊 Statistics:")
print(f"   Total tags: {len(tags)}")
print(f"   Raw chars: {raw_chars}")
print(f"   API chars: {api_chars}")
print(f"   Spaced tags: {spaced_count} ({spaced_percent:.0f}%)")
print(f"   Max tag length: {max(len(t) for t in tags) if tags else 0}")
print(f"   Min tag length: {min(len(t) for t in tags) if tags else 0}")

# Check compliance
print()
print("🔍 Compliance Check:")
tag_count_ok = 28 <= len(tags) <= 32
all_valid_length = all(len(t) <= 26 for t in tags)
raw_in_range = 460 <= raw_chars <= 500
api_ok = api_chars <= 499

print(f"   ✅ Tag count in range 28-32: {'YES ✓' if tag_count_ok else f'NO ❌ (got {len(tags)})'}")
print(f"   ✅ All tags ≤26 chars: {'YES ✓' if all_valid_length else 'NO ❌'}")
print(f"   ✅ Raw chars in 460-500: {'YES ✓' if raw_in_range else f'NO ❌ (got {raw_chars})'}")
print(f"   ✅ API chars ≤499: {'YES ✓' if api_ok else f'NO ❌ (got {api_chars})'}")

