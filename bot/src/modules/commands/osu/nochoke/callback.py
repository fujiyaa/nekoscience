


from telegram import Update
from telegram.ext import ContextTypes

from .buttons import get_keyboard
from .page_text import get_text



async def callback_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 

    best_scores = context.user_data.get("best_scores", [])
    user_data = context.user_data.get("user_data")
    total_pages = context.user_data.get("total_pages", 1)

    _, page_str, owner_id_str = query.data.split("_")
    owner_id = int(owner_id_str)
    if query.from_user.id != owner_id:
        await query.answer("Это не ваша команда!", show_alert=True)
        return

    page = int(page_str)
    text = get_text(user_data, best_scores, page)  # твоя функция генерации текста
    keyboard = get_keyboard(page, total_pages, owner_id)

    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )
