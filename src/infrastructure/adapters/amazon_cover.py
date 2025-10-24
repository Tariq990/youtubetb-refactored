"""
Amazon Book Cover Fetcher using Playwright with Cookies
Fetches book covers from Amazon using cookies to avoid blocking.
Selects the book with highest rating and review count.
"""

import re
import time
import random
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests


def _load_cookies_from_file(cookies_path: Path) -> List[Dict[str, Any]]:
    """
    Load cookies from Netscape format file (cookies.txt).
    
    Args:
        cookies_path: Path to cookies.txt file
    
    Returns:
        List of cookie dictionaries for Playwright
    """
    try:
        if not cookies_path.exists():
            print(f"[Cookies] File not found: {cookies_path}")
            return []
        
        cookies: List[Dict[str, Any]] = []
        with open(cookies_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse Netscape format: domain  flag  path  secure  expiration  name  value
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain, _, path, secure, expiration, name, value = parts[:7]
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'expires': int(expiration) if expiration != '0' else -1,
                        'httpOnly': False,
                        'secure': secure.upper() == 'TRUE',
                        'sameSite': 'None' if secure.upper() == 'TRUE' else 'Lax'
                    })
        
        print(f"[Cookies] Loaded {len(cookies)} cookies from {cookies_path.name}")
        return cookies
    
    except Exception as e:
        print(f"[Cookies] Error loading cookies: {e}")
        return []


def _extract_book_info(element) -> Dict:
    """
    Extract book information including rating and review count.
    
    Args:
        element: Playwright element representing a book
    
    Returns:
        Dictionary with book info (rating, reviews, image_url)
    """
    try:
        info = {
            'rating': 0.0,
            'reviews': 0,
            'image_url': None,
            'score': 0
        }
        
        # Extract rating (e.g., "4.7 out of 5 stars")
        rating_elem = element.query_selector('[data-cy="reviews-ratings-slot"], .a-icon-star-small, .a-icon-star')
        if rating_elem:
            rating_text = rating_elem.get_attribute('aria-label') or rating_elem.text_content() or ''
            match = re.search(r'(\d+\.?\d*)\s*out of 5', rating_text)
            if match:
                info['rating'] = float(match.group(1))
        
        # Extract review count (e.g., "12,345" or "12.3K")
        review_elem = element.query_selector('[data-csa-c-content-id="reviews-count"], .a-size-small .a-link-normal')
        if review_elem:
            review_text = review_elem.text_content() or ''
            # Remove commas and parse number
            review_text = review_text.replace(',', '').strip()
            # Handle K notation (e.g., "12.3K" = 12300)
            if 'K' in review_text.upper():
                match = re.search(r'(\d+\.?\d*)', review_text)
                if match:
                    info['reviews'] = int(float(match.group(1)) * 1000)
            else:
                match = re.search(r'(\d+)', review_text)
                if match:
                    info['reviews'] = int(match.group(1))
        
        # Extract image URL with STRICT validation
        img_elem = element.query_selector('img.s-image')
        if img_elem:
            src = img_elem.get_attribute('src')
            if src:
                # CRITICAL FILTERS: Reject invalid/placeholder images
                # 1. Must be from Amazon CDN
                if 'amazon.com/images' not in src:
                    return info
                
                # 2. Must have proper product image format (_AC_)
                if '_AC_' not in src:
                    return info
                
                # 3. REJECT placeholder images with solid backgrounds
                # These patterns indicate non-book images:
                # - "no-img" / "no-image" / "placeholder"
                # - Very short image IDs (placeholders are often short)
                # - Transparent/1x1 pixel images
                src_lower = src.lower()
                if any(pattern in src_lower for pattern in [
                    'no-img', 'no-image', 'placeholder', 'blank',
                    'transparent', '1x1', 'pixel', 'spacer'
                ]):
                    print(f"  [Filter] Rejected placeholder image: {src[:80]}...")
                    return info
                
                # 4. REJECT images from non-book categories
                # Amazon uses specific patterns for book covers vs. other products
                # Book covers typically have longer image IDs
                # Extract image ID (the part between /I/ and ._AC_)
                img_id_match = re.search(r'/I/([A-Za-z0-9+\-_]+)\.', src)
                if img_id_match:
                    img_id = img_id_match.group(1)
                    # Amazon book cover IDs are typically 10-15 chars
                    # Very short IDs (<8 chars) are often placeholders
                    if len(img_id) < 8:
                        print(f"  [Filter] Rejected very short image ID (placeholder): {img_id}")
                        return info
                    
                    # 5. Upgrade to HIGHEST quality (UL1000 = best quality)
                    # Replace any size modifier with max quality
                    high_quality_url = re.sub(r'_AC_U[XY]\d+_', '_AC_UL1000_', src)
                    high_quality_url = re.sub(r'_SX\d+_', '_SX1000_', high_quality_url)
                    high_quality_url = re.sub(r'_SY\d+_', '_SY1000_', high_quality_url)
                    
                    info['image_url'] = high_quality_url
                    print(f"  [Filter] ✓ Valid book cover detected (ID: {img_id}, length: {len(img_id)})")
                else:
                    # No image ID found - use original URL with quality upgrade
                    high_quality_url = re.sub(r'_AC_U[XY]\d+_', '_AC_UL1000_', src)
                    info['image_url'] = high_quality_url
                    print(f"  [Filter] ✓ Valid book cover detected (no ID pattern)")


        
        # Calculate score: rating * 10 + min(reviews/100, 10)
        # This gives priority to highly rated books with many reviews
        if info['rating'] > 0:
            rating_score = info['rating'] * 10  # Max 50 points
            review_score = min(info['reviews'] / 100, 10)  # Max 10 points
            info['score'] = rating_score + review_score
        
        return info
    
    except Exception as e:
        print(f"[Extract] Error: {e}")
        return {'rating': 0.0, 'reviews': 0, 'image_url': None, 'score': 0}


