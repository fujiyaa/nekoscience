


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....utils.text_format import build_beatmaps_text
from .buttons import beatmaps_keyboard

from .....config import COOLDOWN_STATS_COMMANDS



async def beatmaps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    can_run = await check_user_cooldown(
            command_name="beatmaps",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return      

    caller_id = update.effective_user.id
    msg = await build_beatmaps_text(caller_id)
    reply_markup = beatmaps_keyboard(caller_id)

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )