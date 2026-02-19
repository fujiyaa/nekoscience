


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import try_send, safe_query_answer, safe_edit_query
from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....external.osu_api import get_user_scores_by_beatmap
from .send_best_scores import send_best_scores
from .....actions.context import set_message_context
import temp

from config import USER_SETTINGS_FILE



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["score_best", "map", "<map_id>", "<origin_user_id>"]
    action = parts[1]
    map_id = int(parts[2])
    origin_uid = int(parts[3])
    username_to_lookup = str(parts[4]) 
    
    if uid_click != origin_uid:
            await safe_query_answer(query, text="Не твои кнопки")
            return        
  
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return
    
    elif action == "ignore":
        await safe_query_answer(query, text="Это название карты, ее сложности это кнопки ниже...")
        return
    
    
    await safe_query_answer(query, show_alert=False)

    if action == "map":   
        try:                    
            await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")
             
            scores = await get_user_scores_by_beatmap(username_to_lookup, map_id, limit=1, fails=0)
            
            try:
                title = scores[0].get('map', {}).get('beatmap_full')
            except:
                title = map_id

            if not scores:
                await safe_edit_query(query,
                    text=f"`Нет скоров`  *{username_to_lookup}*  `на карте (``{title}``)`",
                    parse_mode="Markdown"
                )
                return
            
            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(update.effective_user.id), {}) 
            more = user_settings.get("display_more_scores", True) 

            limit = 1
            if more: limit = 10
                    
            bot_msg = await try_send(send_best_scores, query, scores, limit)        

            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False, 
                    map_id=map_id,
                    map_title=await get_beatmap_title_from_file(map_id),
                    mapper_username=await get_beatmap_creator_from_file(map_id),
                    origin_call_user_id=update.effective_user.id,
                )

        except Exception:
            traceback.print_exc() 
