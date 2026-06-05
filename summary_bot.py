import os
import random
import sys
import re
from time import sleep
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
from config import ROOT_FOLDER, SYSTEM_PROMPTS

# Environment loading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, "variables.env")
dot_env_path = os.path.join(BASE_DIR, ".env")
fixed_path = "D:/Documents/Python/variables.env"

if os.path.exists(env_path):
    load_dotenv(env_path)
elif os.path.exists(dot_env_path):
    load_dotenv(dot_env_path)
elif os.path.exists(fixed_path):
    load_dotenv(fixed_path)


def parse_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    frontmatter = ""
    transcript_text = content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        transcript_text = content[match.end() :]
    return frontmatter, transcript_text


def summarize_transcript(file_path):
    max_retries = 5
    summary_dir = f"{ROOT_FOLDER}/summary"
    if not os.path.exists(summary_dir):
        os.makedirs(summary_dir)

    api_key = os.getenv("AISTUDIO_API_KEY")
    if not api_key:
        print("ERROR: AISTUDIO KEY not found.")
        sys.exit(1)

    client = genai.Client()

    frontmatter, transcript_content = parse_markdown(file_path)
    if not transcript_content.strip():
        print("ERROR: Empty transcript.")
        sys.exit(1)

    print(f"Summarizing {file_path}...")
    system_msg = SYSTEM_PROMPTS[0].strip()

    gemini_config = types.GenerateContentConfig(
        system_instruction=system_msg,
        temperature=0.3,
    )

    initial_delay = 10

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=transcript_content,
                config=gemini_config,
            )

            summary = response.text
            md_output = f"---\n{frontmatter}\n---\n\n{summary}\n"

            base_name = (
                os.path.basename(file_path)
                .replace(".md", "")
                .replace("_transcript", "")
            )
            summary_file_name = f"summary_{base_name}.md"
            summary_path = os.path.join(summary_dir, summary_file_name)

            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(md_output)

            print(f"SUCCESS: Summary saved to {summary_path}")
            return summary_path
        except APIError as e:
            if e.code == 503:
                if attempt == max_retries - 1:
                    print(f"ERROR: Service unavailable after {max_retries} attempts.")
                    sys.exit(1)

                delay = initial_delay * (2**attempt) + random.uniform(0, 5)

                sleep(delay)
            else:
                raise e


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcript_GPT.py <path_to_transcript_md>")
        sys.exit(1)
    summarize_transcript(sys.argv[1])
