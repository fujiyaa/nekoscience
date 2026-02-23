


import asyncio
import traceback
from telegram.ext import ContextTypes
from telegram import Update, InputFile

from ......actions.messages import safe_edit_query, safe_query_answer
from ......actions.context import set_message_context
from ......external.osu_http import fetch_txt_beatmaps
from ......external.osu_api import get_osu_token, get_beatmap
from ......actions.context import set_message_context
from ..buttons import get_keyboard
from ..processing_v1 import create_beatmap_image
from ..utils import delayed_remove
import temp

from config import USER_SETTINGS_FILE



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["card_beatmap_context", "map", "<map_id>", "<origin_user_id>", "<origin_msg_id>"]
    action = parts[1]
    map_id = int(parts[2])
    origin_uid = int(parts[3])
    origin_msg_id = int(parts[4])
    
    if uid_click != origin_uid:
            await safe_query_answer(query, text="Не твои кнопки")
            return
        
    await safe_query_answer(query, show_alert=False)
  
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return

    if action == "map":   
        try:                    
            await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")

            maps_ids = []
            maps_ids.append(map_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(map_id, token)

            user_id = str(update.effective_user.id)

            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(user_id), {}) 
            _new_card = user_settings.get("new_card", True)
            map_data["lang"] = user_settings.get("lang", "ru") 

            img_path = await create_beatmap_image(map_data, map_id)             

            with open(img_path, "rb") as f:
                try:
                    reply_markup = await get_keyboard(str(map_id))
                    bot_msg = await context.bot.send_photo(
                        query.message.chat.id,
                        message_thread_id=query.message.message_thread_id,
                        photo=InputFile(f), reply_markup = reply_markup,
                    )                    

                except:
                    bot_msg = await context.bot.send_photo(
                        query.message.chat.id,
                        photo=InputFile(f), reply_markup = reply_markup,
                    )
                    
            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False, 
                    map_id=map_id,
                    map_title=map_data['beatmapset']['title'], 
                    mapper_username=map_data['owners'][0]['username'],
                    origin_call_user_id=update.effective_user.id,
                )
            
            await query.delete_message()              
            asyncio.create_task(delayed_remove(img_path))

        except Exception:
            traceback.print_exc() 
