


import time

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_DEV_COMMANDS



async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="ping",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_DEV_COMMANDS} секунд"
        )
        if not can_run:
            return

        start = time.time()
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Pong!",
            message_thread_id=update.message.message_thread_id
        )
        end = time.time()
        latency = (end - start) * 1000 
        await msg.edit_text(f"🏓   {latency:.2f} ms")

    except Exception as e:
        print(f"Ошибка в команде /ping: {e}")