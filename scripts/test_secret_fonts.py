"""Quick test of font profiles on The Secret book"""
from pathlib import Path
from src.infrastructure.adapters.thumbnail import (
    _load_font_profile,
    _calculate_optimal_title_size
)

# Test titles
titles = [
    "The Power of Attraction",  # 4 words (current)
    "Manifest Dreams",  # 2 words (short)
    "The Secret",  # 2 words (very short)
]

# Load profiles
bebas = _load_font_profile("Bebas Neue", Path("config"))
cairo = _load_font_profile("Cairo", Path("config"))

print("=" * 70)
print("Font Profile Comparison - The Secret Book")
print("=" * 70)

for title in titles:
    bebas_size = _calculate_optimal_title_size(title, bebas, 710)
    cairo_size = _calculate_optimal_title_size(title, cairo, 710)
    diff = bebas_size - cairo_size
    
    print(f"\n'{title}':")
    print(f"  Bebas Neue: {bebas_size}px")
    print(f"  Cairo:      {cairo_size}px")
    print(f"  Difference: {diff:+d}px ({'Bebas bigger' if diff > 0 else 'Cairo bigger'})")

print("\n" + "=" * 70)
print("Profile Details:")
print("=" * 70)
print(f"Bebas Neue: base={bebas['title_base_size']}px, 2-word boost={bebas['dynamic_scaling']['2_words']}x")
print(f"Cairo:      base={cairo['title_base_size']}px, 2-word boost={cairo['dynamic_scaling']['2_words']}x")
