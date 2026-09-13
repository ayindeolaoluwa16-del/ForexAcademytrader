import os
import logging
import random
import string
import hashlib
import base64
import urllib.parse
import uuid
import re
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TOOLS = {
    "case": "🔠 Text Case Converter",
    "count": "🔢 Word & Character Counter",
    "password": "🔐 Password Generator",
    "uuid": "🆔 UUID Generator",
    "lorem": "📄 Lorem Ipsum Generator",
    "b64": "🧬 Base64 Encode/Decode",
    "url": "🔗 URL Encode/Decode",
    "hash": "🔒 Hash Generator",
    "reverse": "↩️ Text Reverser",
    "binary": "💻 Text ↔ Binary",
    "bmi": "⚖️ BMI Calculator",
    "age": "🎂 Age Calculator",
    "percent": "📊 Percentage Calculator",
    "random_num": "🎲 Random Number",
    "slug": "🐌 Slug Generator",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for key, label in TOOLS.items():
        row.append(InlineKeyboardButton(label, callback_data=f"tool:{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    text = (
        "👋 *Welcome to EducToolBot!*\n\n"
        "I'm a free educational toolbox with *15+ utilities*.\n"
        "No sign-up, no API keys, no data stored.\n\n"
        "👇 *Pick a tool below:*"
    )
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use EducToolBot*\n\n"
        "1. Send /start to see all tools.\n"
        "2. Tap a tool button.\n"
        "3. Send your input as a normal message.\n"
        "4. Get instant results.\n\n"
        "Use /cancel to exit any tool.",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Cancelled. Send /start to pick another tool.")


async def tool_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_menu":
        context.user_data.clear()
        keyboard = []
        row = []
        for key, label in TOOLS.items():
            row.append(InlineKeyboardButton(label, callback_data=f"tool:{key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        await query.edit_message_text(
            "👇 *Pick a tool:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    tool_key = data.split(":", 1)[1]
    context.user_data["tool"] = tool_key

    prompts = {
        "case": "Send me any text. I'll show UPPER, lower, Title, and Sentence case.",
        "count": "Send me any text. I'll count words, characters, and lines.",
        "password": "Send a number (length, e.g. `16`).",
        "uuid": "Send any message (or just 'go') to generate a UUID v4.",
        "lorem": "Send a number of paragraphs (e.g. `2`).",
        "b64": "Send text to encode, or `decode:` + text to decode.",
        "url": "Send text to URL-encode, or `decode:` + text to decode.",
        "hash": "Send text. I'll return MD5, SHA1, and SHA256.",
        "reverse": "Send text. I'll reverse it.",
        "binary": "Send text to encode, or `decode:` + binary to decode.",
        "bmi": "Send weight and height like `70 1.75`.",
        "age": "Send your birth date as `YYYY-MM-DD`.",
        "percent": "Send `X Y` for X% of Y (e.g. `15 200`).",
        "random_num": "Send `min max` (e.g. `1 100`).",
        "slug": "Send text. I'll make a URL-friendly slug.",
    }

    back_kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_menu")]]
    )
    await query.edit_message_text(
        f"*{TOOLS[tool_key]}*\n\n{prompts.get(tool_key, 'Send your input.')}",
        reply_markup=back_kb,
        parse_mode="Markdown",
    )


def run_tool(tool: str, text: str) -> str:
    text = text.strip()

    if tool == "case":
        return (
            f"*UPPER:* `{text.upper()}`\n"
            f"*lower:* `{text.lower()}`\n"
            f"*Title:* `{text.title()}`\n"
            f"*Sentence:* `{text.capitalize()}`"
        )

    if tool == "count":
        words = len(text.split())
        chars = len(text)
        chars_no_space = len(text.replace(" ", ""))
        lines = len(text.splitlines())
        return (
            f"📊 *Results:*\n"
            f"Words: `{words}`\n"
            f"Characters (with spaces): `{chars}`\n"
            f"Characters (no spaces): `{chars_no_space}`\n"
            f"Lines: `{lines}`"
        )

    if tool == "password":
        try:
            length = int(text)
            if length < 4 or length > 128:
                return "⚠️ Send a number between 4 and 128."
        except ValueError:
            return "⚠️ Send a valid number (e.g. `16`)."
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        pwd = "".join(random.SystemRandom().choice(chars) for _ in range(length))
        return f"🔐 *Your password:*\n`{pwd}`"

    if tool == "uuid":
        return f"🆔 `{uuid.uuid4()}`"

    if tool == "lorem":
        try:
            n = int(text)
            n = max(1, min(n, 10))
        except ValueError:
            n = 1
        base = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris."
        )
        return "\n\n".join([base for _ in range(n)])

    if tool == "b64":
        if text.lower().startswith("decode:"):
            try:
                decoded = base64.b64decode(text[7:].strip()).decode("utf-8", errors="replace")
                return f"✅ *Decoded:*\n`{decoded}`"
            except Exception as e:
                return f"⚠️ Decode error: {e}"
        encoded = base64.b64encode(text.encode()).decode()
        return f"✅ *Encoded:*\n`{encoded}`"

    if tool == "url":
        if text.lower().startswith("decode:"):
            return f"✅ *Decoded:*\n`{urllib.parse.unquote(text[7:].strip())}`"
        return f"✅ *Encoded:*\n`{urllib.parse.quote(text)}`"

    if tool == "hash":
        return (
            f"*MD5:* `{hashlib.md5(text.encode()).hexdigest()}`\n"
            f"*SHA1:* `{hashlib.sha1(text.encode()).hexdigest()}`\n"
            f"*SHA256:* `{hashlib.sha256(text.encode()).hexdigest()}`"
        )

    if tool == "reverse":
        return f"↩️ `{text[::-1]}`"

    if tool == "binary":
        if text.lower().startswith("decode:"):
            try:
                bits = text[7:].strip().replace(" ", "")
                chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
                return f"✅ *Decoded:*\n`{''.join(chars)}`"
            except Exception as e:
                return f"⚠️ Error: {e}"
        return f"✅ *Binary:*\n`{' '.join(format(ord(c), '08b') for c in text)}`"

    if tool == "bmi":
        try:
            parts = text.split()
            w, h = float(parts[0]), float(parts[1])
            bmi = w / (h * h)
            if bmi < 18.5:
                cat = "Underweight"
            elif bmi < 25:
                cat = "Normal"
            elif bmi < 30:
                cat = "Overweight"
            else:
                cat = "Obese"
            return f"⚖️ *BMI:* `{bmi:.2f}`\n*Category:* {cat}"
        except Exception:
            return "⚠️ Send like `70 1.75` (kg then meters)."

    if tool == "age":
        try:
            bd = datetime.strptime(text, "%Y-%m-%d")
            today = datetime.today()
            years = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            days = (today - bd).days
            return f"🎂 *Age:* `{years}` years\n*Total days:* `{days}`"
        except Exception:
            return "⚠️ Send date as `YYYY-MM-DD`."

    if tool == "percent":
        try:
            x, y = map(float, text.split())
            return f"📊 `{x}%` of `{y}` = `{x * y / 100}`"
        except Exception:
            return "⚠️ Send like `15 200`."

    if tool == "random_num":
        try:
            a, b = map(int, text.split())
            return f"🎲 `{random.randint(min(a,b), max(a,b))}`"
        except Exception:
            return "⚠️ Send like `1 100`."

    if tool == "slug":
        s = text.lower()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"\s+", "-", s).strip("-")
        return f"🐌 `{s}`"

    return "Unknown tool."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tool = context.user_data.get("tool")
    if not tool:
        await update.message.reply_text("Please send /start to pick a tool first.")
        return

    try:
        result = run_tool(tool, update.message.text)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Tool error")
        await update.message.reply_text(f"⚠️ Something went wrong: {e}")


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN env variable is missing.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(tool_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 EducToolBot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
