


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.rich import rich_reply
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .buttons import get_keyboard

from config import COOLDOWN_LEADERBOARD_COMMANDS



async def start_leaderboard_chat(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(leaderboard_chat(update, context, user_request))
async def leaderboard_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="leaderboard_chat",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_LEADERBOARD_COMMANDS,           
            update=update,
            context=context
        )
    if not can_run:
        return
    
    try:    
        text = "### 🏆 Топ чата <code> - выбeри раздел</code>"
        reply_markup = get_keyboard("select_group", update.effective_message.from_user.id)                
        
        await rich_reply(
            update,
            markdown=text,
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id
        )
        
        return

    except Exception:
        traceback.print_exc()
        