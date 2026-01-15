


from telegram import Update

from ....actions.messages import safe_send_message



async def send(update: Update, stats_batch: dict = None, caption: str = ''):
    if not stats_batch:
        await safe_send_message(
                update,
                "Нет данных",
                parse_mode="HTML",
                # reply_markup=pagination
            )     
        return

    await safe_send_message(
                update,
                caption,
                parse_mode="HTML",
                # reply_markup=pagination
            )         