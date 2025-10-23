#!/usr/bin/env python
"""Test basic Playwright functionality"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_basic():
    template_path = Path("config/template.html").absolute()
    file_url = f"file:///{template_path.as_posix()}"
    
    print(f"📝 Template: {template_path}")
    print(f"🌐 URL: {file_url}")
    print(f"✅ Exists: {template_path.exists()}")
    print()
    
    async with async_playwright() as pw:
        print("🚀 Launching browser...")
        browser = await pw.chromium.launch(headless=True)
        
        print("📄 Creating page...")
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print(f"🔗 Loading {file_url}...")
        try:
            await page.goto(file_url, timeout=10000)
            print("✅ Page loaded successfully!")
            
            title = await page.title()
            print(f"📰 Page title: {title}")
            
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            print("🏁 Browser closed")

if __name__ == "__main__":
    asyncio.run(test_basic())
