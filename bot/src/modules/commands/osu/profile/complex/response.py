


import asyncio
import traceback
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes

from .....actions.context import set_message_context
from .....actions.rich import edit_rich_query, edit_rich_message
from .....external.osu_api import get_user_profile, get_top_100_scores
from .....actions.messages import safe_edit_query
from .....wrappers.osu_profile import get_profile_text
from .....wrappers.mods_top import get_mods_top
from .....wrappers.mappers import get_mappers_text
from .....wrappers.anime import get_anime_text
from .....wrappers.aimslop import get_aimslop_text
from .....wrappers.speedslop import get_speedslop_text
from .....wrappers.nish import get_nish_text
from ....service.settings.service import neko_settings
from ..average.average import average
import temp



async def get_text_by_action(
    update: Update, 
    action,
    username,
    user_id
):  
    language = neko_settings.get(user_id, "lang")

    if action == 'average':
        return await average(update, username, language), None
        
    elif action == 'minmax':
        return await average(update, username, language, True), None

    elif action == 'ppfire':
        return await average(update, username, language, "ppfire"), None
    
    
    user_data, best_pp = await get_data(username)

    if action == 'profile':
        return get_profile_text(user_data), "HTML"

    elif action == 'mods':            
        return get_mods_top(user_data, best_pp), "HTML"

    elif action == 'mappers':
        return get_mappers_text(user_data, best_pp), "HTML"

    elif action == 'anime':
        return get_anime_text(user_data, best_pp), "HTML"
    
    elif action == 'aimslop':
        return get_aimslop_text(user_data, best_pp), "HTML"
    
    elif action == 'speedslop':
        return get_speedslop_text(user_data, best_pp), "HTML"
    
    elif action == 'nish':
        return get_nish_text(user_data, best_pp), "HTML"

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
        text, parse_mode = await get_text_by_action(update, action, username, update.message.from_user.id)

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
    
        # bot_msg = await context.bot.edit_message_text(
        #     chat_id=update.effective_chat.id,
        #     message_id=temp_id,
        #     text=text,
        #     parse_mode=parse_mode,
        #     disable_web_page_preview=True
        # )

        bot_msg = await edit_rich_message(
            update,
            message_id=temp_id,
            markdown=text
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
    query: CallbackQuery,
    action,
    username
):       
    text, parse_mode = await get_text_by_action(update, action, username, query.from_user.id)
    
    if parse_mode is None:
        return # bypass
   
    if text is None:
        await safe_edit_query(
            query,
            text="`Нет данных`",
            parse_mode="Markdown"
        )
        return
    
    bot_msg = await edit_rich_query(
        query,
        markdown=text
    )

    # bot_msg = await safe_edit_query(
    #     query,
    #     text=text,
    #     parse_mode=parse_mode,
    #     disable_web_page_preview=True,
    # )

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
