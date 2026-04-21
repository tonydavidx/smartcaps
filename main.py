import sys
from download_transcription import download_transcript
from transcript_GPT import summarize_transcript

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
    summarize_transcript(f"./transcripts/{video_id}_transcript.md")