def _get_book_cover_from_amazon_playwright(
    title: str, 
    author: Optional[str], 
    cookies_path: Optional[Path] = None,
    max_retries: int = 3
) -> Optional[str]:
    """
    Fetch book cover from Amazon using Playwright with cookies.
    Selects the book with highest rating and review count.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
        cookies_path: Path to cookies.txt file (default: secrets/cookies.txt)
        max_retries: Maximum retry attempts
    
    Returns:
        Cover image URL if found, None otherwise
    """
    import urllib.parse
    
    # Default cookies path
    if cookies_path is None:
        # Try multiple locations
        for path in [Path('secrets/cookies.txt'), Path('cookies.txt')]:
            if path.exists():
                cookies_path = path
                break
    
    # Load cookies
    cookies = []
    if cookies_path and cookies_path.exists():
        cookies = _load_cookies_from_file(cookies_path)
    else:
        print(f"[Amazon] Warning: No cookies file found, may be blocked")
    
    # Build search query
    query = f"{title} {author}" if author else title
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.amazon.com/s?k={encoded_query}&i=stripbooks&s=relevancerank"
    
    print(f"[Amazon] Searching for: {query}")
    if cookies and cookies_path:
        print(f"[Amazon] Using {len(cookies)} cookies from {cookies_path.name}")
    elif cookies:
        print(f"[Amazon] Using {len(cookies)} cookies")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = random.uniform(3.0, 6.0)
                print(f"[Amazon] Retry {attempt + 1}/{max_retries} after {delay:.1f}s...")
                time.sleep(delay)
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
                
                # Add cookies to context
                if cookies:
                    # Cast to proper type for Playwright
                    context.add_cookies(cookies)  # type: ignore[arg-type]
                
                page = context.new_page()
                
                # Navigate to search page
                print(f"[Amazon] Loading search results...")
                page.goto(search_url, wait_until='domcontentloaded', timeout=45000)
                
                # Wait for search results to load
                time.sleep(random.uniform(2.0, 3.0))
                
                # Find all book results
                product_divs = page.query_selector_all('[data-component-type="s-search-result"]')
                
                if not product_divs:
                    print("[Amazon] No search results found")
                    browser.close()
                    continue
                
                print(f"[Amazon] Found {len(product_divs)} results, analyzing...")
                
                # Extract info from first 5 results WITH TITLE VALIDATION
                books = []
                for idx, div in enumerate(product_divs[:10]):  # Check more results (10 instead of 5)
                    # CRITICAL: Validate book title FIRST before extracting image
                    title_elem = div.query_selector('h2 a span, .a-size-medium.a-text-normal')
                    if not title_elem:
                        continue
                    
                    book_title = (title_elem.text_content() or '').strip()
                    if not book_title:
                        continue
                    
                    # FILTER 1: Title must be substantial (not just 1-2 words)
                    title_words = book_title.split()
                    if len(title_words) < 2:
                        print(f"  [Filter] Skipped result #{idx+1}: Title too short ({book_title})")
                        continue
                    
                    # FILTER 2: Reject non-book items (common Amazon junk)
                    title_lower = book_title.lower()
                    blocked_keywords = [
                        'kindle', 'case', 'cover', 'stand', 'holder', 
                        'bag', 'sleeve', 'skin', 'protector', 'screen',
                        'charger', 'cable', 'adapter', 'mount', 'dock',
                        'light', 'lamp', 'clip', 'bookmark', 'pen'
                    ]
                    if any(keyword in title_lower for keyword in blocked_keywords):
                        print(f"  [Filter] Skipped result #{idx+1}: Non-book item ({book_title})")
                        continue
                    
                    # FILTER 3: Title relevance check (fuzzy match with search query)
                    # At least 30% of search words should appear in result title
                    search_words = set(title.lower().split())
                    title_words_set = set(title_lower.split())
                    common_words = search_words.intersection(title_words_set)
                    relevance = len(common_words) / len(search_words) if search_words else 0
                    
                    if relevance < 0.3:  # Less than 30% match
                        print(f"  [Filter] Skipped result #{idx+1}: Low relevance ({relevance:.0%}) - {book_title}")
                        continue
                    
                    # Extract full book info (rating, reviews, image)
                    info = _extract_book_info(div)
                    
                    if info['image_url']:
                        info['position'] = idx
                        info['title'] = book_title
                        info['relevance'] = relevance
                        books.append(info)
                        print(f"  Book #{idx+1}: {book_title[:50]}")
                        print(f"    Rating={info['rating']:.1f}, Reviews={info['reviews']}, Relevance={relevance:.0%}, Score={info['score']:.1f}")

                
                if not books:
                    print("[Amazon] No valid books with covers found after filtering")
                    browser.close()
                    continue
                
                # Sort by COMPOSITE score: (relevance * 50) + (rating * 10) + min(reviews/100, 10)
                # This prioritizes: relevance > rating > review count
                for book in books:
                    book['composite_score'] = (
                        book['relevance'] * 50 +  # Relevance is MOST important
                        book['rating'] * 10 +      # Then rating
                        min(book['reviews'] / 100, 10)  # Then reviews
                    )
                
                books.sort(key=lambda x: x['composite_score'], reverse=True)
                
                # Select best book
                best_book = books[0]
                print(f"\n[Amazon] ✅ SELECTED BEST MATCH:")
                print(f"  Title: {best_book.get('title', 'N/A')[:60]}")
                print(f"  Rating: {best_book['rating']:.1f} ⭐")
                print(f"  Reviews: {best_book['reviews']:,}")
                print(f"  Relevance: {best_book['relevance']:.0%}")
                print(f"  Position: #{best_book['position']+1}")
                print(f"  Composite Score: {best_book['composite_score']:.1f}")

                
                browser.close()
                return best_book['image_url']
                
        except PlaywrightTimeout:
            print(f"[Amazon] Timeout on attempt {attempt + 1}")
            continue
        except Exception as e:
            print(f"[Amazon] Error on attempt {attempt + 1}: {e}")
            continue
    
    print(f"[Amazon] Failed after {max_retries} attempts")
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


