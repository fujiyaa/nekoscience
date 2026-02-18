


import traceback
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .....wrappers.osu_profile import get_profile_text
from .....actions.messages import safe_query_answer, safe_edit_query
from .....actions.context import set_message_context
from .response import send_query
# import temp

# from config import USER_SETTINGS_FILE



async def callback(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        uid_click = query.from_user.id
        
        parts = query.data.split(":")
        # ["ctx1", "profile|compare|mods|mappers|anime", "u|c", "<username>", "<origin_user_id>"]
        action = parts[1]
        proceed_or_cancel = parts[2]
        username = str(parts[3])
        origin_uid = int(parts[4])
        
        if uid_click != origin_uid:
                await safe_query_answer(query, text="Не твои кнопки")
                return
            
        await safe_query_answer(query, show_alert=False)
    
        if proceed_or_cancel == "c":
            await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
            return

        if proceed_or_cancel == "u":                 
            await safe_edit_query(query, text="`Загрузка!!!...`", parse_mode="Markdown")             
        
        await send_query(
            update, 
            query,
            action,
            username
        )    

    except Exception:
        traceback.print_exc() 
