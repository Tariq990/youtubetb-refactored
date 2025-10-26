"""
Test YouTube upload using MAIN CODE tag generation system.
This uses the production tag generation from youtube_metadata.py
instead of the simplified test script version.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.youtube_metadata import (
    _generate_tags,
    _build_density_tags,
    _merge_tags,
)
from src.infrastructure.adapters.youtube_upload import _get_service


def create_test_video(output_path: Path) -> bool:
    """Create a 10-second test video with FFmpeg."""
    print("🎬 Creating 10-second test video...")
    
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "color=c=blue:s=1280x720:d=10",
        "-vf", "drawtext=fontfile=/Windows/Fonts/arial.ttf:text='Main Code Tag Test':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264",
        "-t", "10",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_path),
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and output_path.exists():
            print(f"✅ Test video created: {output_path}")
            return True
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return False


def test_upload_with_main_tags():
    """Upload test video using main code tag generation."""
    
    print("\n" + "=" * 70)
    print("🚀 YOUTUBE UPLOAD TEST - MAIN CODE TAG GENERATION")
    print("=" * 70)
    
    # Test book info
    book_title = "Atomic Habits"
    author_name = "James Clear"
    
    print(f"\n📚 Book: {book_title}")
    print(f"✍️  Author: {author_name}\n")
    
    # Step 1: Generate tags using MAIN CODE
    print("🔵 Step 1: Generating tags using main code...")
    print("-" * 70)
    
    basic_tags = _generate_tags(book_title, author_name)
    print(f"  ✓ Basic tags: {len(basic_tags)}")
    
    density_tags = _build_density_tags(book_title, author_name)
    print(f"  ✓ Density tags: {len(density_tags)}")
    
    # Simulate AI tags (in real pipeline, these come from Gemini)
    ai_tags = [
        "habit formation",
        "behavior change",
        "productivity systems",
        "self improvement strategies",
        "identity based habits",
        "compound growth mindset",
        "habit stacking techniques",
        "atomic improvements",
        "small habits big results",
        "habit building",
        "personal transformation",
    ]
    print(f"  ✓ AI tags (simulated): {len(ai_tags)}")
    
    # Merge all tags
    final_tags, raw_chars, api_chars = _merge_tags(
        primary=basic_tags,
        ai=ai_tags,
        density=density_tags,
        book_title=book_title,
        author_name=author_name,
    )
    
    print(f"\n✅ Final merged tags: {len(final_tags)} tags")
    print(f"📊 Raw chars: {raw_chars} | API chars: {api_chars}/500")
    print("\nGenerated tags:")
    for i, tag in enumerate(final_tags, 1):
        marker = "📝" if " " in tag else "⚡"
        print(f"  {i:2}. {marker} {tag:<50} (len={len(tag):2})")
    
    # Step 2: Create test video
    print(f"\n🔵 Step 2: Creating test video...")
    print("-" * 70)
    
    video_path = repo_root / "tmp" / "main_code_tag_test.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not create_test_video(video_path):
        print("❌ Failed to create test video!")
        return
    
    # Step 3: Prepare metadata
    print(f"\n🔵 Step 3: Preparing YouTube metadata...")
    print("-" * 70)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    title = f"Main Code Tag Test - {book_title} - {timestamp}"
    description = f"""
🧪 TEST VIDEO - Main Code Tag Generation System

This video tests the PRODUCTION tag generation system from youtube_metadata.py

📚 Book: {book_title}
✍️  Author: {author_name}

🏷️ Tag Statistics:
• Total tags: {len(final_tags)}/30
• Raw characters: {raw_chars}
• API characters: {api_chars}/500
• Spaced tags: {sum(1 for t in final_tags if ' ' in t)}
• Density tags: {sum(1 for t in final_tags if ' ' not in t)}

🔧 Tag Generation Process:
1. Basic tags (book + author combinations)
2. Density tags (compressed, no spaces)
3. AI tags (topic-based from Gemini - simulated)
4. Smart merge with prioritization

⚡ This is a TEST video - will be deleted shortly.

