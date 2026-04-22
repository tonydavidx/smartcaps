import subprocess
import sys
import os
from monitor import start_monitoring


def run_command(command):
    print(f"\n--- Running: {' '.join(command)} ---")
    result = subprocess.run([sys.executable] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {result.stderr}")
        return False, None

    print(result.stdout.strip())
    output_line = [line for line in result.stdout.split("\n") if "SUCCESS:" in line]
    if output_line:
        filename = output_line[0].split("saved to ")[-1].strip()
        return True, filename
    return True, None


def run_pipeline(video_input):
    success, transcript_file = run_command(["download_transcription.py", video_input])
    if not success or not transcript_file:
        return False

    success, summary_file = run_command(["transcript_GPT.py", transcript_file])
    if not success or not summary_file:
        return False

    success, _ = run_command(["telegram_bot.py", summary_file])
    return success


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            # For GitHub Actions: Run the scanner once and exit
            from monitor import check_for_new_videos

            check_for_new_videos(run_pipeline)
        else:
            # Manual Mode: Process specific video
            run_pipeline(sys.argv[1])
    else:
        start_monitoring(run_pipeline)
