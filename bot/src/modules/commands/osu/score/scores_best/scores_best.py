


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message, try_send
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....actions.context import get_message_context
from .buttons import get_keyboard

from config import COOLDOWN_RECENT_FIX_COMMAND



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
                "Использование без авторизации: `/scores Fujiya` <- ник\n"
                "\n"
                "авторизация: */name*"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
     
        text = "`загрузка...`"
        
        loading_msg = await try_send(update.message.reply_text, text, parse_mode="Markdown")
        
        
        
        message_context = get_message_context(update, reply=False)
        if message_context:
            message_context_reply = get_message_context(update, reply=True)

            await safe_send_message(
                update, 
                text=f"<code>Ты хочешь посмотреть скор</code> <b>  {username}  </b> <code>на карте...</code>", 
                reply_markup=await get_keyboard(
                    message_context, 
                    message_context_reply, 
                    origin_user_id=update.effective_user.id, 
                    username_to_lookup=username
                ),
                parse_mode="HTML"
            )

            await loading_msg.delete()
            return
            
        if not message_context:
            await safe_send_message(update, text="`Нет карты в чате...`", parse_mode="Markdown")
            await loading_msg.delete()
            return       

    except Exception:
        traceback.print_exc() 
