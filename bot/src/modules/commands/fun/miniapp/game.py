

import json
import random
from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....actions.messages import safe_send_message
from .buttons import get_keyboard

from config import MINIAPP_PW_FILE



async def get_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await log_all_update(update)

    text = (
        f"<code>вот кнопка, такая же как в меню бота</code>\n\n"
    )

    reply_markup = get_keyboard()

    await safe_send_message(
        update,
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
