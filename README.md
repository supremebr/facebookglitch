# Telegram Ray-Ban Metadata Bot

Python bot that listens for incoming Telegram media, rewrites the EXIF metadata with Ray-Ban Meta Smart Glasses values via `exiftool`, and sends the updated file back to the sender.

## Prerequisites
- Python 3.11+ recommended (3.8+ required).
- [exiftool](https://exiftool.org/) available on PATH (`choco install exiftool` on Windows).
- A Telegram bot token from [@BotFather](https://t.me/botfather).

## Setup
```powershell
# (optional) create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Set the bot token in your environment:
```powershell
$env:TELEGRAM_BOT_TOKEN = "123456789:ABC..."
```

## Run
```powershell
python -m bot.main
```
The bot uses long polling. Stop with `Ctrl+C`.

## How it works
1. Downloads each incoming photo, video, or document message into a temporary file.
2. Runs `exiftool` via `bot/tagger.py` to stamp Ray-Ban metadata.
3. Removes any backup files left by `exiftool`.
4. Sends the modified media back as a document attachment.

## Notes
- `exiftool` supports common image/video formats, but not every file type exposes the same fields.
- Telegram enforces upload limits; the bot cannot bypass them.
- Files are deleted immediately after responding, but avoid sharing sensitive media with untrusted deployments.
