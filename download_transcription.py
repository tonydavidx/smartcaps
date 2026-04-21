from youtube_transcript_api import YouTubeTranscriptApi
import sys
from datetime import datetime
import urllib.request
import re


def get_video_title(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode()
            match = re.search(r"<title>(.*?)</title>", html)
            if match:
                title = match.group(1).replace(" - YouTube", "")
                return title
    except:
        pass
    return "YouTube Video"


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
        title = get_video_title(video_id)
        url = f"https://www.youtube.com/watch?v={video_id}"
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Markdown with Frontmatter
        md_content = f"""---
date: {date_str}
title: "{title}"
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
    download_transcript("RK1ZdGcZHrA")
