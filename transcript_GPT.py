import os
import sys
import re
from openai import OpenAI


def parse_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter
    frontmatter = ""
    transcript_text = content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        transcript_text = content[match.end() :]

    return frontmatter, transcript_text


def summarize_transcript(file_path):
    summary_dir = "summary"
    if not os.path.exists(summary_dir):
        os.makedirs(summary_dir)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not found.")
        return

    client = OpenAI(api_key=api_key)

    try:
        frontmatter, transcript_content = parse_markdown(file_path)

        if not transcript_content.strip():
            print("ERROR: Transcript content is empty.")
            return

        print(f"Summarizing {file_path}...")

        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized financial analyst.Your goal is to extract actionable insights from a finance youtube video transcripts. Always output concise and informative summary in structured Markdown. keep it concise but informative. Avoid fluff, repetition, or promotional content. If an information isn't a insight omit it. Focus on key takeaways, trends, and actionable advice relevant to investors and traders. Always provide clear, concise summaries that highlight the most important insights from the transcript.",
                },
                {
                    "role": "user",
                    "content": f"""summarize this transcript:\n\n{transcript_content}""",
                },
            ],
        )

        summary = response.choices[0].message.content

        # Reconstruct Markdown with frontmatter
        md_output = f"""---
{frontmatter}
---
{summary}
"""

        base_name = (
            os.path.basename(file_path).replace(".md", "").replace("_transcript", "")
        )
        summary_file_name = f"summary_{base_name}.md"
        summary_path = os.path.join(summary_dir, summary_file_name)

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(md_output)

        print(f"SUCCESS: Summary saved to {summary_path}")

    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcript_GPT.py <path_to_transcript_md>")
        sys.exit(1)

    transcript_file = sys.argv[1]
    if not os.path.exists(transcript_file):
        print(f"ERROR: File {transcript_file} not found.")
        sys.exit(1)

    summarize_transcript(transcript_file)
