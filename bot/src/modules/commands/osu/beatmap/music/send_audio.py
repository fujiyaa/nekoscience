


import os
import asyncio
import tempfile
import traceback
import json
import subprocess

from pathlib import Path

from telegram import InputFile, Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from telegram.error import TimedOut


async def safe_reply_audio(
    update,
    message,
    context,
    kwargs,
    retries: int = 3
):
    last_error = None

    send_methods = [
        lambda: message.reply_audio(
            **kwargs,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
            pool_timeout=30
        ),

        lambda: context.bot.send_audio(
            chat_id=update.effective_user.id,
            **kwargs,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
            pool_timeout=30
        )
    ]

    for attempt in range(1, retries + 1):
        print(f"[AUDIO SEND] attempt={attempt}")

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

                # пробуем следующий метод
                continue

    raise last_error


async def send_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    audio_file_path,
    title=None,
    artist=None,
    bg=None,
    beatmap_id=None,
    speed_1_5: bool = False,
    change_pitch: bool = False,
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

        MAX_DURATION = 30 * 60

        duration = get_audio_duration(str(path))

        if duration > MAX_DURATION:
            print(f"[REJECTED] Audio too long: {duration:.2f}s")
            return

        if path.suffix.lower() == ".ogg" or speed_1_5:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            )
            temp_file.close()

            command = [
                "ffmpeg",
                "-y",
                "-loglevel", "error",
                "-i", str(path),
            ]

            if speed_1_5: 
                if change_pitch:
                    command += [
                        "-filter:a",
                        "asetrate=44100*1.5,aresample=44100"
                    ]
                else:
                    command += [
                        "-filter:a",
                        "rubberband=tempo=1.5"
                    ]

            command += [
                "-vn",
                "-c:a", "libmp3lame",
                "-q:a", "0",
                temp_file.name
            ]

            command += ["-t", str(MAX_DURATION)]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                _, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("FFmpeg timed out")
            
            if process.returncode != 0:
                raise RuntimeError(stderr.decode())

            send_path = Path(temp_file.name)

        size_mb = os.path.getsize(send_path) / (1024 * 1024)

        print(
            f"[UPLOAD] "
            f"path={send_path} "
            f"size={size_mb:.2f}MB"
        )

        username = update.effective_user.username or "unknown"
        username = escape_markdown(username, version=2)

        caption = f"@{username}"

        if speed_1_5:
           caption += (" \+NC" if change_pitch else " \+DT")

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
                    update,
                    update.message,
                    context,
                    kwargs
                )
            else:
                result = await safe_reply_audio(
                    update,
                    update.callback_query.message,
                    context,
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

def get_audio_duration(path: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    return float(data["format"]["duration"])