import os
import sys
import asyncio
import re
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

env_path = "D:/Documents/Python/variables.env"
load_dotenv(env_path)


def clean_markdown_for_telegram(text):
    """Converts basic Markdown syntax to Telegram-compatible HTML."""
    # 1. Convert bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # 2. Convert headers: ### Header -> <b>Header</b>
    text = re.sub(r"^#+\s*(.*)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 3. Convert bullet points: - Item or * Item -> • Item
    text = re.sub(r"^[*-]\s+", r"• ", text, flags=re.MULTILINE)

    # 4. Convert Markdown links: [text](url) -> <a href="url">text</a>
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    return text.strip()


async def send_to_telegram(file_path):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse frontmatter and content
        title = "Summary"
        url = ""
        summary_text = content

        # Extract info from frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            summary_text = content[fm_match.end() :].strip()

            # Extract title and url from YAML-like frontmatter
            for line in fm_text.split("\n"):
                if line.startswith("title:"):
                    title = line.replace("title:", "").strip().strip('"')
                if line.startswith("url:"):
                    url = line.replace("url:", "").strip()

        # Format the Header
        formatted_header = f"<b>📊 {title}</b>\n\n"
        if url:
            formatted_header += f"🔗 <a href='{url}'>Original Video</a>\n\n"

        # Clean up the summary body
        # Remove original "# Summary" header if it exists
        summary_text = re.sub(r"^#\s*Summary\s*", "", summary_text, flags=re.IGNORECASE).strip()
        
        # Convert Markdown markers to HTML
        summary_html = clean_markdown_for_telegram(summary_text)

        final_message = formatted_header + summary_html

        bot = Bot(token=token)

        # Telegram has a 4096 char limit.
        if len(final_message) > 4090:
            final_message = final_message[:4090] + "..."

        await bot.send_message(
            chat_id=chat_id,
            text=final_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )

        print("SUCCESS: Summary sent to Telegram with improved formatting.")
    except Exception as e:
        print(f"ERROR: Failed to send to Telegram: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python telegram_bot.py <path_to_summary_md>")
        sys.exit(1)

    asyncio.run(send_to_telegram(sys.argv[1]))
