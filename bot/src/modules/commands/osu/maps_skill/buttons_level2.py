


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"farm_page:{user_id}:{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"farm_page:{user_id}:{page+1}"))
    return InlineKeyboardMarkup([buttons])