def _get_book_cover_from_google_books(title: str, author: Optional[str]) -> Optional[str]:
    """
    Get book cover from Google Books API.
    Fast and reliable alternative to scraping.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        import urllib.parse
        
        # Build search query
        query = f"intitle:{title}"
        if author:
            query += f" inauthor:{author}"
        
        encoded_query = urllib.parse.quote(query)
        api_url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=5"
        
        print(f"[Google Books] Searching for: {title} by {author or 'Unknown'}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' in data and data['items']:
            # Look through results for the best match
            for item in data['items']:
                volume_info = item.get('volumeInfo', {})
                
                # Check if title matches closely
                api_title = volume_info.get('title', '').lower()
                search_title = title.lower()
                
                # Simple title matching (could be improved)
                if search_title in api_title or api_title in search_title:
                    # Get the largest available image
                    images = volume_info.get('imageLinks', {})
                    
                    # Prefer large thumbnail
                    cover_url = images.get('large') or images.get('medium') or images.get('small') or images.get('thumbnail')
                    
                    if cover_url:
                        # Remove size restrictions from Google Books URLs
                        cover_url = re.sub(r'&zoom=\d+', '', cover_url)
                        cover_url = re.sub(r'&edge=curl', '', cover_url)
                        print(f"[Google Books] [OK] Found cover image")
                        return cover_url
            
            print("[Google Books] [X] No matching book found")
            return None
        
        print("[Google Books] [X] No results from API")
        return None
        
    except Exception as e:
        print(f"[Google Books] [ERROR] {e}")
        return None


def get_book_cover_from_amazon(
    title: str, 
    author: Optional[str], 
    use_playwright: bool = True,
    cookies_path: Optional[Path] = None
) -> Optional[str]:
    """
    Main function to get book cover from Amazon ONLY.
    Uses Playwright with cookies to avoid blocking.
    Selects the book with highest rating and review count.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
        use_playwright: Always True (kept for compatibility)
        cookies_path: Path to cookies.txt file (default: auto-detect)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    print(f"[Cover] Using Amazon with cookies (rating-based selection)")
    
    try:
        cover_url = _get_book_cover_from_amazon_playwright(
            title, 
            author, 
            cookies_path=cookies_path,
            max_retries=3
        )
        if cover_url:
            return cover_url
        print("[Amazon] Playwright with cookies failed")
    except Exception as e:
        print(f"[Amazon] Error: {e}")
    
    return None
