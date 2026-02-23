


import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_NO_API_COMMANDS



async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await log_all_update(update)
            
        can_run = await check_user_cooldown(
            command_name="roll",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_NO_API_COMMANDS,           
            update=update,
            context=context
        )
        if not can_run:
            return
        
        message_thread_id = update.message.message_thread_id

        with open(GIF_roll_PATH, "rb") as animation_file:
            await context.bot.send_sticker(
                chat_id=update.effective_chat.id,
                sticker=animation_file,
                message_thread_id=message_thread_id
            )

    except Exception:
        traceback.print_exc()