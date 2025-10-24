"""
Test font profile system with both Bebas Neue and Cairo fonts.
Validates dynamic sizing for each font profile.
"""
from pathlib import Path
import json

def test_profile_loading():
    """Test loading font profiles from settings.json"""
    config_dir = Path("config")
    settings_path = config_dir / "settings.json"
    
    if not settings_path.exists():
        print("❌ settings.json not found!")
        return False
    
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    profiles = settings.get("thumbnail_font_profiles", {})
    
    print("=" * 60)
    print("Font Profiles Test")
    print("=" * 60)
    
    # Test Bebas Neue profile
    bebas = profiles.get("Bebas Neue")
    if bebas:
        print("\n✅ Bebas Neue Profile Found:")
        print(f"   - Base size: {bebas['title_base_size']}px")
        print(f"   - Range: {bebas['title_min_size']}-{bebas['title_max_size']}px")
        print(f"   - 2 words boost: {bebas['dynamic_scaling']['2_words']}x")
        print(f"   - Decay rate: {bebas['dynamic_scaling']['decay_rate']}")
    else:
        print("❌ Bebas Neue profile not found!")
        return False
    
    # Test Cairo profile
    cairo = profiles.get("Cairo")
    if cairo:
        print("\n✅ Cairo Profile Found:")
        print(f"   - Base size: {cairo['title_base_size']}px")
        print(f"   - Range: {cairo['title_min_size']}-{cairo['title_max_size']}px")
        print(f"   - 2 words boost: {cairo['dynamic_scaling']['2_words']}x")
        print(f"   - Decay rate: {cairo['dynamic_scaling']['decay_rate']}")
    else:
        print("❌ Cairo profile not found!")
        return False
    
    print("\n" + "=" * 60)
    print("Profile Comparison:")
    print("=" * 60)
    print(f"Bebas Neue: {bebas['title_base_size']}px base (AGGRESSIVE)")
    print(f"Cairo:      {cairo['title_base_size']}px base (CONSERVATIVE)")
    print(f"\nBebas 2-word boost: {bebas['dynamic_scaling']['2_words']}x")
    print(f"Cairo 2-word boost: {cairo['dynamic_scaling']['2_words']}x")
    print(f"\nBebas decay: {bebas['dynamic_scaling']['decay_rate']} (slower)")
    print(f"Cairo decay: {cairo['dynamic_scaling']['decay_rate']} (faster)")
    
    return True

def test_font_discovery():
    """Test if font files are available"""
    from src.infrastructure.adapters.thumbnail import _bebas_neue_candidates, _cairo_candidates
    
    print("\n" + "=" * 60)
    print("Font Discovery Test")
    print("=" * 60)
    
    # Test Bebas Neue
    bebas_fonts = _bebas_neue_candidates("bold")
    if bebas_fonts:
        print(f"\n✅ Found {len(bebas_fonts)} Bebas Neue font(s):")
        for f in bebas_fonts[:3]:  # Show first 3
            print(f"   - {f}")
    else:
        print("\n⚠️ No Bebas Neue fonts found!")
    
    # Test Cairo
    cairo_fonts = _cairo_candidates("bold")
    if cairo_fonts:
        print(f"\n✅ Found {len(cairo_fonts)} Cairo font(s):")
        for f in cairo_fonts[:3]:  # Show first 3
            print(f"   - {f}")
    else:
        print("\n⚠️ No Cairo fonts found!")
        print("   To use Cairo font, download from:")
        print("   https://fonts.google.com/specimen/Cairo")
        print("   Then install to: C:/Windows/Fonts/ or assets/fonts/")
    
    return True

def test_sizing_differences():
    """Test sizing calculation differences between fonts"""
    from src.infrastructure.adapters.thumbnail import _load_font_profile, _calculate_optimal_title_size
    
    print("\n" + "=" * 60)
    print("Sizing Calculation Test")
    print("=" * 60)
    
    test_titles = [
        "Success",  # 1 word
        "Think Big",  # 2 words
        "The Art of War",  # 4 words
        "How to Win Friends and Influence People",  # 7 words
    ]
    
    config_dir = Path("config")
    bebas_profile = _load_font_profile("Bebas Neue", config_dir)
    cairo_profile = _load_font_profile("Cairo", config_dir)
    
    for title in test_titles:
        bebas_size = _calculate_optimal_title_size(title, bebas_profile, max_width=700)
        cairo_size = _calculate_optimal_title_size(title, cairo_profile, max_width=700)
        
        print(f"\n'{title}':")
        print(f"  Bebas Neue: {bebas_size}px")
        print(f"  Cairo:      {cairo_size}px")
        print(f"  Difference: {bebas_size - cairo_size:+d}px")
    
    return True

if __name__ == "__main__":
    print("\n" + "🔤" * 30)
    print("Font Profile System Test")
    print("🔤" * 30 + "\n")
    
    success = True
    success &= test_profile_loading()
    success &= test_font_discovery()
    success &= test_sizing_differences()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests completed!")
        print("\nTo use Cairo font:")
        print("1. Download Cairo font from Google Fonts")
        print("2. Install to C:/Windows/Fonts/ or assets/fonts/")
        print("3. Change thumbnail_title_font in config/settings.json to 'Cairo'")
    else:
        print("❌ Some tests failed!")
    print("=" * 60 + "\n")
