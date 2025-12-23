


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_GIFS_COMMANDS, GIF_DOUBT_PATH



async def doubt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    try:
        await update.message.delete()

        can_run = await check_user_cooldown(
            command_name="doubt",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_GIFS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_GIFS_COMMANDS} секунд"
        )
        if not can_run:
            return
        
        message_thread_id = update.message.message_thread_id

        with open(GIF_DOUBT_PATH, "rb") as animation_file:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=animation_file,
                message_thread_id=message_thread_id
            )

    except Exception as e:
        print(f"Ошибка при doubt: {e}")