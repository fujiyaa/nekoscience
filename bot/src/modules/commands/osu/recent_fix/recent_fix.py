


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message, try_send
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_osu_token, get_user_scores
from .send_score_fix import send_score_fix

from .....config import COOLDOWN_RECENT_FIX_COMMAND



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
        scores = await get_user_scores(username, token, limit=1)

        if not scores:
            await safe_send_message(update, text="❌ Нет последних игр", parse_mode="Markdown")
            await loading_msg.delete()
            return

        score = scores[0]
        
        msg = await try_send(send_score_fix, update, score, uid, token)
        await loading_msg.delete()

    except Exception:
        traceback.print_exc()
