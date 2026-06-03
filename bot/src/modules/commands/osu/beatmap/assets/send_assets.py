import os
import asyncio
import tempfile
import traceback

from pathlib import Path

from pydub import AudioSegment

from telegram import InputFile, Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from telegram.error import TimedOut


async def safe_reply_assets(
    update,
    message,
    context,
    kwargs,
    retries: int = 3
):
    last_error = None

    send_methods = [
        lambda: message.reply_photo(
            **kwargs,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
            pool_timeout=30
        ),

        lambda: context.bot.send_photo(
            chat_id=update.effective_user.id,
            **kwargs,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
            pool_timeout=30
        )
    ]

    for attempt in range(1, retries + 1):
        print(f"[PHOTO SEND] attempt={attempt}")

        for method_index, method in enumerate(send_methods, start=1):
            try:
                print(f"[METHOD {method_index}] sending...")
                return await method()

            except TimedOut as e:
                last_error = e

                print(f"[TIMEOUT] attempt={attempt} method={method_index}")
                traceback.print_exc()

                await asyncio.sleep(2)

            except Exception as e:
                last_error = e

                print(f"[FAILED] attempt={attempt} method={method_index}")
                traceback.print_exc()

                continue

    raise last_error

async def send_assets(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    bg_file_path
):
    path = Path(bg_file_path)

    if not path.is_file():
        print(f"[ERROR] File not found: {bg_file_path}")
        return

    if os.path.getsize(bg_file_path) == 0:
        print(f"[ERROR] File is empty: {bg_file_path}")
        return

    try:
        size_mb = os.path.getsize(path) / (1024 * 1024)

        print(
            f"[UPLOAD] "
            f"path={path} "
            f"size={size_mb:.2f}MB"
        )

        username = (
            update.effective_user.username
            or "unknown"
        )

        username = escape_markdown(
            username,
            version=2
        )

        caption = f"@{username}"

        with open(path, "rb") as f:
            kwargs = {
                "photo": InputFile(
                    f,
                    filename=path.name
                ),
                "caption": caption,
                "parse_mode": "MarkdownV2",
            }

            if update.message is not None:
                result = await safe_reply_assets(
                    update,
                    update.message,
                    context,
                    kwargs
                )
            else:
                result = await safe_reply_assets(
                    update,
                    update.callback_query.message,
                    context,
                    kwargs
                )

            print("[SUCCESS] photo sent")
            return result

    except Exception as e:
        print(f"[ERROR] Failed to send photo: {e}")
        traceback.print_exc()