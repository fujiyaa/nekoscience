


import temp

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from .buttons import get_settings_kb

from .....config import USER_SETTINGS_FILE



async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = str(update.effective_user.id)
    name = str(update.effective_user.name)

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
  
    kb, text = await get_settings_kb(user_id, settings)

    await update.message.reply_text(
        f'{text} {name}',
        reply_markup=InlineKeyboardMarkup(kb)
    )
