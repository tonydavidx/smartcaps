import json
import os
import yt_dlp
from config import CHANNELS

# Dynamically get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "processed_videos.json")

def load_processed_videos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_videos(processed_set):
    with open(DB_FILE, "w") as f:
        json.dump(list(processed_set), f)

def get_latest_video_ids(channel_url, limit=3):
    """Uses yt-dlp to get the latest video IDs from a channel URL."""
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'playlist_items': f'1:{limit}',
        'quiet': True,
        'no_warnings': True,
        # Only get actual videos, skip shorts/streams if possible via filter
        'match_filter': lambda info: None if info.get('duration') and info.get('duration') > 60 else 'Skip shorts'
    }
    
    video_ids = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Note: /videos suffix helps yt-dlp focus on the video tab
            target_url = channel_url if channel_url.endswith('/videos') else f"{channel_url.rstrip('/')}/videos"
            info = ydl.extract_info(target_url, download=False)
            if 'entries' in info:
                # filter out None entries and get ids
                video_ids = [entry['id'] for entry in info['entries'] if entry and 'id' in entry]
        except Exception as e:
            print(f"Error fetching videos for {channel_url}: {e}")
            
    return video_ids

def check_for_new_videos(pipeline_func):
    processed = load_processed_videos()
    any_new_video = False

    for channel_url in CHANNELS:
        print(f"\nScanning channel: {channel_url}")
        try:
            # Use yt-dlp instead of scrapetube
            video_ids = get_latest_video_ids(channel_url, limit=3)
            
            for video_id in video_ids:
                if video_id not in processed:
                    print(f"NEW VIDEO DETECTED: {video_id}")
                    # Run the pipeline
                    success = pipeline_func(video_id)
                    
                    # Mark as processed to avoid retry loops on permanent failures
                    processed.add(video_id)
                    save_processed_videos(processed)
                    
                    if success:
                        any_new_video = True
                else:
                    print(f"Skipping {video_id} (already processed).")
        except Exception as e:
            print(f"Error scanning {channel_url}: {str(e)}")

    if not any_new_video:
        print("\nScan complete. No new videos found.")

def start_monitoring(pipeline_func):
    """Run the check exactly once and exit."""
    print("Starting YouTube Channel Scan...")
    check_for_new_videos(pipeline_func)
