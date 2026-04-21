from youtube_transcript_api import YouTubeTranscriptApi
import sys
from datetime import datetime
import urllib.request
import re
import json


def get_video_metadata(video_id):
    metadata = {"title": "YouTube Video", "upload_date": "Unknown"}
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode()

            # Get Title
            title_match = re.search(r"<title>(.*?)</title>", html)
            if title_match:
                metadata["title"] = title_match.group(1).replace(" - YouTube", "")

            # Get Upload Date (Look for schema.org metadata)
            date_match = re.search(r'"uploadDate":"(.*?)"', html)
            if date_match:
                # Format: 2024-04-12T07:00:01-07:00 -> 2024-04-12
                metadata["upload_date"] = date_match.group(1).split("T")[0]
            else:
                # Fallback: Look for publication date in other tags
                date_match = re.search(
                    r'itemprop="datePublished" content="(.*?)"', html
                )
                if date_match:
                    metadata["upload_date"] = date_match.group(1).split("T")[0]

    except Exception as e:
        print(f"Warning: Could not fetch full metadata ({e})")

    return metadata


def download_transcript(video_id):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        transcript_obj = transcript_list.find_transcript(["ta", "en"])
        fetched_data = transcript_obj.fetch()

        # Extract text
        if hasattr(fetched_data, "snippets"):
            clean_text = "\n".join([snippet.text for snippet in fetched_data.snippets])
        else:
            clean_text = "\n".join([item["text"] for item in fetched_data])

        # Metadata
        meta = get_video_metadata(video_id)
        url = f"https://www.youtube.com/watch?v={video_id}"
        fetch_date = datetime.now().strftime("%Y-%m-%d")

        # Markdown with Frontmatter
        md_content = f"""---
fetch_date: {fetch_date}
upload_date: {meta["upload_date"]}
title: "{meta["title"]}"
url: {url}
---

# Transcript

{clean_text}
"""

        output_file = f"transcripts/{video_id}_transcript.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"SUCCESS: Transcript saved to {output_file}")

    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_transcription.py <video_id>")
        sys.exit(1)

    video_id = sys.argv[1]
    if "v=" in video_id:
        video_id = video_id.split("v=")[1].split("&")[0]
    elif "/" in video_id:
        video_id = video_id.split("/")[-1]

    download_transcript(video_id)
