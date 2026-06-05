import os
import sys
import asyncio
import re
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Dynamic path for .env file
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

async def send_error_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment.")
        return

    try:
        bot = Bot(token=token)
        final_message = f"❌ <b>Error in SmartCaps Pipeline</b>\n\n{message}"
        if len(final_message) > 4090:
            final_message = final_message[:4090] + "..."

        await bot.send_message(
            chat_id=chat_id,
            text=final_message,
            parse_mode=ParseMode.HTML,
        )
        print("SUCCESS: Error message sent to Telegram.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

async def send_to_telegram(file_path):
    # GitHub Actions will provide these via repository secrets
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        title = "Summary"
        url = ""
        summary_text = content

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            summary_text = content[fm_match.end() :].strip()
            for line in fm_text.split("\n"):
                if line.startswith("title:"):
                    title = line.replace("title:", "").strip().strip('"')
                if line.startswith("url:"):
                    url = line.replace("url:", "").strip()

        formatted_header = f"<b>📊 {title}</b>\n\n"
        if url:
            formatted_header += f"🔗 <a href='{url}'>Original Video</a>\n\n"

        summary_text = re.sub(r"^#\s*Summary\s*", "", summary_text, flags=re.IGNORECASE).strip()
        
        # Helper function logic inside to keep it self-contained
        def clean_md(text):
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
            text = re.sub(r"^#+\s*(.*)$", r"<b>\1</b>", text, flags=re.MULTILINE)
            text = re.sub(r"^[*-]\s+", r"• ", text, flags=re.MULTILINE)
            text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)
            return text.strip()

        summary_html = clean_md(summary_text)
        final_message = formatted_header + summary_html

        bot = Bot(token=token)
        if len(final_message) > 4090:
            final_message = final_message[:4090] + "..."

        await bot.send_message(
            chat_id=chat_id,
            text=final_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
        print("SUCCESS: Sent to Telegram.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python telegram_bot.py <path_to_summary_md> OR python telegram_bot.py --error <message>")
        sys.exit(1)
    
    if sys.argv[1] == "--error":
        if len(sys.argv) < 3:
            print("Error: No message provided for --error")
            sys.exit(1)
        asyncio.run(send_error_message(sys.argv[2]))
    else:
        asyncio.run(send_to_telegram(sys.argv[1]))
