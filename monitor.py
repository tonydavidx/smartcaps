import time
import json
import os
import scrapetube
from config import CHANNELS

DB_FILE = "processed_videos.json"


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


def check_for_new_videos(pipeline_func):
    processed = load_processed_videos()
    any_new_video = False

    for channel_url in CHANNELS:
        print(f"\nScanning channel: {channel_url}")
        try:
            # Fetch latest 3 regular videos (skips shorts and streams)
            videos = scrapetube.get_channel(
                channel_url=channel_url, limit=4, content_type="videos"
            )
            for video in videos:
                video_id = video["videoId"]
                if video_id not in processed:
                    print(f"NEW VIDEO DETECTED: {video_id}")
                    if pipeline_func(video_id):
                        processed.add(video_id)
                        save_processed_videos(processed)
                        any_new_video = True
                else:
                    print(f"Skipping {video_id} (already processed).")
        except Exception as e:
            print(f"Error scanning {channel_url}: {str(e)}")

    if not any_new_video:
        print("\nScan complete. No new videos found.")


def start_monitoring(pipeline_func):
    print("Starting YouTube Channel Monitor...")
    check_for_new_videos(pipeline_func)
