


import time

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_DEV_COMMANDS, START_TIME



async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="uptime",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_DEV_COMMANDS} секунд"
        )
        if not can_run:
            return

        current_time = time.time()
        uptime_seconds = int(current_time - START_TIME)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Uptime: {days}d {hours}h {minutes}m {seconds}s",
            message_thread_id=update.message.message_thread_id
        )

    except Exception as e:
        print(f"Ошибка в команде /uptime: {e}")