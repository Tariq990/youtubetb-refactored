"""
Language Detection Utility
Detects whether input text is primarily Arabic or English.
"""


def detect_language(text: str) -> str:
    """
    Detect if text is primarily Arabic or English.
    
    Uses Unicode character ranges to identify Arabic text:
    - Arabic: U+0600 to U+06FF
    
    Args:
        text: Input text to analyze
        
    Returns:
        "ar" for Arabic, "en" for English
        
    Examples:
        >>> detect_language("العادات الذرية")
        'ar'
        >>> detect_language("Atomic Habits")
        'en'
        >>> detect_language("48 قانونا للقوة")
        'ar'
    """
    if not text:
        return "en"
    
    # Count Arabic Unicode characters (U+0600 to U+06FF)
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    
    # Count total alphabetic characters
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return "en"
    
    # If more than 30% Arabic characters, consider it Arabic
    arabic_ratio = arabic_chars / total_chars
    return "ar" if arabic_ratio > 0.3 else "en"


def is_arabic(text: str) -> bool:
    """
    Check if text is Arabic.
    
    Args:
        text: Input text to check
        
    Returns:
        True if Arabic, False otherwise
    """
    return detect_language(text) == "ar"


def is_english(text: str) -> bool:
    """
    Check if text is English.
    
    Args:
        text: Input text to check
        
    Returns:
        True if English, False otherwise
    """
    return detect_language(text) == "en"


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("العادات الذرية", "ar"),
        ("Atomic Habits", "en"),
        ("48 قانونا للقوة", "ar"),
        ("Deep Work", "en"),
        ("كيف تكسب الأصدقاء وتؤثر في الناس", "ar"),
        ("The 7 Habits of Highly Effective People", "en"),
        ("التفكير بسرعة وببطء", "ar"),
        ("Thinking, Fast and Slow", "en"),
    ]
    
    print("Language Detection Tests:")
    print("=" * 60)
    
    for text, expected in test_cases:
        detected = detect_language(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text}' → {detected} (expected: {expected})")
