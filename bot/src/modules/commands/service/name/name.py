


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....actions.messages import safe_send_message
from .buttons import get_keyboard



async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await log_all_update(update)

    try:
        username = update.message.from_user.username
    except:
        username = update.callback_query.from_user.username

    text = (
        f"<b><i>@{username}</i></b>   <code>Похоже, у тебя еще не авторизован аккаунт, "
        f"однако для использования некоторых моих функций я должна узнать твой ник:</code>\n\n"
    )

    reply_markup = get_keyboard()

    await safe_send_message(
        update,
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
