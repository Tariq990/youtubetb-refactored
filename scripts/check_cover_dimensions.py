#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص أبعاد أغلفة الكتب المجلوبة"""

from PIL import Image
import requests
from io import BytesIO

# URLs من آخر اختبار
covers = [
    ("Zero to One", "https://m.media-amazon.com/images/I/71r+KgczQmL._AC_UL1000_.jpg"),
    ("Atomic Habits", "https://m.media-amazon.com/images/I/71F4+7rk2eL._AC_UL1000_.jpg"),
    ("48 Laws of Power", "https://m.media-amazon.com/images/I/51K3uUsU94L._AC_UL1000_.jpg"),
    ("Think and Grow Rich", "https://m.media-amazon.com/images/I/61IxJuRI39L._AC_UL1000_.jpg"),
]

print("=" * 70)
print("  📐 فحص أبعاد أغلفة الكتب")
print("=" * 70)
print()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

for book_name, url in covers:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        aspect_ratio = width / height
        
        print(f"📖 {book_name}")
        print(f"   العرض: {width}px")
        print(f"   الارتفاع: {height}px")
        print(f"   نسبة الأبعاد: {aspect_ratio:.2f}:1")
        
        # تحديد نوع الغلاف
        if aspect_ratio < 0.7:
            cover_type = "عمودي (Portrait) - طبيعي للكتاب ✓"
        elif aspect_ratio > 1.3:
            cover_type = "أفقي (Landscape) - غير طبيعي ✗"
        else:
            cover_type = "مربع تقريباً"
        
        print(f"   النوع: {cover_type}")
        print()
        
    except Exception as e:
        print(f"❌ {book_name}: خطأ - {e}")
        print()

print("=" * 70)
print("ℹ️  الأبعاد الطبيعية للكتاب: عادة نسبة 0.6:1 إلى 0.7:1 (عمودي)")
print("=" * 70)
