


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....external.localapi import get_forum_db_thread_count

from config import COOLDOWN_DEV_COMMANDS



async def dev_getthreads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        can_run = await check_user_cooldown(
            command_name="dev_getthreads",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_DEV_COMMANDS,           
            update=update,
            context=context
        )
        if not can_run:
            return

        #neko API         
        try:
            data = await get_forum_db_thread_count()

            thread_count = data["current"]["thread_count"]

        except Exception as e:
            print(f"neko API failed: {e}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=str(thread_count),
            message_thread_id=update.message.message_thread_id
        )

    except Exception as e:
        print(f"Ошибка в команде /getthreads: {e}")