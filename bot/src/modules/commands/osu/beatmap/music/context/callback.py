


import os
import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from ......actions.messages import safe_edit_query, safe_query_answer
from ......actions.context import set_message_context
from ......actions.messages import delete_message_after_delay
from ......external.osu_and_meatconnect import download_osz_async
from ..send_audio import send_audio
from ..utils import beatmap_artists_and_audio_path

from config import OSU_SESSION, OSZ_DIR



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["simulate_context", "map", "<map_id>", "<origin_user_id>"]
    action = parts[1]
    beatmap_id = str(parts[2])
    origin_uid = int(parts[3])
    
    if uid_click != origin_uid:
            await safe_query_answer(query, text="Не твои кнопки")
            return
        
    await safe_query_answer(query, show_alert=False)
  
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return

    if action == "map":   
        try:                    
            status_msg = await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")
                    
            max_attempts = 1
            
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
                    map_id=map_id,
                    map_title=await get_beatmap_title_from_file(map_id),
                    mapper_username=await get_beatmap_creator_from_file(map_id),
                    origin_call_user_id=update.effective_user.id,
                )

        except  Exception as e:
            print(e)

        try:
            asyncio.create_task(delete_message_after_delay(context, status_msg.chat_id, status_msg.message_id, 1)) 
        


        except Exception:
            traceback.print_exc() 
