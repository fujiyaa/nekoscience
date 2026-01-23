


import os
import tempfile

from pathlib import Path
from pydub import AudioSegment
from telegram.helpers import escape_markdown

from ....external.osu_http import download_osz_async
from .utils import beatmap_artists_and_audio_path

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from config import OSU_SESSION, OSZ_DIR



async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, audio_file_path, title=None, artist=None, bg=None, beatmap_id=None):
    path = Path(audio_file_path)
    if not path.is_file():
        print("Файл не найден:", audio_file_path)
        max_attempts = 3        
        
        for _ in range(max_attempts):
            try: 
                await download_osz_async(beatmap_id, OSU_SESSION, OSZ_DIR)

                path = os.path.join(OSZ_DIR, beatmap_id)

                title, artist, path, bg_path = await beatmap_artists_and_audio_path(path)

                path = os.path.join(OSZ_DIR, beatmap_id, path)
                bg_path = os.path.join(OSZ_DIR, beatmap_id, bg_path)

                break

            except Exception as e: print(e)   

        return
    if os.path.getsize(audio_file_path) == 0:
        print("Файл пустой:", audio_file_path)
        return

    temp_file = None
    try:
        if path.suffix.lower() == ".ogg":
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()
            audio = AudioSegment.from_file(audio_file_path, format="ogg")
            audio.export(temp_file.name, format="mp3")
            send_path = Path(temp_file.name)
        else:
            send_path = path

        username = escape_markdown(update.effective_user.username, version=2)
        link = "https://t.me/fujiyaosubot"
        caption = f"@{username} 💃 [ᴅᴀʀᴋɴᴇss]({link})"

        with open(send_path, "rb") as f:
            kwargs = {
                "audio": InputFile(f, filename=send_path.name),
                "caption": caption,
                "title": title or "",
                "parse_mode": "MarkdownV2",
            }
            if artist:
                kwargs["performer"] = artist

            return await update.message.reply_audio(**kwargs)

    except Exception as e:
        print("Ошибка при отправке аудио:", e)
    finally:
        if temp_file:
            try:
                os.remove(temp_file.name)
            except OSError:
                pass
