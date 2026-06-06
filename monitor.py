import json
import os
import random
from time import sleep
import yt_dlp
import subprocess
import sys
from config import CHANNELS, ROOT_FOLDER

# Dynamically get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "processed_videos.json")


def send_error_to_telegram(message):
    try:
        subprocess.run(
            [sys.executable, f"{ROOT_FOLDER}/telegram_bot.py", "--error", message]
        )
    except Exception as e:
        print(f"Failed to send error to telegram: {e}")


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
    sleep(random.randint(30, 90))


def get_latest_video_ids(channel_url, limit=3):
    """Uses yt-dlp to get the latest video IDs from a channel URL."""
    ydl_opts = {
        "extract_flat": "in_playlist",
        "playlist_items": f"1:{limit}",
        "quiet": True,
        "no_warnings": True,
        # Only get actual videos, skip shorts/streams if possible via filter
        "match_filter": lambda info: (
            None
            if info.get("duration") and info.get("duration") > 60
            else "Skip shorts"
        ),
    }

    video_ids = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Note: /videos suffix helps yt-dlp focus on the video tab
            target_url = (
                channel_url
                if channel_url.endswith("/videos")
                else f"{channel_url.rstrip('/')}/videos"
            )
            info = ydl.extract_info(target_url, download=False)
            if "entries" in info:
                # filter out None entries and get ids
                video_ids = [
                    entry["id"] for entry in info["entries"] if entry and "id" in entry
                ]
        except Exception as e:
            msg = f"Error fetching videos for {channel_url}: {e}"
            print(msg)
            send_error_to_telegram(msg)

    return video_ids


def check_for_new_videos(pipeline_func):
    processed = load_processed_videos()
    any_new_video = False

    for channel_url in CHANNELS:
        print(f"\nScanning channel: {channel_url}")
        try:
            # Use yt-dlp instead of scrapetube
            video_ids = get_latest_video_ids(channel_url, limit=6)
            
            videos_processed_this_channel = 0
            for video_id in video_ids:
                if videos_processed_this_channel >= 2:
                    print(f"Reached limit of 2 videos for this channel. Skipping remaining.")
                    break

                if video_id not in processed:
                    print(f"NEW VIDEO DETECTED: {video_id}")
                    # Run the pipeline
                    success = pipeline_func(video_id, channel_url)

                    if success:
                        # Mark as processed only after successful completion
                        processed.add(video_id)
                        save_processed_videos(processed)
                        any_new_video = True
                        videos_processed_this_channel += 1
                    else:
                        print(f"PIPELINE FAILED for {video_id}. Will not mark as processed.")
                else:
                    print(f"Skipping {video_id} (already processed).")
        except Exception as e:
            msg = f"Error scanning {channel_url}: {str(e)}"
            print(msg)
            send_error_to_telegram(msg)

    if not any_new_video:
        print("\nScan complete. No new videos found.")


def start_monitoring(pipeline_func):
    """Run the check exactly once and exit."""
    print("Starting YouTube Channel Scan...")
    check_for_new_videos(pipeline_func)
