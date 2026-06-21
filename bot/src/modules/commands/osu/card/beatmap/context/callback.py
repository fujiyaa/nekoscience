


import asyncio
import traceback, html
from telegram.ext import ContextTypes
from telegram import Update, InputFile

from ......actions.public_buttons import get_keyboard as get_pkb
from ......actions.messages import safe_edit_query, safe_query_answer
from ......actions.rich import edit_rich_query
from ......actions.context import set_message_context
from ......external.osu_http import fetch_txt_beatmaps
from ......external.osu_api import get_osu_token, get_beatmap
from ......actions.context import set_message_context
from .....service.settings.service import neko_settings
from ..processing_v1 import create_beatmap_image
from ..utils import delayed_remove




async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["cbcxt", "map", "<map_id>", "<origin_user_id>", "<origin_msg_id>"]
    action = parts[1]
    map_id = int(parts[2])
    origin_uid = int(parts[3])
    origin_msg_id = int(parts[4])
    
    if uid_click != origin_uid:
            await safe_query_answer(query, text="Не твои кнопки")
            return
          
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return
    
    elif action == "ignore":
        await safe_query_answer(query, text="Это название карты, ее сложности это кнопки ниже...", show_alert=True)
        return
        
    await safe_query_answer(query, show_alert=False)

    if action == "map":   
        try:                    
            await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")

            maps_ids = []
            maps_ids.append(map_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(map_id, token)

            user_id = str(update.effective_user.id)

            map_data["lang"] = neko_settings.get(user_id, "lang")

            img_path = await create_beatmap_image(map_data, map_id)        

            mapset = map_data.get('beatmapset', {})

            artist = mapset.get('artist', 'artist')
            title = mapset.get('title', 'title')

            full_title = f"{artist} - {title}"
            beatmap_escaped = html.escape(full_title)            
            preview_url = mapset.get("preview_url")

            if preview_url is None:
                preview_url = ""
            else:
                preview_url = f'<details><summary><code>Превью для: </code> {beatmap_escaped}</summary><audio src="{preview_url}"></audio>\n</details>'            
     

            with open(img_path, "rb") as f:
                try:
                    reply_markup = get_pkb(beatmap_id=str(map_id))
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
                try:                   
                    await edit_rich_query(
                        query,
                        markdown=preview_url
                    )
                    audio_sent = True
                except:
                    await query.delete_message()  

                set_message_context(
                    bot_msg, 
                    reply=False, 
                    map_id=map_id,
                    map_title=map_data['beatmapset']['title'], 
                    mapper_username=map_data['owners'][0]['username'],
                    origin_call_user_id=update.effective_user.id,
                )            
                        
            asyncio.create_task(delayed_remove(img_path))

        except Exception:
            traceback.print_exc() 
