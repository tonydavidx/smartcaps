import subprocess
import sys
import os

def run_command(command):
    print(f"\n--- Running: {' '.join(command)} ---")
    result = subprocess.run([sys.executable] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {result.stderr}")
        return False, None
    
    print(result.stdout.strip())
    # Try to extract the filename from the success message
    # e.g., "SUCCESS: Transcript saved to 67k2-xh4bIE_transcript.md"
    output_line = [line for line in result.stdout.split('\n') if "SUCCESS:" in line]
    if output_line:
        filename = output_line[0].split("saved to ")[-1].strip()
        return True, filename
    return True, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <youtube_url_or_id>")
        sys.exit(1)

    video_input = sys.argv[1]

    # Step 1: Download Transcript
    success, transcript_file = run_command(["download_transcription.py", video_input])
    if not success or not transcript_file:
        print("Pipeline stopped at Step 1.")
        sys.exit(1)

    # Step 2: Generate Summary
    success, summary_file = run_command(["transcript_GPT.py", transcript_file])
    if not success or not summary_file:
        print("Pipeline stopped at Step 2.")
        sys.exit(1)

    # Step 3: Send to Telegram
    success, _ = run_command(["telegram_bot.py", summary_file])
    if not success:
        print("Pipeline stopped at Step 3.")
        sys.exit(1)

    print("\n" + "="*30)
    print("ALL STEPS COMPLETED SUCCESSFULLY!")
    print("="*30)

if __name__ == "__main__":
    main()
