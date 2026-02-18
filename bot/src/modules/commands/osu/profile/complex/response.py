


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from .....actions.context import set_message_context
from .....external.osu_api import get_user_profile, get_top_100_scores
from .....actions.messages import safe_edit_query
from .....wrappers.osu_profile import get_profile_text
from .....wrappers.mods_top import get_mods_top
from .....wrappers.mappers import get_mappers_text
from .....wrappers.anime import get_anime_text
from ..average.average import average
import temp

from config import USER_SETTINGS_FILE



async def get_text_by_action(
    update: Update, 
    action,
    username    
):  
    language = await init_language(str(update.effective_user.id))    

    if action == 'average':
        return await average(update, username, language), None # bypass
    
    
    user_data, best_pp = await get_data(username)

    if action == 'profile':
        return get_profile_text(user_data), "HTML"

    elif action == 'mods':            
        return get_mods_top(user_data, best_pp), "HTML"

    elif action == 'mappers':
        return get_mappers_text(user_data, best_pp), "HTML"

    elif action == 'anime':
        return get_anime_text(user_data, best_pp), "HTML"


    else:
        raise ValueError(f'unspecified action: {action}')

async def send_message(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    action,
    username,
    temp_id
):
    try:
        text, parse_mode = await get_text_by_action(update, action, username)

        if parse_mode is None:
            return # bypass

        if text is None:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=temp_id,
                text="`Нет данных`",
                parse_mode="Markdown"
            )
            return
    
        bot_msg = await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=temp_id,
            text=text,
            parse_mode=parse_mode
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
        # ошибку в ответ бота?

async def send_query(
    update: Update, 
    query,
    action,
    username
):       
    text, parse_mode = await get_text_by_action(update, action, username)
    
    if parse_mode is None:
        return # bypass
   
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
        parse_mode=parse_mode,
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

async def get_data(username: str):    
    
    user_data = await asyncio.wait_for(
        get_user_profile(username), timeout=10
    )

    try:
        user_id = user_data["id"]
        best_pp = await asyncio.wait_for(
            get_top_100_scores(username, user_id=user_id), timeout=10
        )
    
    # потому что не везде нужны best pp
    except Exception:
        best_pp = None

    return user_data, best_pp

async def init_language(telegram_username_str: str):
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(telegram_username_str, {})
    lang = user_settings.get("lang", "ru")

    return lang