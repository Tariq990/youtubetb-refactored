from googleapiclient.discovery import build
from pathlib import Path

# Get API key
repo_root = Path(__file__).resolve().parent
api_key = (repo_root / "secrets" / "api_key.txt").read_text().strip()

# Build YouTube service
youtube = build('youtube', 'v3', developerKey=api_key)

# Get channel uploads playlist
channel_id = 'UCQyOYMG7mH7kwM5O5kMF6tQ'
request = youtube.channels().list(part='contentDetails', id=channel_id)
response = request.execute()
playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

# Get all videos
videos = []
next_page = None

while True:
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50,
        pageToken=next_page
    )
    response = request.execute()
    videos.extend(response['items'])
    
    next_page = response.get('nextPageToken')
    if not next_page:
        break

# Get full titles using videos().list()
print("Fetching full titles and durations...")
video_ids = [v['snippet']['resourceId']['videoId'] for v in videos]
full_videos = []

# Fetch in batches of 50 (API limit)
for i in range(0, len(video_ids), 50):
    batch_ids = video_ids[i:i+50]
    request = youtube.videos().list(
        part='snippet,contentDetails',  # Add contentDetails for duration
        id=','.join(batch_ids)
    )
    response = request.execute()
    full_videos.extend(response['items'])

# Helper function to parse ISO 8601 duration
def parse_duration(duration):
    """Convert ISO 8601 duration (PT1M30S) to seconds"""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

# Print and save all videos with full titles
print(f"\n{'='*120}")
print(f"Total Videos: {len(full_videos)}")
print(f"{'='*120}\n")

# Categorize videos
shorts = []
long_videos = []

for video in full_videos:
    duration = parse_duration(video['contentDetails']['duration'])
    if duration <= 60:  # Shorts are ≤60 seconds
        shorts.append(video)
    else:
        long_videos.append(video)

# Save to file with full titles
with open('video_titles.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total Videos: {len(full_videos)}\n")
    f.write(f"Long Videos: {len(long_videos)}\n")
    f.write(f"Shorts: {len(shorts)}\n")
    f.write("="*120 + "\n\n")
    
    # Print long videos first
    f.write("=== LONG VIDEOS ===\n\n")
    for i, video in enumerate(long_videos, 1):
        title = video['snippet']['title']
        duration = parse_duration(video['contentDetails']['duration'])
        minutes = duration // 60
        seconds = duration % 60
        
        line = f"{i:2}. [{minutes:2}:{seconds:02d}] {title}"
        print(line[:115] + "...")
        f.write(line + '\n')
    
    # Print shorts
    f.write("\n\n=== SHORTS ===\n\n")
    for i, video in enumerate(shorts, 1):
        title = video['snippet']['title']
        duration = parse_duration(video['contentDetails']['duration'])
        
        line = f"{i:2}. [{duration:2}s] {title}"
        print(line[:115] + "...")
        f.write(line + '\n')

print(f"\n{'='*120}")
print(f"✅ Full titles saved to: video_titles.txt")
print(f"📊 Long Videos: {len(long_videos)} | Shorts: {len(shorts)}")
print(f"{'='*120}")
