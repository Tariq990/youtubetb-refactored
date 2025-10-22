"""
Multi-source Book Cover Fetcher
Fetches book covers from multiple sources without using paid APIs.
"""

import re
import time
import random
import hashlib
import sys
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import quote


def _get_cover_from_google_books(title: str, author: Optional[str]) -> Optional[str]:
    """
    Fetch book cover from Google Books (free, no API key needed).
    Uses the Google Books free search.
    
    Args:
        title: Book title
        author: Author name (optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        
        query = f"{title} {author}" if author else title
        print(f"[Google Books] Searching for: {query}")
        
        # Google Books API endpoint (no key needed for basic search)
        url = f"https://www.googleapis.com/books/v1/volumes?q={quote(query)}&maxResults=5"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            # Check first few results for best match
            for item in data['items'][:3]:
                volume_info = item.get('volumeInfo', {})
                image_links = volume_info.get('imageLinks', {})
                
                # Try to get highest quality image
                if 'extraLarge' in image_links:
                    cover_url = image_links['extraLarge'].replace('http://', 'https://')
                    print(f"[Google Books] ✓ Found cover (extraLarge)")
                    return cover_url
                elif 'large' in image_links:
                    cover_url = image_links['large'].replace('http://', 'https://')
                    print(f"[Google Books] ✓ Found cover (large)")
                    return cover_url
                elif 'medium' in image_links:
                    cover_url = image_links['medium'].replace('http://', 'https://')
                    print(f"[Google Books] ✓ Found cover (medium)")
                    return cover_url
                elif 'thumbnail' in image_links:
                    # Upgrade thumbnail to larger size
                    cover_url = image_links['thumbnail'].replace('http://', 'https://')
                    cover_url = cover_url.replace('&zoom=1', '&zoom=3')
                    print(f"[Google Books] ✓ Found cover (thumbnail upgraded)")
                    return cover_url
        
        print("[Google Books] ✗ No cover found")
        return None
        
    except Exception as e:
        print(f"[Google Books] ✗ Error: {e}")
        return None


def _get_cover_from_open_library(title: str, author: Optional[str]) -> Optional[str]:
    """
    Fetch book cover from Open Library (free, no API key needed).
    
    Args:
        title: Book title
        author: Author name (optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        
        query = f"{title} {author}" if author else title
        print(f"[Open Library] Searching for: {query}")
        
        # Open Library Search API
        url = f"https://openlibrary.org/search.json?q={quote(query)}&limit=5"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'docs' in data and len(data['docs']) > 0:
            # Check first few results
            for doc in data['docs'][:3]:
                # Try to get cover ID
                if 'cover_i' in doc:
                    cover_id = doc['cover_i']
                    # Open Library cover URL (L = Large, M = Medium, S = Small)
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                    print(f"[Open Library] ✓ Found cover (ID: {cover_id})")
                    return cover_url
                elif 'isbn' in doc and len(doc['isbn']) > 0:
                    # Try ISBN-based cover
                    isbn = doc['isbn'][0]
                    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                    print(f"[Open Library] ✓ Found cover (ISBN: {isbn})")
                    return cover_url
        
        print("[Open Library] ✗ No cover found")
        return None
        
    except Exception as e:
        print(f"[Open Library] ✗ Error: {e}")
        return None


def _get_cover_from_goodreads_scrape(title: str, author: Optional[str]) -> Optional[str]:
    """
    Scrape book cover from Goodreads (no API needed).
    
    Args:
        title: Book title
        author: Author name (optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        query = f"{title} {author}" if author else title
        print(f"[Goodreads] Searching for: {query}")
        
        # Goodreads search URL
        search_url = f"https://www.goodreads.com/search?q={quote(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for book cover image
        cover_img = soup.find('img', class_='bookCover')
        if not cover_img:
            # Try alternative selector
            cover_img = soup.find('img', attrs={'alt': re.compile(title, re.IGNORECASE)})
        
        if cover_img and cover_img.get('src'):
            cover_url = str(cover_img['src'])
            # Upgrade image quality (Goodreads uses _SX/SY for sizes)
            cover_url = re.sub(r'_S[XY]\d+_', '_SX600_', cover_url)
            print(f"[Goodreads] ✓ Found cover")
            return cover_url
        
        print("[Goodreads] ✗ No cover found")
        return None
        
    except Exception as e:
        print(f"[Goodreads] ✗ Error: {e}")
        return None


def _get_cover_from_isbnsearch(title: str, author: Optional[str]) -> Optional[str]:
    """
    Try to find book via ISBNSearch.org and get cover.
    
    Args:
        title: Book title
        author: Author name (optional)
    
    Returns:
        Cover image URL if found, None otherwise
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        query = f"{title} {author}" if author else title
        print(f"[ISBNSearch] Searching for: {query}")
        
        search_url = f"https://isbnsearch.org/search?s={quote(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        time.sleep(random.uniform(0.3, 0.8))
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for book cover
        cover_img = soup.find('img', class_='book-cover')
        if not cover_img:
            cover_img = soup.find('img', attrs={'itemprop': 'image'})
        
        if cover_img and cover_img.get('src'):
            cover_url = str(cover_img['src'])
            if not cover_url.startswith('http'):
                cover_url = f"https://isbnsearch.org{cover_url}"
            print(f"[ISBNSearch] ✓ Found cover")
            return cover_url
        
        print("[ISBNSearch] ✗ No cover found")
        return None
        
    except Exception as e:
        print(f"[ISBNSearch] ✗ Error: {e}")
        return None


def get_book_cover_multi_source(
    title: str, 
    author: Optional[str],
    sources: Optional[List[str]] = None
) -> Optional[str]:
    """
    Try to fetch book cover from multiple sources.
    
    Args:
        title: Book title (English)
        author: Author name (English, optional)
        sources: List of sources to try (default: all sources)
                Options: 'google_books', 'open_library', 'goodreads', 'isbnsearch'
    
    Returns:
        Cover image URL if found from any source, None otherwise
    """
    if not sources:
        # Default order: most reliable first
        sources = ['google_books', 'open_library', 'goodreads', 'isbnsearch']
    
    source_functions = {
        'google_books': _get_cover_from_google_books,
        'open_library': _get_cover_from_open_library,
        'goodreads': _get_cover_from_goodreads_scrape,
        'isbnsearch': _get_cover_from_isbnsearch,
    }
    
    print(f"[Cover] البحث عن غلاف: {title} - {author if author else 'Unknown Author'}")
    
    for source in sources:
        if source not in source_functions:
            print(f"[Cover] Warning: Unknown source '{source}', skipping")
            continue
        
        try:
            cover_url = source_functions[source](title, author)
            if cover_url:
                print(f"[Cover] ✓ تم العثور على الغلاف من {source}")
                return cover_url
            
            # Small delay between sources
            time.sleep(random.uniform(0.3, 0.8))
            
        except Exception as e:
            print(f"[Cover] ✗ خطأ في {source}: {e}")
            continue
    
    print(f"[Cover] ✗ لم يتم العثور على غلاف من جميع المصادر")
    return None


def download_cover_image(cover_url: str, output_path: Path) -> bool:
    """
    Download cover image from URL to local path.
    
    Args:
        cover_url: URL of the cover image
        output_path: Path where to save the image
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        print(f"[Cover] Downloading from: {cover_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(cover_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write image
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"[Cover] ✓ Downloaded to: {output_path}")
        return True
        
    except Exception as e:
        print(f"[Cover] ✗ Download failed: {e}")
        return False
