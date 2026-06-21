from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....actions.rich import rich_reply

from .menu import main_menu
from .service import neko_settings


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = update.effective_user.id
    name = update.effective_user.name

    keyboard, text = main_menu(neko_settings, user_id, name)

    await rich_reply(
        update=update,
        markdown=text,
        message_thread_id=update.message.message_thread_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )