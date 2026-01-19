


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message, try_send
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_user_scores_by_beatmap
from .send_best_scores import send_best_scores
from ....actions.context import get_cached_map, set_cached_map
import temp

from config import COOLDOWN_RECENT_FIX_COMMAND, USER_SETTINGS_FILE



async def start_scores_best(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(scores_best(update, context, user_request))
    
async def scores_best(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="scores_best",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_RECENT_FIX_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RECENT_FIX_COMMAND} секунд"
        )
    if not can_run:
        return

    try:
        uid = update.effective_user.id
        saved_name = await check_osu_verified(str(uid))

        if context.args:
            username = " ".join(context.args)
        elif saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/scores Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
     
        text = "`загрузка...`"
        
        loading_msg = await try_send(update.message.reply_text, text, parse_mode="Markdown")
        
        cached_map = get_cached_map(update)
        if cached_map:
            cached_map_id = cached_map["map_id"]
            # cached_user_id = cached_map["user_id"]
        if not cached_map:
            await safe_send_message(update, text="❌ Нет карты в чате... `/help scores`", parse_mode="Markdown")
            await loading_msg.delete()
            return

        scores = await get_user_scores_by_beatmap(username, cached_map_id, limit=1, fails=0)

        if not scores:
            await safe_send_message(update, text="❌ Нет скоров на карте... `/help scores`", parse_mode="Markdown")
            await loading_msg.delete()
            return
        
        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(update.effective_user.id), {}) 
        more = user_settings.get("display_more_scores", 1) 

        limit = 1
        if more: limit = 5
                
        bot_msg = await try_send(send_best_scores, update, scores, limit)        

        if bot_msg:
            bot_msg_id = bot_msg.message_id
            user_to_cache = update.effective_user.id
            map_to_cache = cached_map_id
            
            set_cached_map(bot_msg, map_to_cache, user_to_cache, bot_msg_id)

        await loading_msg.delete()

    except Exception:
        traceback.print_exc() 
