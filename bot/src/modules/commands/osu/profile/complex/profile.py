


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from .....systems.cooldowns import check_user_cooldown
from .....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from .response import send_message
from .context import context_lookup

from config import COOLDOWN_STATS_COMMANDS


    
async def profile(
    update: Update, context: 
    ContextTypes.DEFAULT_TYPE, 
    action: str = 'profile'
):      
    can_run = await check_user_cooldown(
            command_name=action,
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ {COOLDOWN_STATS_COMMANDS}s"
        )
    if not can_run:
        return

    temp_message, username = await context_lookup(update, context, action)

    if temp_message is None: 
        return
    else:
        temp_id = temp_message.message_id

    try:   
        await send_message(
            update,
            context,
            action,
            username,
            temp_id
        )

    except Exception:
        traceback.print_exc()
        # ошибку в ответ бота?
