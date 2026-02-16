


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....actions.messages import safe_send_message, try_send
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....external.osu_api import get_osu_token, get_user_scores
from .....actions.context import set_message_context
from .send_score_fix import send_score_fix

from config import COOLDOWN_RECENT_FIX_COMMAND



async def start_recent_fix(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(recent_fix(update, context, user_request))
    
async def recent_fix(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="recent_fix",
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
                "Использование: `/fix Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
     
        text = "`загрузка...`"
        
        loading_msg = await try_send(update.message.reply_text, text, parse_mode="Markdown")

        token = await get_osu_token()
        scores = await get_user_scores(username, limit=1, fails=0)

        if not scores:
            await safe_send_message(update, text="❌ Нет последних игр", parse_mode="Markdown")
            await loading_msg.delete()
            return

        cached_entry = scores[0]
        
        bot_msg = await try_send(send_score_fix, update, cached_entry, uid, token)       

        map_id=cached_entry.get('map').get('beatmap_id')
        if bot_msg:
            set_message_context(
                bot_msg, 
                reply=False, 
                map_id=map_id,
                map_title=await get_beatmap_title_from_file(map_id),
                mapper_username=await get_beatmap_creator_from_file(map_id),
                origin_call_user_id=update.effective_user.id,
            )


        await loading_msg.delete()

    except Exception:
        traceback.print_exc() 
