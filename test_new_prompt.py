"""Quick test for new AI tags prompt."""

from src.infrastructure.adapters.youtube_metadata import _generate_ai_tags
import google.generativeai as genai
from pathlib import Path

# Load API key
api_key = Path("secrets/api_key.txt").read_text().strip().split('\n')[0]
genai.configure(api_key=api_key)

# Create model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Test with Atomic Habits
print("🧪 Testing new AI tags prompt with 'Atomic Habits'...\n")
tags = _generate_ai_tags(model, 'Atomic Habits', 'James Clear', {}, target_count=60)

# Display results
print("📋 GENERATED TAGS:")
print("=" * 70)
for i, tag in enumerate(tags, 1):
    print(f"{i:2d}. {tag:30s} ({len(tag):2d} chars)")

print("\n" + "=" * 70)
print(f"📊 STATISTICS:")
print(f"   Total tags: {len(tags)}")
print(f"   Raw chars: {sum(len(t) for t in tags)}")
print(f"   API chars: {sum(len(t) + (2 if ' ' in t else 0) for t in tags)}")
print(f"   Spaced tags: {sum(1 for t in tags if ' ' in t)} ({sum(1 for t in tags if ' ' in t)/len(tags)*100:.0f}%)")
print(f"   Longest tag: {max(len(t) for t in tags)} chars")
print(f"   Shortest tag: {min(len(t) for t in tags)} chars")

# Check compliance
print(f"\n✅ VALIDATION:")
print(f"   All tags ≤26 chars: {all(len(t) <= 26 for t in tags)}")
print(f"   API limit (≤499): {sum(len(t) + (2 if ' ' in t else 0) for t in tags) <= 499}")
print(f"   Tag count (25-30): {25 <= len(tags) <= 30}")
