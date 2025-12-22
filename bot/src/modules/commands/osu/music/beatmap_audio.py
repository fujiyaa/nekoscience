


import re
import os
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import delete_user_message, delete_message_after_delay
from ....external.osu_http import download_osz_async
from .send_audio import send_audio
from .utils import beatmap_artists_and_audio_path

from .....config import COOLDOWN_MP3_COMMAND, OSU_SESSION, OSZ_DIR



async def start_beatmap_audio(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(beatmap_audio(update, context, user_request))
async def beatmap_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):
    url = update.message.text.strip()
    match = re.search(r"beatmapsets/(\d+)", url)

    if user_request:
        if not match:        
            msg = await update.message.reply_text(
                "❌ Нужна ссылка на карту"
            )
            asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
            asyncio.create_task(delete_user_message(update, context, delay=4))
            return
    
    try:
        if match is None: return
        beatmap_id = match.group(1)
    except Exception as e:
        print(e)
        return

    if user_request: warn_text = f"⏳ Подождите {COOLDOWN_MP3_COMMAND} секунд"
    else: warn_text = None
    can_run = await check_user_cooldown(
        command_name="render_score",
        user_id=str(update.effective_user.id),
        cooldown_seconds=COOLDOWN_MP3_COMMAND,           
        update=update,
        context=context,
        warn_text=warn_text
    )
    if not can_run:
        return

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                status_msg = await update.message.reply_text("Загрузка...")
                break
            except Exception as e: print(e)
    
    for _ in range(max_attempts):
        try: 
            await download_osz_async(beatmap_id, OSU_SESSION, OSZ_DIR)

            break
        except Exception as e: print(e)   

    path = os.path.join(OSZ_DIR, beatmap_id)

    title, artist, path, bg_path = await beatmap_artists_and_audio_path(path)

    path = os.path.join(OSZ_DIR, beatmap_id, path)
    bg_path = os.path.join(OSZ_DIR, beatmap_id, bg_path)

    await send_audio(update, context, path, title, artist, bg_path)
    if user_request:
        asyncio.create_task(delete_message_after_delay(context, status_msg.chat_id, status_msg.message_id, 1)) 

