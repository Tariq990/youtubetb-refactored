"""
Amazon Book Cover Fetcher using Playwright
Solves the blocking issue by using a real browser
"""

import re
import time
import random
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def _get_book_cover_from_amazon_playwright(title: str, author: Optional[str], max_retries: int = 2) -> Optional[str]:
    """
    Fetch book cover from Amazon using Playwright (real browser).
    More reliable than requests as it avoids bot detection.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
        max_retries: Maximum retry attempts
    
    Returns:
        Cover image URL if found, None otherwise
    """
    import urllib.parse
    
    # Build search query
    query = f"{title} {author}" if author else title
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.amazon.com/s?k={encoded_query}&i=stripbooks&s=relevancerank"
    
    print(f"[Amazon/Playwright] Searching for: {query}")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = random.uniform(3.0, 6.0)
                print(f"[Amazon/Playwright] Retry {attempt + 1}/{max_retries} after {delay:.1f}s...")
                time.sleep(delay)
            
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
                
                page = context.new_page()
                
                # Navigate to search page
                print(f"[Amazon/Playwright] Loading search results...")
                page.goto(search_url, wait_until='networkidle', timeout=30000)
                
                # Wait a bit for dynamic content
                time.sleep(random.uniform(1.5, 2.5))
                
                # Try to find book images
                # Method 1: Look for product images with data-image-index
                images = page.query_selector_all('img.s-image')
                
                if images:
                    # Get the first valid image (usually the most relevant result)
                    for img in images[:3]:  # Check first 3 results
                        src = img.get_attribute('src')
                        if src and 'amazon.com/images' in src and '_AC_' in src:
                            # Upgrade image quality
                            cover_url = re.sub(r'_AC_U[XY]\d+_', '_AC_UL600_', src)
                            print(f"[Amazon/Playwright] [OK] Found cover image")
                            browser.close()
                            return cover_url
                
                # Method 2: Try to find detailed product image
                product_links = page.query_selector_all('a.a-link-normal.s-no-outline')
                if product_links:
                    # Click on first product to get detailed image
                    first_product = product_links[0]
                    href = first_product.get_attribute('href')
                    if href:
                        product_url = href if href.startswith('http') else f"https://www.amazon.com{href}"
                        print(f"[Amazon/Playwright] Opening product page for better image...")
                        page.goto(product_url, wait_until='networkidle', timeout=30000)
                        time.sleep(1.0)
                        
                        # Find the main product image
                        main_img = page.query_selector('img#landingImage, img.a-dynamic-image')
                        if main_img:
                            src = main_img.get_attribute('src')
                            if src and 'amazon.com/images' in src:
                                cover_url = re.sub(r'_AC_U[XY]\d+_', '_AC_UL600_', src)
                                print(f"[Amazon/Playwright] [OK] Found cover from product page")
                                browser.close()
                                return cover_url
                
                browser.close()
                print("[Amazon/Playwright] [X] No cover image found in results")
                
        except PlaywrightTimeout:
            print(f"[Amazon/Playwright] [TIMEOUT] Timeout on attempt {attempt + 1}")
            continue
        except Exception as e:
            print(f"[Amazon/Playwright] [ERROR] Error on attempt {attempt + 1}: {e}")
            continue
    
    print(f"[Amazon/Playwright] [FAILED] Failed after {max_retries} attempts")
    return None


def _get_book_cover_from_amazon_requests(title: str, author: Optional[str]) -> Optional[str]:
    """
    Fallback method using requests (kept for compatibility).
    Less reliable due to bot detection.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        
        # Build search query
        query = f"{title} {author}" if author else title
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.amazon.com/s?k={encoded_query}&i=stripbooks&s=relevancerank"
        
        print(f"[Amazon/Requests] Searching for: {query}")
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1.0, 2.0))
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for product images
        product_img = soup.find('img', class_='s-image')
        if product_img and product_img.get('src'):
            cover_img = str(product_img['src'])
            # Upgrade image quality
            cover_img = re.sub(r'_AC_U[XY]\d+_', '_AC_UL600_', cover_img)
            print(f"[Amazon/Requests] [OK] Found cover image")
            return cover_img
        
        print("[Amazon/Requests] [X] No cover image found")
        return None
        
    except requests.exceptions.HTTPError as e:
        if e.response and e.response.status_code in [503, 403]:
            print(f"[Amazon/Requests] [BLOCKED] Blocked by Amazon ({e.response.status_code})")
        else:
            print(f"[Amazon/Requests] [ERROR] HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"[Amazon/Requests] [ERROR] Error: {e}")
        return None


def get_book_cover_from_amazon(title: str, author: Optional[str], use_playwright: bool = True) -> Optional[str]:
    """
    Main function to get book cover from Amazon.
    Tries Playwright first (more reliable), then falls back to requests.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
        use_playwright: Try Playwright first (recommended)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    if use_playwright:
        try:
            cover_url = _get_book_cover_from_amazon_playwright(title, author)
            if cover_url:
                return cover_url
            print("[Amazon] Playwright failed, trying requests fallback...")
        except Exception as e:
            print(f"[Amazon] Playwright error: {e}")
            print("[Amazon] Falling back to requests method...")
    
    # Fallback to requests
    return _get_book_cover_from_amazon_requests(title, author)