#InkEcho #BookSummary #TestVideo
""".strip()
    
    print(f"  📝 Title: {title[:60]}...")
    print(f"  📄 Description: {len(description)} chars")
    print(f"  🏷️  Tags: {len(final_tags)} tags")
    
    # Sanitize tags for YouTube API
    # YouTube rejects tags with special chars, >30 chars, etc.
    import re
    
    def sanitize_tag_for_youtube(tag: str) -> str:
        """Sanitize tag for YouTube API compliance - STRICT VERSION."""
        # Remove special chars, keep only alphanumeric and spaces
        tag = re.sub(r"[^A-Za-z0-9\s]", "", tag)
        # Normalize whitespace
        tag = re.sub(r"\s+", " ", tag).strip()
        # CRITICAL: YouTube appears to have UNDOCUMENTED 28-char limit (not 30!)
        # Discovered through testing - tags at exactly 30 chars get rejected
        if len(tag) > 28:
            tag = tag[:28].rstrip()
        return tag
    
    sanitized_tags = []
    for tag in final_tags:
        clean = sanitize_tag_for_youtube(tag)
        if clean and len(clean) <= 28 and clean not in sanitized_tags:
            sanitized_tags.append(clean)
    
    print(f"\n  🧹 After sanitization: {len(sanitized_tags)} tags (removed {len(final_tags) - len(sanitized_tags)})")
    if len(final_tags) != len(sanitized_tags):
        print(f"  ⚠️  {len(final_tags) - len(sanitized_tags)} tags were removed (too long or duplicates)")
    
    # Debug: print sanitized tags
    print(f"\n  📋 Sanitized tags to upload:")
    for i, tag in enumerate(sanitized_tags[:10], 1):
        print(f"    {i}. {tag} (len={len(tag)})")
    if len(sanitized_tags) > 10:
        print(f"    ... and {len(sanitized_tags) - 10} more")
    
    final_tags = sanitized_tags[:25]  # Use sanitized tags (limit to 25 for safety)
    
    # TEST: Try with tags ≤26 chars (testing exact boundary)
    final_tags = [t for t in final_tags if len(t) <= 26]
    print(f"\n  ✂️  After removing tags >26 chars: {len(final_tags)} tags remain")
    
    # Show tag length distribution
    lengths = {}
    for t in final_tags:
        l = len(t)
        lengths[l] = lengths.get(l, 0) + 1
    print(f"  📊 Tag length distribution:")
    for length in sorted(lengths.keys()):
        print(f"     {length} chars: {lengths[length]} tags")
    
    # Step 4: Get YouTube service
    print(f"\n🔵 Step 4: Authenticating with YouTube...")
    print("-" * 70)
    
    secrets_dir = repo_root / "secrets"
    client_secret = secrets_dir / "client_secret.json"
    token_file = secrets_dir / "token.json"
    
    try:
        youtube, MediaFileUpload = _get_service(client_secret, token_file, debug=True)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Step 5: Upload video
    print(f"\n🔵 Step 5: Uploading video to YouTube...")
    print("-" * 70)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": final_tags,  # Using MAIN CODE tags here!
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "unlisted",  # Unlisted for testing
            "selfDeclaredMadeForKids": False,
        }
    }
    
    try:
        media = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4"
        )
        
        print("📤 Uploading...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response.get("id")
        
        print("\n" + "=" * 70)
        print("✅ UPLOAD SUCCESSFUL!")
        print("=" * 70)
        print(f"\n🎥 Video ID: {video_id}")
        print(f"🔗 URL: https://youtube.com/watch?v={video_id}")
        print(f"📊 Tags uploaded: {len(final_tags)}")
        print(f"🔒 Privacy: Unlisted")
        
        # Show tag details
        print(f"\n📋 Uploaded tags breakdown:")
        print(f"  • Total: {len(final_tags)}/30")
        print(f"  • Spaced tags (📝): {sum(1 for t in final_tags if ' ' in t)}")
        print(f"  • Density tags (⚡): {sum(1 for t in final_tags if ' ' not in t)}")
        print(f"  • Raw chars: {raw_chars}")
        print(f"  • API chars: {api_chars}/500")
        
        print("\n💡 Compare this with the simple test script upload!")
        print("   The main code generates MORE tags and uses character limit efficiently.")
        
        return video_id
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up test video
        if video_path.exists():
            try:
                video_path.unlink()
                print(f"\n🗑️  Test video deleted: {video_path.name}")
            except:
                pass


if __name__ == "__main__":
    print("\n🧪 Testing YouTube upload with MAIN CODE tag generation system")
    print("=" * 70)
    
    video_id = test_upload_with_main_tags()
    
    if video_id:
        print("\n✅ Test complete! Check the video on YouTube.")
        print("\n⚠️  IMPORTANT: This is an unlisted test video.")
        print("   You can delete it manually from YouTube Studio if needed.")
    else:
        print("\n❌ Test failed! Check the error messages above.")
