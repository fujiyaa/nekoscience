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


async def safe_reply_audio(
    message,
    kwargs,
    retries: int = 3
):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"[AUDIO SEND] attempt={attempt}")

            return await message.reply_audio(
                **kwargs,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30
            )

        except TimedOut as e:
            last_error = e

            print(f"[TIMEOUT] attempt={attempt}")
            traceback.print_exc()

            await asyncio.sleep(2)

        except Exception:
            traceback.print_exc()
            raise

    raise last_error


async def send_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    audio_file_path,
    title=None,
    artist=None,
    bg=None,
    beatmap_id=None
):
    path = Path(audio_file_path)

    # file exists
    if not path.is_file():
        print(f"[ERROR] File not found: {audio_file_path}")
        return

    # file not empty
    if os.path.getsize(audio_file_path) == 0:
        print(f"[ERROR] File is empty: {audio_file_path}")
        return

    temp_file = None

    try:
        send_path = path

        # convert ogg -> mp3
        if path.suffix.lower() == ".ogg":
            print("[CONVERT] ogg -> mp3")

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            )

            temp_file.close()

            audio = AudioSegment.from_file(
                audio_file_path,
                format="ogg"
            )

            audio.export(
                temp_file.name,
                format="mp3"
            )

            send_path = Path(temp_file.name)

        # size info
        size_mb = os.path.getsize(send_path) / (1024 * 1024)

        print(
            f"[UPLOAD] "
            f"path={send_path} "
            f"size={size_mb:.2f}MB"
        )

        # telegram username
        username = (
            update.effective_user.username
            or "unknown"
        )

        username = escape_markdown(
            username,
            version=2
        )

        caption = f"@{username}"

        with open(send_path, "rb") as f:
            kwargs = {
                "audio": InputFile(
                    f,
                    filename=send_path.name
                ),
                "caption": caption,
                "title": title or "",
                "parse_mode": "MarkdownV2",
            }

            if artist:
                kwargs["performer"] = artist

            if update.message is not None:
                result = await safe_reply_audio(
                    update.message,
                    kwargs
                )
            else:
                result = await safe_reply_audio(
                    update.callback_query.message,
                    kwargs
                )

            print("[SUCCESS] audio sent")

            return result

    except Exception as e:
        print(f"[ERROR] Failed to send audio: {e}")
        traceback.print_exc()

    finally:
        if temp_file:
            try:
                os.remove(temp_file.name)

                print(
                    f"[CLEANUP] removed temp file: "
                    f"{temp_file.name}"
                )

            except OSError:
                traceback.print_exc()