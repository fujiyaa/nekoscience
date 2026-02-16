


import traceback
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .....wrappers.osu_profile import get_profile_text
from .....actions.messages import safe_query_answer, safe_edit_query
from .....actions.context import set_message_context
# import temp

# from config import USER_SETTINGS_FILE



async def callback(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        uid_click = query.from_user.id
        
        parts = query.data.split(":")
        # ["profile_context", "username|cancel", "<username>", "<origin_user_id>"]
        action = parts[1]
        username = str(parts[2])
        origin_uid = int(parts[3])
        
        if uid_click != origin_uid:
                await safe_query_answer(query, text="Не твои кнопки")
                return
            
        await safe_query_answer(query, show_alert=False)
    
        if action == "cancel":
            await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
            return

        if action == "username":                 
            await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")             
        
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await safe_edit_query(
                    query,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            text = get_profile_text(user_data, best_pp)

            if text is None:
                await safe_edit_query(
                    query,
                    text="`Нет данных`",
                    parse_mode="Markdown"
                )
                return                
        
            bot_msg = await safe_edit_query(
                query,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False,
                    profile_player_username=username,
                    origin_call_user_id=update.effective_user.id,
                )

            return      

    except Exception:
        traceback.print_exc() 
