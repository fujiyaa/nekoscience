


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....actions.messages import safe_send_message



async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)
    await safe_send_message(update, "Открой эту ссылку в том браузере, где залогинен на сайте осу!\n\nhttps://myangelfujiya.ru/darkness/auth")