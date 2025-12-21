


from telegram import Update

from ....systems.logging import log_all_update
from ....actions.messages import safe_send_message



async def set_name(update: Update):
    await log_all_update(update)
    await safe_send_message(update, "https://myangelfujiya.ru/darkness/auth")
