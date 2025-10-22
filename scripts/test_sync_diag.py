"""Quick diagnostics for YouTube sync issue."""
from src.infrastructure.adapters import database
from pathlib import Path
import os

print('='*60)
print('YOUTUBE SYNC DIAGNOSTICS')
print('='*60)
print()

# Check API key
print('1. API KEY:')
print('   ENV YT_API_KEY present:', bool(os.environ.get('YT_API_KEY')))
print('   ENV YOUTUBE_API_KEY present:', bool(os.environ.get('YOUTUBE_API_KEY')))
print('   ENV GEMINI_API_KEY present:', bool(os.environ.get('GEMINI_API_KEY')))

api = database._get_youtube_api_key()
if api:
    print(f'   ✅ API key found (first 10 chars): {api[:10]}...')
else:
    print('   ❌ No API key found')

# Check channel ID
print()
print('2. CHANNEL ID:')
chan = database._get_channel_id_from_config()
if chan:
    print(f'   ✅ Channel ID from config: {chan}')
else:
    print('   ❌ No channel ID in config')

# Try fetching channel details
print()
print('3. CHANNEL API TEST:')
if api and chan:
    try:
        from googleapiclient.discovery import build
        youtube = build('youtube', 'v3', developerKey=api)
        
        print('   Calling YouTube Data API...')
        resp = youtube.channels().list(part='contentDetails,snippet', id=chan).execute()
        
        items = resp.get('items', [])
        print(f'   Response items count: {len(items)}')
        
        if items:
            item = items[0]
            print(f'   ✅ Channel found!')
            print(f'      Title: {item["snippet"].get("title")}')
            print(f'      Uploads playlist: {item["contentDetails"]["relatedPlaylists"].get("uploads")}')
            
            # Try to fetch videos from the uploads playlist
            uploads_id = item["contentDetails"]["relatedPlaylists"].get("uploads")
            if uploads_id:
                print()
                print('4. UPLOADS PLAYLIST TEST:')
                print(f'   Trying playlist ID: {uploads_id}')
                try:
                    playlist_resp = youtube.playlistItems().list(
                        part='snippet',
                        playlistId=uploads_id,
                        maxResults=5
                    ).execute()
                    
                    playlist_items = playlist_resp.get('items', [])
                    print(f'   ✅ Playlist accessible! Found {len(playlist_items)} videos (showing first 5)')
                    for idx, vid in enumerate(playlist_items[:3], 1):
                        print(f'      {idx}. {vid["snippet"]["title"][:60]}...')
                except Exception as playlist_err:
                    print(f'   ❌ Playlist error: {playlist_err}')
                    
                    # Try search as fallback
                    print()
                    print('5. SEARCH FALLBACK TEST:')
                    try:
                        search_resp = youtube.search().list(
                            part='snippet',
                            channelId=chan,
                            maxResults=5,
                            order='date',
                            type='video'
                        ).execute()
                        
                        search_items = search_resp.get('items', [])
                        print(f'   Search returned {len(search_items)} videos')
                        if search_items:
                            print('   ✅ Search works! First 3 videos:')
                            for idx, vid in enumerate(search_items[:3], 1):
                                print(f'      {idx}. {vid["snippet"]["title"][:60]}...')
                        else:
                            print('   ❌ Search returned 0 videos')
                            print('   This usually means:')
                            print('      - Channel has no public videos')
                            print('      - Channel ID is incorrect')
                            print('      - Channel is private/hidden')
                    except Exception as search_err:
                        print(f'   ❌ Search error: {search_err}')
        else:
            print('   ❌ Channel not found!')
            print('   This means the channel ID is incorrect or the channel does not exist.')
            
    except Exception as e:
        print(f'   ❌ API Error: {e}')
else:
    if not api:
        print('   ⏭️  Skipped (no API key)')
    if not chan:
        print('   ⏭️  Skipped (no channel ID)')

print()
print('='*60)
print('DIAGNOSTICS COMPLETE')
print('='*60)
