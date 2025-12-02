"""Telegram bot that re-tags incoming media to look like Ray-Ban Meta captures."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from telegram import Update
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater

try:  # Support running as ``python bot/main.py`` without package context.
    from .tagger import ExiftoolError, tag_as_rayban
except ImportError:  # pragma: no cover - fallback for direct script execution
    from tagger import ExiftoolError, tag_as_rayban

from dotenv import load_dotenv

EXIFTOOL_PATH = "exiftool"


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("rayban_bot")
MEDIA_FILTER = Filters.document | Filters.photo | Filters.video | Filters.video_note


def _download_media(update: Update) -> Path | None:
    message = update.effective_message
    if not message:
        return None

    file_obj = None
    if message.document:
        file_obj = message.document.get_file()
    elif message.video:
        file_obj = message.video.get_file()
    elif message.video_note:
        file_obj = message.video_note.get_file()
    elif message.photo:
        file_obj = message.photo[-1].get_file()

    if not file_obj:
        return None

    with NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)

    file_obj.download(custom_path=str(tmp_path))
    return tmp_path


def _handle_media(update: Update, context: CallbackContext) -> None:
    if not update.message:
        return

    LOGGER.info("Processing media from chat %s", update.effective_chat and update.effective_chat.id)
    try:
        tmp_path = _download_media(update)
    except Exception as exc:
        if "File is too big" in str(exc):
            update.message.reply_text("File exceeds Telegram Bot API's 20 MB download limit. Please send a smaller file.")
            return
        raise
    if not tmp_path:
        update.message.reply_text("I can only process photos, videos, or documents.")
        return

    filename = update.message.document.file_name if update.message.document else None
    if not filename and update.message.photo:
        filename = "rayban-photo.jpg"
    if not filename and update.message.video:
        filename = "rayban-video.mp4"

    try:
        tag_as_rayban(tmp_path, exiftool_path=EXIFTOOL_PATH)
    except ExiftoolError as exc:
        LOGGER.exception("exiftool failed: %s", exc)
        update.message.reply_text(f"Failed to edit metadata: {exc}")
        if tmp_path.exists():
            tmp_path.unlink()
        return
    except FileNotFoundError:
        update.message.reply_text("Temporary download failed. Please try again.")
        if tmp_path.exists():
            tmp_path.unlink()
        return

    with tmp_path.open("rb") as file_handle:
        update.message.reply_document(document=file_handle, filename=filename, timeout=120)

    if tmp_path.exists():
        tmp_path.unlink()


def main() -> None:
    load_dotenv()
    global EXIFTOOL_PATH
    EXIFTOOL_PATH = os.environ.get("EXIFTOOL_PATH", "exiftool")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable before running the bot.")

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(MEDIA_FILTER, _handle_media))

    LOGGER.info("Bot is starting. Press Ctrl+C to stop.")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
