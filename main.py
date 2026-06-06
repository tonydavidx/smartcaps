import subprocess
import sys
import os
from config import ROOT_FOLDER
from monitor import start_monitoring


def run_command(command):
    print(f"\n--- Running: {' '.join(command)} ---")
    result = subprocess.run([sys.executable] + command, capture_output=True, text=True)
    if result.returncode != 0:
        # Combine stdout and stderr to ensure we catch the error message
        combined_output = (result.stdout + "\n" + result.stderr).strip()
        error_msg = f"Command failed: {' '.join(command)}\n\n{combined_output}"
        print(f"FAILED: {result.stderr}")
        # Send error to telegram
        subprocess.run(
            [sys.executable, f"{ROOT_FOLDER}/telegram_bot.py", "--error", error_msg]
        )
        return False, None

    print(result.stdout.strip())
    output_line = [line for line in result.stdout.split("\n") if "SUCCESS:" in line]
    if output_line:
        filename = output_line[0].split("saved to ")[-1].strip()
        return True, filename
    return True, None


def run_pipeline(video_input, channel_url=None):
    success, transcript_file = run_command(
        [f"{ROOT_FOLDER}/download_transcription.py", video_input]
    )
    if not success or not transcript_file:
        return False

    summary_command = [f"{ROOT_FOLDER}/summary_bot.py", transcript_file]
    if channel_url:
        summary_command.append(channel_url)

    success, summary_file = run_command(summary_command)
    if not success or not summary_file:
        return False

    success, _ = run_command([f"{ROOT_FOLDER}/telegram_bot.py", summary_file])
    return success


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            from monitor import check_for_new_videos

            check_for_new_videos(run_pipeline)
        else:
            # Manual Mode: Process specific video
            run_pipeline(sys.argv[1])
    else:
        start_monitoring(run_pipeline)
