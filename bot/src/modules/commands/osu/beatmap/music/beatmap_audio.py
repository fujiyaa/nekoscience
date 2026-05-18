


import os
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....systems.logging import log_all_update
from .....systems.cooldowns import check_user_cooldown
from .....actions.messages import delete_user_message, delete_message_after_delay
from .....external.osu_and_meatconnect import download_osz_async
from .....actions.context import set_message_context
from .send_audio import send_audio
from .utils import beatmap_artists_and_audio_path
from .....systems.logging import log_all_update
from .context.buttons import get_context_keyboard
from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....actions.messages import delete_user_message, delete_message_after_delay, safe_send_message
from .....actions.context import set_message_context, get_message_context

from config import COOLDOWN_MP3_COMMAND, OSU_SESSION, OSZ_DIR
from config import OSU_MAPSET_REGEX



async def start_beatmap_audio(update, context):
    await log_all_update(update)
    asyncio.create_task(beatmap_audio(update, context))
async def beatmap_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    can_run = await check_user_cooldown(
        command_name="music",
        user_id=str(update.effective_user.id),
        cooldown_seconds=COOLDOWN_MP3_COMMAND,           
        update=update,
        context=context
    )
    if not can_run:
        return
    
    try:
    
        message_text = update.message.text.strip()
        match = OSU_MAPSET_REGEX.search(message_text)
    
        if not match:
            message_context = get_message_context(update, reply=False)          
            message_context_reply = get_message_context(update, reply=True)      
            if message_context:
                m1 = m2 = None

                m1 = message_context["metadata"].get("map_id")
                if message_context_reply:
                    m2 = message_context_reply["metadata"].get("map_id")
        
                if (m1 is not None) or (m2 is not None):
                    message_context_reply = get_message_context(update, reply=True)
                                
                    await safe_send_message(
                        update, 
                        text=f"<code>Выбери карту...\n(или /music +ссылка)</code>", 
                        reply_markup=get_context_keyboard(
                            message_context,
                            message_context_reply,
                            update.effective_user.id,
                        ),
                        parse_mode="HTML"
                    )
                    return

            msg = await update.message.reply_text(
                "❌ Нужна ссылка на карту"
            )
            asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
            asyncio.create_task(delete_user_message(update, context, delay=4))
            return
        else:
            beatmap_id = match.group(1) if match.group(1) else match.group(2)

        max_attempts = 1
        for _ in range(max_attempts):
            try:
                status_msg = await update.message.reply_text("Загрузка...")
                break
            except Exception as e: print(e)
        
        result = None

        for _ in range(max_attempts):
            try:
                result = await download_osz_async(
                    beatmap_id,
                    OSU_SESSION,
                    OSZ_DIR
                )
                break
            except Exception as e:
                print(e)

        if not result:
            raise RuntimeError("Failed to download beatmap")
        
        mapset_id = str(result["mapset_id"])
        base_path = result["path"]

        title, artist, audio_name, bg_path = await beatmap_artists_and_audio_path(base_path)

        audio_file_path = os.path.join(base_path, audio_name)

        bot_msg = await send_audio(update, context, audio_file_path, title, artist, bg_path, beatmap_id)

        map_id=int(beatmap_id)

        if bot_msg:
            set_message_context(
                bot_msg, 
                reply=False, 
                mapset_id=map_id,
                map_title=await get_beatmap_title_from_file(map_id),
                mapper_username=await get_beatmap_creator_from_file(map_id),
                origin_call_user_id=update.effective_user.id,
            )

    except  Exception as e:
        print(e)

    try:
        asyncio.create_task(delete_message_after_delay(context, status_msg.chat_id, status_msg.message_id, 1)) 
    except:
        pass